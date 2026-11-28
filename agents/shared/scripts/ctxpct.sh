#!/bin/zsh
# Usage: ctxpct.sh [-k] <session id | agent id | session name>
#
# Reports how large a Claude Code session's newest main-conversation call was.
#   default: an integer percentage of $CONTEXT_WINDOW_TOKENS (1000000 when unset)
#   -k:      thousands of tokens, the unit the size caps use (350 = 350k)
# The size is call_sizes' sum in sessions.zsh (input + cache read + cache
# write tokens; subagent and synthetic records skipped). The transcript is
# <session id>.jsonl below the transcripts folder; an agent id or a session
# name is first turned into a session id with `claude agents --json`.
# On any failure (no transcript, no call yet, another host) it prints "?" and
# exits 1. Requires jq.

emulate -L zsh
setopt pipefail
source ${0:A:h}/sessions.zsh

unit=pct
[[ ${1-} == -k ]] && { unit=k; shift }
key=${1-}
window=${CONTEXT_WINDOW_TOKENS:-1000000}

unknown() { print -r -- '?'; exit 1 }

[[ -n $key ]] || unknown
file=$(transcript_of $key)
if [[ -z $file ]]; then
  sid=$(claude agents --json 2>/dev/null |
        jq -r --arg k "$key" '[.[] | select(.id == $k or .name == $k)][0].sessionId // empty' 2>/dev/null)
  file=$(transcript_of $sid)
fi
[[ -n $file ]] || unknown

used=$(latest_size $file)
[[ $used == <-> ]] || unknown
if [[ $unit == k ]]; then
  print -r -- $(( used / 1000 ))
else
  [[ $window == <-> ]] && (( window > 0 )) || unknown
  print -r -- $(( used * 100 / window ))
fi
