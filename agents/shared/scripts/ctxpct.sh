#!/bin/zsh
# Usage: ctxpct.sh <session id | agent id | session name>
#
# Reports how much of a Claude Code session's context window its most recent
# assistant turn used, as an integer percentage.
#   used   = input_tokens + cache_read_input_tokens + cache_creation_input_tokens
#   window = $CONTEXT_WINDOW_TOKENS, or 1000000 when unset
# The transcript is <session id>.jsonl, found up to two levels below
# $CLAUDE_PROJECTS_DIR (default ~/.claude/projects). An agent id or a session
# name is first turned into a session id with `claude agents --json`.
# On any failure (no transcript, no assistant turn yet, another host) it
# prints "?" and exits 1. Requires jq.

emulate -L zsh
setopt pipefail

root=${CLAUDE_PROJECTS_DIR:-$HOME/.claude/projects}
window=${CONTEXT_WINDOW_TOKENS:-1000000}
key=$1

unknown() { print -r -- '?'; exit 1 }

transcript_for() {
  [[ -n $1 ]] || return 1
  local hits=( $root/$1.jsonl(N) $root/*/$1.jsonl(N) )
  (( $#hits )) && print -r -- $hits[1]
}

[[ -n $key ]] || unknown
file=$(transcript_for $key)
if [[ -z $file ]]; then
  sid=$(claude agents --json 2>/dev/null |
        jq -r --arg k "$key" '[.[] | select(.id == $k or .name == $k)][0].sessionId // empty' 2>/dev/null)
  file=$(transcript_for $sid)
fi
[[ -n $file && -r $file ]] || unknown

# Stream the transcript; keep only assistant turns that report cache reads,
# emit each one's token total, and keep the last.
used=$(jq -r 'select(.type == "assistant")
              | .message.usage? // empty
              | select((.cache_read_input_tokens // 0) > 0)
              | (.input_tokens // 0) + .cache_read_input_tokens + (.cache_creation_input_tokens // 0)' \
         $file 2>/dev/null | tail -n 1)

[[ $used == <-> && $window == <-> ]] && (( window > 0 )) || unknown
print -r -- $(( used * 100 / window ))
