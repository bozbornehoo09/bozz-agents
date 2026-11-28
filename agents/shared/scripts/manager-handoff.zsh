#!/bin/zsh
# manager-handoff.zsh — manager succession, behind agents/manager.md
# ("Succession"). A manager hands off to a fresh session at its size cap
# instead of growing; this script makes the change-over safe.
#
# MODES
#   claim <work root> <prefix>
#       A new manager's first act. Writes <work root>/CURRENT-MANAGER
#       ("<name> <id> <session id> <UTC>"; <id> is - for an interactive
#       session, which the agent view lists without one) for the calling
#       session and exits 0,
#       or exits 1 without writing when another <prefix> session is the live
#       manager, printing that manager's name. During a handoff the session
#       handing off does not count as another manager. A re-claim by the
#       session already named changes nothing.
#   current <work root>
#       Exits 0 when the calling session is the manager: CURRENT-MANAGER names
#       it and no handoff is running. Otherwise prints the name the owner
#       should open and exits 1. The manager's wake guard.
#   handoff <work root> <prefix> <next prompt>
#       Run by the live manager in the background once it has written <next
#       prompt> and its state file. Takes the handoff lock (or exits 3 if
#       another run holds it), kills the caller's watcher, launches
#       <prefix><n+1> on "Run <next prompt>" with a one-hour prompt cache and
#       idle compaction off, and waits for it to claim CURRENT-MANAGER. Then it
#       releases the lock and stops the caller once the caller is between
#       turns and its transcript has been quiet for 10 minutes.
#       Exit 0: the successor is the manager. Exit 1: it is not; the successor
#       is stopped, CURRENT-MANAGER is restored, `ctxcap.sh hold` notes the
#       caller's present size so the hook keeps quiet a while, and the caller
#       carries on as manager.
#   first <work root> <prefix> <next prompt>
#       The same launch with no caller: starts the first manager when none is
#       live.
#   Exit 2: bad arguments. Exit 3: another handoff holds the lock, or this
#   run's owner line was replaced (then nothing more is changed).
#
# The calling session is $CLAUDE_CODE_SESSION_ID. With it unset (another
# host) there is no succession: claim and current say so and exit 0, except
# that current exits 1 while a handoff runs. Sessions are matched by their
# full session id (the agent view's .sessionId): an interactive session has
# no agent-view .id, which is used only to `claude stop` a background one.
#
# Locking uses zsystem flock, an advisory lock the kernel keeps on
# .manager-handoff.lock for as long as this process lives and drops however it
# ends; so a lock is never stale, and the file itself is never removed. The
# owner line in .manager-handoff.owner ("<caller session id|first> <pid>
# <UTC> <token>") is written only while the lock is held.
#
# SETTINGS (environment; mostly for tests)
#   BOZZ_MANAGER_AGENT       agent to launch (default bozz-agents:manager)
#   BOZZ_MANAGER_SETTINGS    launch --settings JSON
#                            (default {"promptCacheTtl":"1h","idleCompaction":false})
#   BOZZ_HANDOFF_WAIT        seconds the successor has to claim (default 600)
#   BOZZ_HANDOFF_START_WAIT  seconds before an unlisted launch counts as failed (default 60)
#   BOZZ_HANDOFF_POLL        seconds between checks (default 15)
#   BOZZ_HANDOFF_QUIET       minutes the caller must be quiet (default 10)
#   BOZZ_HANDOFF_STOP_WAIT   minutes to wait for that (default 115)
#
# Everything runs inside main(), called on the file's last line, so the whole
# script is parsed before it runs.

typeset -g HANDOFF_HERE=${0:A:h}

main() {
  emulate -L zsh
  zmodload zsh/system
  zmodload -F zsh/stat b:zstat
  zmodload zsh/datetime
  source $HANDOFF_HERE/sessions.zsh
  local mode=${1-}
  [[ $mode == (claim|current|handoff|first) ]] || usage
  [[ -n ${2-} && -d $2 ]] || usage
  local root=${2:A} prefix=${3-}
  local cur=$root/CURRENT-MANAGER
  local lock=$root/.manager-handoff.lock owner_file=$root/.manager-handoff.owner
  local me=${CLAUDE_CODE_SESSION_ID-}
  local live_q='(.status | IN("busy", "idle", "waiting"))'

  case $mode in
    (claim)   [[ -n $prefix ]] || usage; do_claim ;;
    (current) do_current ;;
    (handoff) [[ -n $prefix && -f ${4-} && -n $me ]] || usage; do_launch 0 ${4:A} ;;
    (first)   [[ -n $prefix && -f ${4-} ]] || usage; do_launch 1 ${4:A} ;;
  esac
}

