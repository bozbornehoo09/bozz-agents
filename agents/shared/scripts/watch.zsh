#!/bin/zsh
# watch.zsh — the watcher behind agents/manager.md ("Waking yourself").
#
# Relies on jq and on Claude Code's agent-view commands: `claude agents --json`
# (and `--all`, where known), `claude respawn <id>` and `claude stop <id>`
# (confirm with `claude --help`). Hosts without them run the manager in paste
# mode, which does not use this.
#
# MODES
#   snap  <work root> <prefix> [-i id]... [-s id]... [-q id]...
#         Remember these arguments, print how the current state differs from
#         the saved snapshot (or the full state, the first time), and save the
#         current state as the new snapshot.
#   start <work root> [-m minutes]
#         Replace any running watcher, then check at once and once a minute,
#         using the arguments the last snap remembered. Ends by printing the
#         UTC time and a diff as soon as the state differs from the snapshot,
#         or after -m minutes (default 55, inside a manager's one-hour prompt
#         cache) with no change. Along the way it respawns any -i session that
#         has gone (the agent view retires a background session left idle for
#         a long time), skipping any whose folder's STATUS is final (DONE,
#         HANDOFF-READY). When the list shows a respawned session again, it
#         prints "<time> respawned <id>" and ends; after three tries that fail
#         it prints "respawn of <id> keeps failing" and ends.
#   stop  <work root> <id> <folder id> [-m minutes]
#         Stop session <id> once it is finished, between turns and quiet.
#         Finished means work/<folder id>/ shows one of:
#           - STATUS.md reads DONE or HANDOFF-READY;
#           - HANDOFF.md exists and BRIEF.md now names a different session
#             (so STATUS.md is the successor's);
#           - STATUS.md reads WAITING-ON-OWNER, is 30 minutes old, the folder
#             holds a HANDOFF.md this session wrote (a commit whose subject
#             starts "[<session name>]" touches it, so a predecessor's does
#             not count) and its "Open reviews:" line is absent or "none".
#         Between turns means idle, or busy only because a background task of
#         its own is still running (its last turn has ended). Quiet means its
#         transcript has not changed for 10 minutes and no watcher started
#         before the last snap is still running. Refuses while <id> is in the
#         remembered -i list. Gives up after -m minutes (default 115). Prints
#         "stopped <id>" on success or when the session is already gone.
#
# FLAGS (repeat the flag for each id)
#   -i id   live worker: its size is watched, and it is respawned if it goes
#   -s id   session to ignore (one already stopped)
#   -q id   session whose "waiting" status counts as live (the owner is on it)
#
# STATE compared between checks holds just the things the manager must act on:
#   - "ctx <id> over <cap>k" once an -i session's newest call is at least 10k
#     above the worker cap (BOZZ_CTXCAP_WORKER_K, default 350, the same cap the
#     hook uses), so a worker the hook's note did not move still reaches the
#     manager;
#   - the STATUS: line of every work/*/STATUS.md (not Doing now:, which changes
#     every turn and is never a reason to wake);
#   - for each WAITING-ON-MANAGER: <session> in <file> ..., that session's
#     Doing now: line and "blocker <file> clean|dirty|missing" (git status, so
#     staged, unstaged and untracked changes all read dirty);
#   - every HANDOFF.md and every unread channel/MSG-*.md;
#   - each <prefix> session's status, with busy and idle both shown as "live".
# Tests set BOZZ_WATCH_POLL (seconds between checks, default 60).
#
# Everything runs inside main(), called on the file's last line, so the whole
# script is parsed before anything executes: editing this file while a
# watcher is running cannot change what that watcher does.

# Captured at top level: inside a function, $0 is the function's name.
typeset -g WATCH_SELF=${0:A}

