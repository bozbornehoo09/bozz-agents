#!/bin/zsh
# ctxcap.sh: the size cap behind the worker contract's "Context budget" and the
# manager's "Succession". Claude Code runs it as a PostToolUse hook from the
# plugin's hooks/hooks.json (through hooks/ctxcap-hook.sh).
#
# USAGE
#   ctxcap.sh                    hook mode: reads the hook's JSON on stdin
#   ctxcap.sh hold <session id>  record the session's current size as its hold
#                                (manager-handoff.zsh runs this when a handoff fails)
#
# A plugin hook runs in every session that has the plugin enabled, so hook mode
# gates itself and prints nothing unless all of these hold:
#   - BOZZ_CTXCAP is not "off";
#   - the input's agent_type is a session role started with --agent, as the
#     plugin's session reports it: bozz-agents:manager, bozz-agents:architect
#     or bozz-agents:implementer. A bare manager, architect or implementer
#     counts only with BOZZ_CTXCAP_BARE=1 (agent files copied into your own
#     agents folder), since another tool's agent may share the name;
#   - the input has no agent_id (the call is not inside a subagent);
#   - the newest main-conversation call is at least 85% of the role's cap;
#   - that size is at least 40k above the largest of the first 15 calls (a
#     successor that starts large does not hand off at once) and 40k above any
#     hold (a handoff that just failed is not retried at once).
# When it speaks, it prints one PostToolUse additionalContext note, at most once
# per 10k step: below the cap, "keep turns lean, start no new review pass"; at
# or past the cap, "hand off now", by the worker prompt's Handoff rules or, for
# the manager, by agents/manager.md's Succession. It always exits 0, so a fault
# never shows as a hook error on every tool call.
#
# SETTINGS (environment; a background session reads its environment from the
# background service, so set these in the user settings' "env" block)
#   BOZZ_CTXCAP=off          turn the hook off
#   BOZZ_CTXCAP_WORKER_K     architect and implementer cap, thousands (default 350)
#   BOZZ_CTXCAP_MANAGER_K    manager cap, thousands (default 150)
#   BOZZ_CTXCAP_BARE=1       also gate bare manager|architect|implementer
#   BOZZ_CTXCAP_DIR          state folder (default $TMPDIR/bozz-ctxcap-$UID):
#                            <session id>/step-<n> marks and <session id>/hold
# Requires jq; the size is call_sizes' sum in sessions.zsh.

typeset -g CTXCAP_HERE=${0:A:h}

main() {
  emulate -L zsh
  (( $+commands[jq] )) || return 0
  source $CTXCAP_HERE/sessions.zsh
  local state=${BOZZ_CTXCAP_DIR:-${TMPDIR:-/tmp}/bozz-ctxcap-$UID}
  if [[ ${1-} == hold ]]; then
    record_hold ${2-}
    return
  fi
  [[ ${BOZZ_CTXCAP:-on} == off ]] && return 0
  check_call
  return 0
}

# role_of <agent type>: the session role, or failure.
role_of() {
  local type=$1
  if [[ $type == bozz-agents:* ]]; then
    print -r -- ${type#bozz-agents:}
  elif [[ $type != *:* && ${BOZZ_CTXCAP_BARE-} == 1 ]]; then
    print -r -- $type
  else
    return 1
  fi
}

# role_cap <role>: the cap in thousands for a session role, or failure.
role_cap() {
  case $1 in
    (manager) print -r -- ${BOZZ_CTXCAP_MANAGER_K:-150} ;;
    (architect|implementer) print -r -- ${BOZZ_CTXCAP_WORKER_K:-350} ;;
    (*) return 1 ;;
  esac
}

record_hold() {
  local sid=$1 file k
  file=$(transcript_of $sid) || { print -u2 -r -- "ctxcap.sh: no transcript for ${sid:-<none>}"; return 1 }
  k=$(latest_size $file)
  [[ $k == <-> ]] || { print -u2 -r -- "ctxcap.sh: no model call in $file"; return 1 }
  mkdir -p -- $state/$sid && print -r -- $(( k / 1000 )) > $state/$sid/hold
}

check_call() {
  local input=$(cat)
  local -a v
  v=( "${(@f)$(jq -r '.agent_type // "", .agent_id // "", .session_id // "", .transcript_path // ""' <<<$input 2>/dev/null)}" )
  (( $#v == 4 )) || return 0
  local atype=$v[1] aid=$v[2] sid=$v[3] file=$v[4]
  [[ -z $aid && -n $sid && -r $file ]] || return 0
  local role cap
  role=$(role_of $atype) || return 0
  cap=$(role_cap $role) || return 0
  [[ $cap == <1-> ]] || return 0

  local size=$(latest_size $file)
  [[ $size == <-> ]] || return 0
  local k=$(( size / 1000 ))
  (( k * 100 >= cap * 85 )) || return 0
  local early=$(( $(largest_early_size $file) / 1000 ))
  (( k >= early + 40 )) || return 0
  local hold
  [[ -r $state/$sid/hold ]] && hold=$(<$state/$sid/hold)
  [[ $hold == <-> ]] && (( k < hold + 40 )) && return 0
  # mkdir is atomic: two hooks on one call cannot both claim a step
  mkdir -p -- $state/$sid 2>/dev/null && mkdir -- $state/$sid/step-$(( k / 10 )) 2>/dev/null || return 0

  local note
  if [[ $role == manager ]] && (( k >= cap )); then
    note="Context is ${k}k tokens, at or past this session's ${cap}k cap. Hand off now, by your prompt's Succession section: with nothing live or queued, close the session; otherwise write NEXT-SESSION-PROMPT.md and MANAGER-STATE.md, start manager-handoff.zsh handoff in the background, and finish the turn."
  elif [[ $role == manager ]]; then
    note="Context is ${k}k tokens of this session's ${cap}k cap. Keep turns lean and start no fan-out; at ${cap}k, hand off by your prompt's Succession section."
  elif (( k >= cap )); then
    note="Context is ${k}k tokens, at or past this session's ${cap}k cap. Hand off now, by your prompt's Handoff rules; their exceptions still apply (fold reviews that have completed first; finish a go's steps in the session holding the go)."
  else
    note="Context is ${k}k tokens of this session's ${cap}k cap. Keep turns short and start no new review pass or subagent fan-out; at ${cap}k, hand off by your prompt's Handoff rules."
  fi
  jq -nc --arg note $note '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $note}}'
}

main "$@"; exit $?