usage() {
  print -u2 -r -- "usage: manager-handoff.zsh claim   <work root> <prefix>
       manager-handoff.zsh current <work root>
       manager-handoff.zsh handoff <work root> <prefix> <next prompt>
       manager-handoff.zsh first   <work root> <prefix> <next prompt>"
  exit 2
}

utc() { date -u +%Y-%m-%dT%H:%MZ }

# handoff_running: some run holds the lock. A shared, non-blocking try, so
# two checks never refuse each other; dropped at once.
handoff_running() {
  [[ -e $lock ]] || return 1
  local probe
  if zsystem flock -t 0 -r -f probe $lock 2>/dev/null; then
    zsystem flock -u $probe
    return 1
  fi
  return 0
}

# field <agents json> <session id> <field>: a field of the listed session
field() { jq -r --arg s $2 --arg f $3 '[.[] | select(.sessionId == $s)][0][$f] // empty' <<<$1 2>/dev/null }

current_field() { [[ -r $cur ]] && awk -v n=$1 '{print $n; exit}' $cur }

open_line() { print -r -- "the manager is $1: open it by that name in the agent view" }

do_current() {
  if [[ -z $me ]]; then
    handoff_running && { print -r -- "a manager handoff is running"; exit 1 }
    print -r -- "no CLAUDE_CODE_SESSION_ID: succession is not in use here"
    exit 0
  fi
  [[ $(current_field 3) == $me ]] && ! handoff_running && exit 0
  local name=$(current_field 1)
  if [[ -n $name ]]; then open_line $name; else print -r -- "no manager has claimed $cur"; fi
  exit 1
}