main() {
  emulate -L zsh
  zmodload -F zsh/stat b:zstat
  zmodload zsh/datetime
  local here=${WATCH_SELF:h}
  source $here/sessions.zsh
  [[ ${1-} == (snap|start|stop) ]] || usage
  local mode=$1
  [[ -n ${2-} && -d $2 ]] || usage
  local root=${2:A}
  shift 2

  local -a pos W_live W_skip W_quiet
  local minutes=
  while (( $# )); do
    case $1 in
      (-i|-s|-q|-m)
        (( $# > 1 )) || usage
        case $1 in
          (-i) W_live+=($2) ;;
          (-s) W_skip+=($2) ;;
          (-q) W_quiet+=($2) ;;
          (-m) minutes=$2 ;;
        esac
        shift 2 ;;
      (*) pos+=($1); shift ;;
    esac
  done
  [[ -n $minutes ]] || { [[ $mode == start ]] && minutes=55 || minutes=115 }
  [[ $minutes == <1-> ]] || usage

  local pid_file=$root/.watcher.pid
  local snap_file=$root/.watcher.snap
  local args_file=$root/.watcher.args
  local cap=${BOZZ_CTXCAP_WORKER_K:-350}
  local poll=${BOZZ_WATCH_POLL:-60}

  case $mode in
    (snap)  do_snap ;;
    (start) do_start ;;
    (stop)  do_stop ;;
  esac
}

usage() {
  print -u2 -r -- "usage: watch.zsh snap  <work root> <prefix> [-i id]... [-s id]... [-q id]...
       watch.zsh start <work root> [-m minutes]
       watch.zsh stop  <work root> <id> <folder id> [-m minutes]"
  exit 2
}

agents() { claude agents --json 2>/dev/null }

# json_array <words...>: the words as a JSON array of strings
json_array() { printf '%s\n' "$@" | jq -R . | jq -sc 'map(select(length > 0))' }

# lookup <agents json> <id> <field>: the field of the agent with that id, or "none"
lookup() { jq -r --arg id $2 --arg f $3 '[.[] | select(.id == $id)][0][$f] // "none"' <<<$1 2>/dev/null || print none }

# brief_session <BRIEF.md>: the session named on its "Session:" line
brief_session() {
  local line
  line=$(grep -m 1 -E '^[*]*Session:' $1 2>/dev/null) || return 1
  line=${line#*Session:}; line=${line#\*\*}; line=${line//\`/}
  print -r -- ${${=line}[1]}
}

# folder_of <session name>: prints the folder of the brief naming that session
folder_of() {
  local b
  [[ -n ${1-} ]] || return 1
  for b in $root/work/*/BRIEF.md(N); do
    [[ $(brief_session $b) == $1 ]] && { print -r -- ${b:h}; return 0 }
  done
  return 1
}

current_watcher() {
  local p
  [[ -r $pid_file ]] && p=$(<$pid_file)
  [[ $p == <-> ]] || return 1
  [[ $(ps -o command= -p $p 2>/dev/null) == *${WATCH_SELF:t}* ]] || return 1
  print -r -- $p
}

release_pid() { [[ -r $pid_file && $(<$pid_file) == $$ ]] && rm -f -- $pid_file }

load_args() {
  # plain assignments, so they land in the caller's W_* variables
  [[ -r $args_file ]] && source $args_file
}

# blockers: one pair of lines per WAITING-ON-MANAGER waiter: what the blocking
# session says it is doing, and whether the awaited file is clean
blockers() {
  local line who file g p top st
  grep -h '^STATUS: WAITING-ON-MANAGER: ' /dev/null $root/work/*/STATUS.md(N) | sort -u |
  while IFS= read -r line; do
    who=${${line#STATUS: WAITING-ON-MANAGER: }%% *}
    g=$(folder_of $who) && sed -n "s|^Doing now:|${g#$root/}/STATUS.md:Doing now:|p" $g/STATUS.md 2>/dev/null
    [[ $line == *' in '* ]] || continue
    file=${${line#* in }%% *}
    [[ -n $file ]] || continue
    p=$file
    [[ $p == /* ]] || p=$root/$file
    if [[ ! -e $p ]]; then
      top=$(git -C $root rev-parse --show-toplevel 2>/dev/null)
      [[ -n $top ]] && p=$top/$file
    fi
    if [[ ! -e $p ]]; then
      print -r -- "blocker $file missing"
      continue
    fi
    # --no-optional-locks, so this check never holds the index lock a commit needs;
    # untracked files count, so a new file reads dirty
    st=$(git --no-optional-locks -C ${p:h} status --untracked-files=all --porcelain -- ${p:t} 2>/dev/null) || st=unreadable
    if [[ -z $st ]]; then print -r -- "blocker $file clean"; else print -r -- "blocker $file dirty"; fi
  done
}

state() {
  local js=$(agents) id sid file size f
  for id in $W_live; do
    sid=$(lookup "$js" $id sessionId)
    [[ $sid == none ]] && continue
    file=$(transcript_of $sid) || continue
    size=$(latest_size $file)
    [[ $size == <-> ]] && (( size / 1000 >= cap + 10 )) && print -r -- "ctx $id over ${cap}k"
  done
  for f in $root/work/*/STATUS.md(N); do
    grep -m 1 '^STATUS:' $f 2>/dev/null | sed "s|^|${f#$root/}: |"
  done | sort
  blockers | sort -u
  for f in $root/work/*/HANDOFF.md(N) $root/work/*/channel/MSG-*.md(N); do
    print -r -- ${f#$root/}
  done
  [[ -n $js ]] || { print -r -- "agents: unread"; return }
  jq -c --arg p $W_prefix --argjson skip "$(json_array $W_skip)" --argjson quiet "$(json_array $W_quiet)" '
    [ .[]
      | select((.name // "") | startswith($p))
      | select(.id as $i | $skip | any(. == $i) | not)
      | { name,
          s: (if .status == "busy" or .status == "idle" then "live"
              elif .status == "waiting" and (.id as $i | $quiet | any(. == $i)) then "live"
              else .status end) } ]
    | sort_by(.name)' <<<$js
}

# final_status <folder>: its STATUS is DONE or HANDOFF-READY
final_status() { grep -qE '^STATUS: (DONE|HANDOFF-READY)' $1/STATUS.md 2>/dev/null }

# heal: respawn each -i session that has gone, unless its folder is finished.
# Ends the watcher (exit 0) once a respawned session is listed again, so the
# manager wakes and tells it to re-arm what it lost. Returns 0 while a
# respawn awaits its retry, 1 when every -i session is present.
typeset -gA respawn_count
heal() {
  local js=$(agents_all) id st name g pending=1
  [[ -n $js ]] || return 1
  for id in $W_live; do
    st=$(jq -r --arg id $id "[.[] | select(.id == \$id)][0] | if . == null then \"none\" elif $starting_q then \"starting\" else (.status // \"none\") end" <<<$js 2>/dev/null)
    if [[ -n $st && $st != none ]]; then
      if (( ${respawn_count[$id]:-0} )); then
        print -r -- "$(date -u +%H:%MZ) respawned $id"
        release_pid
        exit 0
      fi
      continue
    fi
    name=$(lookup "$js" $id name)
    g=$(folder_of $name) && final_status $g && continue
    (( respawn_count[$id] = ${respawn_count[$id]:-0} + 1 ))
    if (( respawn_count[$id] > 3 )); then
      print -r -- "respawn of $id keeps failing"
      release_pid
      exit 0
    fi
    claude respawn $id >/dev/null 2>&1
    pending=0
  done
  (( pending )) && respawn_count=()
  return $pending
}

do_snap() {
  local W_prefix=${pos[1]-}
  [[ -n $W_prefix ]] || usage
  {
    print -r -- "W_prefix=${(q)W_prefix}"
    print -r -- "W_live=( ${(@q)W_live} )"
    print -r -- "W_skip=( ${(@q)W_skip} )"
    print -r -- "W_quiet=( ${(@q)W_quiet} )"
  } > $args_file.new && mv -f $args_file.new $args_file
  local now=$(state)
  if [[ -f $snap_file ]]; then
    diff $snap_file <(print -r -- $now) && print -r -- "no change since the last snapshot"
  else
    print -r -- "first snapshot:"
    print -r -- $now
  fi
  print -r -- $now > $snap_file.new && mv -f $snap_file.new $snap_file
}

do_start() {
  [[ -f $snap_file && -f $args_file ]] || { print -u2 -r -- "watch.zsh: run snap first; no snapshot in $root"; exit 2 }
  local W_prefix
  load_args
  local old
  old=$(current_watcher) && kill $old 2>/dev/null
  print -r -- $$ > $pid_file
  trap 'print -r -- "watcher $$ replaced by a newer start"; release_pid; exit 0' TERM
  local base=$(<$snap_file) now n
  for (( n = 1; n <= minutes; n++ )); do
    if ! heal; then
      now=$(state)
      if [[ $now != $base ]]; then
        date -u
        diff <(print -r -- $base) <(print -r -- $now)
        release_pid
        exit 0
      fi
    fi
    sleep $poll &
    wait $!
  done
  print -r -- "no change in $minutes minutes"
  release_pid
  return 0
}

do_stop() {
  local id=${pos[1]-} folder=${pos[2]-}
  [[ -n $id && -n $folder ]] || usage
  local W_prefix
  local dir=$root/work/$folder

  refuse_if_live() {
    load_args
    (( ${W_live[(Ie)$id]} )) || return 0
    print -r -- "not stopped: $id is still a live (-i) id in the saved arguments; snap again without it, then start"
    exit 1
  }
  refuse_unless_finished() {
    local line named name reviews
    line=$(grep -m 1 '^STATUS:' $dir/STATUS.md 2>/dev/null)
    [[ $line == 'STATUS: DONE'* || $line == 'STATUS: HANDOFF-READY'* ]] && return 0
    if [[ -f $dir/HANDOFF.md ]]; then
      named=$(brief_session $dir/BRIEF.md)
      name=$(lookup "$(agents_all)" $id name)
      [[ -n $named && $name != none && $named != $name ]] && return 0
      if [[ $line == 'STATUS: WAITING-ON-OWNER'* ]] && older_than_30_minutes $dir/STATUS.md; then
        [[ $name != none ]] || name=$named
        if ! committed_by $dir/HANDOFF.md $name; then
          print -r -- "not stopped: work/$folder/HANDOFF.md has no commit tagged [${name:-?}], so this session did not write it"
          exit 1
        fi
        reviews=$(grep -m 1 '^Open reviews:' $dir/HANDOFF.md 2>/dev/null)
        reviews=${${reviews#Open reviews:}// /}
        [[ -z $reviews || $reviews == none ]] && return 0
        print -r -- "not stopped: work/$folder/HANDOFF.md lists open reviews"
        exit 1
      fi
    fi
    print -r -- "not stopped: work/$folder/STATUS.md says ${line:-nothing}"
    exit 1
  }
  # committed_by <file> <session name>: a commit whose subject starts
  # "[<session name>]" touches the file (compared as text, not as a pattern)
  committed_by() {
    [[ -n $2 ]] || return 1
    local subject
    for subject in ${(f)"$(git -C ${1:h} log --format=%s -- ${1:t} 2>/dev/null)"}; do
      [[ $subject == "[$2]"* ]] && return 0
    done
    return 1
  }
  older_than_30_minutes() {
    local -a mt
    zstat -A mt +mtime -- $1 2>/dev/null || return 1
    (( EPOCHSECONDS - mt[1] >= 1800 ))
  }
  quiet_for_ten_minutes() {
    local -a mt
    zstat -A mt +mtime -- $1 2>/dev/null || return 1
    (( EPOCHSECONDS - mt[1] >= 600 ))
  }
  between_turns() { [[ $1 == idle ]] || { [[ $1 == busy ]] && turn_ended $transcript } }
  older_watcher_running() { current_watcher >/dev/null && [[ $args_file -nt $pid_file ]] }

  refuse_if_live
  local js=$(agents)
  local sid=$(lookup "$js" $id sessionId) st=$(lookup "$js" $id status)
  [[ $sid == none || $st == none ]] && { print -r -- "stopped $id (already gone)"; exit 0 }
  refuse_unless_finished

  local transcript
  transcript=$(transcript_of $sid) || { print -r -- "not stopped: no transcript for $id"; exit 1 }
  local n
  for (( n = 0; ; n++ )); do
    st=$(lookup "$(agents)" $id status)
    [[ $st == none ]] && { print -r -- "stopped $id (already gone)"; exit 0 }
    refuse_unless_finished
    if between_turns $st && quiet_for_ten_minutes $transcript && ! older_watcher_running; then
      break
    fi
    if (( n >= minutes )); then
      print -r -- "not stopped: no ten-minute idle, quiet window for $id in $minutes minutes"
      exit 1
    fi
    sleep $poll
    refuse_if_live
  done

  refuse_unless_finished
  claude stop $id >/dev/null || { print -r -- "not stopped: claude stop $id failed"; exit 1 }
  print -r -- "stopped $id"
}

main "$@"; exit $?
