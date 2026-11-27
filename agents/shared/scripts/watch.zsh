#!/bin/zsh
# watch.zsh — the watcher behind agents/manager.md ("The watcher").
#
# Relies on jq and on Claude Code's agent-view commands: `claude agents --json`,
# `claude respawn <id>` and `claude stop <id>` (confirm with `claude --help`).
# Hosts without them run the manager in paste mode, which does not use this.
#
# MODES
#   snap  <work root> <prefix> [-i id]... [-s id]... [-q id]...
#         Remember these arguments, print how the current state differs from
#         the saved snapshot (or the full state, the first time), and save the
#         current state as the new snapshot.
#   start <work root> [-m minutes]
#         Replace any running watcher, then poll once a minute, using the
#         arguments the last snap remembered. Ends by printing the UTC time and
#         a diff as soon as the state differs from the snapshot, or after
#         -m minutes (default 115) with no change. An -i session that has
#         vanished is respawned along the way.
#   stop  <work root> <id> <folder id> [-m minutes]
#         Stop session <id>, but only once it is idle, its transcript has not
#         changed for 10 minutes, and no watcher started before the last snap
#         is still running. Refuses while <id> is in the remembered -i list,
#         or once work/<folder id>/STATUS.md no longer reads DONE or
#         HANDOFF-READY. Gives up after -m minutes (default 115). Prints
#         "stopped <id>" on success or when the session is already gone.
#
# FLAGS (repeat the flag for each id)
#   -i id   live worker: context is watched, and it is respawned if it vanishes
#   -s id   session to ignore (one already stopped)
#   -q id   session whose "waiting" status counts as live (the owner is on it)
#
# STATE compared between polls
#   "ctx <id> <N>0%+" for each -i session at 70% context or more; the STATUS:
#   and Doing now: lines of every work/*/STATUS.md; every HANDOFF.md and every
#   unread channel/MSG-*.md; and each <prefix> session's status, with busy and
#   idle both shown as "live".
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
  [[ ${1-} == (snap|start|stop) ]] || usage
  local mode=$1
  [[ -n ${2-} && -d $2 ]] || usage
  local root=${2:A}
  shift 2

  local -a pos W_live W_skip W_quiet
  local minutes=115
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
  [[ $minutes == <1-> ]] || usage

  local pid_file=$root/.watcher.pid
  local snap_file=$root/.watcher.snap
  local args_file=$root/.watcher.args

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

state() {
  local js=$(agents) id sid pct f line
  for id in $W_live; do
    sid=$(lookup "$js" $id sessionId)
    [[ $sid == none ]] && continue
    pct=$(zsh $here/ctxpct.sh $sid 2>/dev/null)
    [[ $pct == <-> ]] && (( pct >= 70 )) && print -r -- "ctx $id $(( pct / 10 ))0%+"
  done
  for f in $root/work/*/STATUS.md(N); do
    while IFS= read -r line; do
      [[ $line == (STATUS|Doing now):* ]] && print -r -- "${f#$root/}: $line"
    done < $f
  done | sort
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

# respawn_missing: respawn the first -i session absent from the agent list.
# Returns 0 if it respawned one, 1 if all are present.
typeset -gA respawn_count
respawn_missing() {
  local js=$(agents) id
  [[ -n $js ]] || return 1
  for id in $W_live; do
    [[ $(lookup "$js" $id id) == none ]] || continue
    (( respawn_count[$id] = ${respawn_count[$id]:-0} + 1 ))
    if (( respawn_count[$id] > 3 )); then
      print -r -- "respawn of $id keeps failing"
      release_pid
      exit 0
    fi
    claude respawn $id >/dev/null 2>&1
    print -r -- "$(date -u +%H:%MZ) respawned $id"
    return 0
  done
  respawn_count=()
  return 1
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
    if ! respawn_missing; then
      now=$(state)
      if [[ $now != $base ]]; then
        date -u
        diff <(print -r -- $base) <(print -r -- $now)
        release_pid
        exit 0
      fi
    fi
    sleep 60 &
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
  local status_file=$root/work/$folder/STATUS.md

  refuse_if_live() {
    load_args
    (( ${W_live[(Ie)$id]} )) || return 0
    print -r -- "not stopped: $id is still a live (-i) id in the saved arguments; snap again without it, then start"
    exit 1
  }
  refuse_unless_finished() {
    local line
    line=$(grep -m 1 '^STATUS:' $status_file 2>/dev/null)
    [[ $line == 'STATUS: DONE'* || $line == 'STATUS: HANDOFF-READY'* ]] && return 0
    print -r -- "not stopped: work/$folder/STATUS.md says ${line:-nothing}"
    exit 1
  }
  quiet_for_ten_minutes() {
    local -a mt
    zstat -A mt +mtime -- $1 2>/dev/null || return 1
    (( EPOCHSECONDS - mt[1] >= 600 ))
  }
  older_watcher_running() { current_watcher >/dev/null && [[ $args_file -nt $pid_file ]] }

  refuse_if_live
  local sid=$(lookup "$(agents)" $id sessionId)
  [[ $sid == none ]] && { print -r -- "stopped $id (already gone)"; exit 0 }
  refuse_unless_finished

  local projects=${CLAUDE_PROJECTS_DIR:-$HOME/.claude/projects}
  local -a found=( $projects/$sid.jsonl(N) $projects/*/$sid.jsonl(N) )
  (( $#found )) || { print -r -- "not stopped: no transcript for $id"; exit 1 }
  local transcript=$found[1] st n

  for (( n = 0; ; n++ )); do
    st=$(lookup "$(agents)" $id status)
    [[ $st == none ]] && { print -r -- "stopped $id (already gone)"; exit 0 }
    refuse_unless_finished
    if [[ $st == idle ]] && quiet_for_ten_minutes $transcript && ! older_watcher_running; then
      break
    fi
    if (( n >= minutes )); then
      print -r -- "not stopped: no ten-minute idle, quiet window for $id in $minutes minutes"
      exit 1
    fi
    sleep 60
    refuse_if_live
  done

  refuse_unless_finished
  claude stop $id >/dev/null || { print -r -- "not stopped: claude stop $id failed"; exit 1 }
  print -r -- "stopped $id"
}

main "$@"; exit $?