do_claim() {
  if [[ -z $me ]]; then
    print -r -- "no CLAUDE_CODE_SESSION_ID: succession is not in use here"
    exit 0
  fi
  [[ $(current_field 3) == $me ]] && { print -r -- "already the manager"; exit 0 }
  local js=$(agents_all)
  # an interactive session is listed without an id; the record then says -
  local myid=$(field "$js" $me id) myname=$(field "$js" $me name)
  [[ -n $myid ]] || myid=-
  local caller=
  handoff_running && caller=$(awk '{print $1; exit}' $owner_file 2>/dev/null)
  local -a others
  others=( ${(f)"$(jq -r --arg p $prefix --arg me $me --arg c "$caller" "
      .[] | select(.sessionId != \$me) | select(.sessionId != \$c)
          | select(.name // \"\" | startswith(\$p)) | select($live_q) | .name" <<<$js 2>/dev/null)"} )
  if [[ -z $caller ]]; then
    local csid=$(current_field 3)
    if [[ -n $csid && $csid != $me ]] &&
       jq -e --arg s $csid "any(.[]; .sessionId == \$s and $live_q)" <<<$js >/dev/null 2>&1; then
      others+=( $(current_field 1) )
    fi
  fi
  if (( $#others )); then
    print -r -- "not claimed: another manager is live"
    local n
    for n in ${(u)others}; do open_line $n; done
    exit 1
  fi
  print -r -- "${myname:-unnamed} $myid $me $(utc)" > $cur.new.$$ && mv -f $cur.new.$$ $cur
  print -r -- "claimed: $cur names ${myname:-unnamed} $myid"
  exit 0
}

do_launch() {
  local first=$1 prompt=$2
  local wait_s=${BOZZ_HANDOFF_WAIT:-600} start_s=${BOZZ_HANDOFF_START_WAIT:-60}
  local poll=${BOZZ_HANDOFF_POLL:-15} quiet=${BOZZ_HANDOFF_QUIET:-10} stop_wait=${BOZZ_HANDOFF_STOP_WAIT:-115}
  local agent=${BOZZ_MANAGER_AGENT:-bozz-agents:manager}
  local settings=${BOZZ_MANAGER_SETTINGS:-'{"promptCacheTtl":"1h","idleCompaction":false}'}
  # old names the caller in messages: its id, else (interactive) its name
  local js=$(agents_all) old=first
  if (( ! first )); then
    old=$(field "$js" $me id)
    [[ -n $old ]] || old=$(field "$js" $me name)
    [[ -n $old ]] || old=${me[1,8]}
  fi
  local token="$$.$EPOCHREALTIME.$RANDOM"
  local caller=first
  (( first )) || caller=$me
  local owner_line="$caller $$ $(utc) $token"

  # one try, never a wait; the descriptor stays open until this process ends
  : >> $lock
  local lockfd
  zsystem flock -t 0 -f lockfd $lock 2>/dev/null ||
    { print -r -- "handoff in progress: the lock is held by $(cat $owner_file 2>/dev/null || print unknown)"; exit 3 }
  print -r -- $owner_line > $owner_file

  ours() { [[ "$(cat -- $owner_file 2>/dev/null)" == "$owner_line" ]] }
  lost() {
    print -r -- "handoff in progress: $owner_file is no longer this run's; CURRENT-MANAGER is left as it is"
    exit 3
  }
  release() { ours || lost; rm -f -- $owner_file; zsystem flock -u $lockfd }

  # from here the caller acts on nothing: its watcher goes, and its wake
  # guard (current) fails while the lock is held
  if (( ! first )); then
    local w
    [[ -r $root/.watcher.pid ]] && w=$(<$root/.watcher.pid)
    [[ $w == <-> && $(ps -o command= -p $w 2>/dev/null) == *watch.zsh* ]] && kill $w 2>/dev/null
  fi

  local prev
  [[ -r $cur ]] && prev=$(<$cur)
  local -a nums
  nums=( ${(f)"$(jq -r --arg p $prefix 'map(.name // "" | select(startswith($p)) | ltrimstr($p)) | .[]' <<<$js 2>/dev/null)"} )
  [[ -n $prev ]] && nums+=( ${${prev%% *}#$prefix} )
  local top=0 x
  for x in $nums; do [[ $x == <-> ]] && (( x > top )) && top=$x; done
  local new=$prefix$(( top + 1 ))

  # launch from the caller's own folder, which the owner has trusted: a
  # background launch from an untrusted folder starts nothing
  local wd=$PWD c
  if (( ! first )); then
    c=$(field "$js" $me cwd)
    [[ -n $c && -d $c ]] && wd=$c
  fi
  local out
  out=$(cd $wd && claude --bg --settings $settings --name $new --agent $agent "Run $prompt" 2>&1)

  # newsid matches the successor everywhere; newid (a background launch
  # always has one) is only for `claude stop`
  local newid= newsid=
  find_new() {
    [[ -n $newsid ]] && return 0
    local row
    row=$(agents_all | jq -r --arg n $new 'map(select(.name == $n)) | max_by(.startedAt // 0)
        | select(. != null and .sessionId != null) | "\(.sessionId) \(.id // "")"' 2>/dev/null)
    newsid=${row%% *} newid=${row#* }
    [[ -n $newsid ]]
  }
  gone() {
    agents_all | jq -e --arg s $newsid "[.[] | select(.sessionId == \$s)]
        | (length == 0) or (.[0] | .status == null and ($starting_q | not))" >/dev/null 2>&1
  }
  fail() {
    print -r -- "handoff failed: $1"
    find_new && [[ -n $newid ]] && claude stop $newid >/dev/null 2>&1
    ours || lost
    if [[ -n $prev ]]; then print -r -- $prev > $cur.new.$$ && mv -f $cur.new.$$ $cur; else rm -f -- $cur; fi
    (( first )) || zsh $HANDOFF_HERE/ctxcap.sh hold $me
    release
    if (( first )); then print -r -- "no manager is live; fix the cause, then start one again"
    else print -r -- "you are still the manager; arm your watcher again and make no second attempt"; fi
    exit 1
  }

  local t
  for (( t = 0; ; t += poll )); do
    if find_new; then
      [[ $(current_field 3) == $newsid ]] && break
      gone && fail "$new ($newid) ended before it claimed CURRENT-MANAGER"
    elif (( t >= start_s || t + poll > wait_s )); then
      fail "$new did not start (launched from $wd): ${out:-no output}"
    fi
    (( t + poll > wait_s )) && fail "$new did not claim CURRENT-MANAGER within $wait_s s"
    sleep $poll
  done
  release
  print -r -- "handed off: $new ($newid) now manages; the owner finds it by that name in the agent view"
  (( first )) && exit 0

  # stop the caller last, since stopping it can end this background job
  local transcript
  transcript=$(transcript_of $me)
  # only a background session has an id to stop; the owner closes an
  # interactive one
  local oldid=$(field "$(agents_all)" $me id)
  if [[ -z $oldid ]]; then
    print -r -- "the old manager ($old) is not listed as a background session: close it yourself"
    exit 0
  fi
  local i st
  for (( i = 0; i <= stop_wait; i++ )); do
    st=$(field "$(agents_all)" $me status)
    [[ -z $st ]] && { print -r -- "stopped $old (already gone)"; exit 0 }
    if { [[ $st == idle ]] || { [[ $st == busy && -n $transcript ]] && turn_ended $transcript } } &&
       quiet_enough $transcript $quiet; then
      claude stop $oldid >/dev/null 2>&1
      print -r -- "stopped $old"
      exit 0
    fi
    (( i < stop_wait )) && sleep 60
  done
  print -r -- "left $old running: not between turns and quiet within $stop_wait minutes"
  exit 0
}

# quiet_enough <transcript> <minutes>: unchanged for that long (no transcript: yes)
quiet_enough() {
  [[ -n $1 && -e $1 ]] || return 0
  local -a mt
  zstat -A mt +mtime -- $1 2>/dev/null || return 0
  (( EPOCHSECONDS - mt[1] >= $2 * 60 ))
}

main "$@"; exit $?
