# sessions.zsh: helpers sourced by ctxpct.sh, ctxcap.sh, watch.zsh and
# manager-handoff.zsh, so every script sizes a session and reads its state the
# same way. Source it; do not run it. Needs jq.

# transcripts_root: where Claude Code keeps session transcripts.
transcripts_root() {
  print -r -- ${CLAUDE_PROJECTS_DIR:-${CLAUDE_CONFIG_DIR:-$HOME/.claude}/projects}
}

# transcript_of <session id>: the path of <session id>.jsonl, searched up to
# two levels below transcripts_root; prints nothing when there is none.
transcript_of() {
  [[ -n ${1-} ]] || return 1
  local root=$(transcripts_root)
  local -a hits=( $root/$1.jsonl(N) $root/*/$1.jsonl(N) )
  (( $#hits )) || return 1
  print -r -- $hits[1]
}

# call_sizes <transcript> [line limit]
#   One "<message id> <tokens>" line per model call of the main conversation,
#   oldest first. <tokens> is everything the call sent the model:
#   input_tokens + cache_read_input_tokens + cache_creation_input_tokens.
#   Subagent (sidechain) records and synthetic records are skipped, and a call
#   written as several lines (one per content block) counts once. With a line
#   limit, only that many transcript lines that carry usage are read.
call_sizes() {
  local file=$1 limit=${2:-0}
  [[ -r $file ]] || return 1
  {
    if (( limit > 0 )); then grep -F '"usage"' -- $file | head -n $limit
    else grep -F '"usage"' -- $file; fi
  } 2>/dev/null |
    jq -rR 'fromjson? // empty
      | select(.type == "assistant")
      | select((.isSidechain // false) | not)
      | select(.message.model != "<synthetic>")
      | .message
      | {id: (.id // "-"),
         n: ([.usage.input_tokens, .usage.cache_read_input_tokens, .usage.cache_creation_input_tokens]
             | map(. // 0) | add)}
      | select(.n > 0)
      | "\(.id) \(.n)"' 2>/dev/null |
    awk '$1 == "-" || !seen[$1]++'
}

# latest_size <transcript>: the token size of the newest main-conversation call.
latest_size() { call_sizes $1 | tail -n 1 | awk '{print $2}' }

# largest_early_size <transcript>: the largest size among the first 15 calls,
# which hold a session's start-up reads. Only the first 400 usage lines are
# read, so a hook that runs on every tool call does not parse a long
# transcript twice.
largest_early_size() {
  call_sizes $1 400 | sed -n '1,15p' | awk '{ if ($2 > big) big = $2 } END { print big + 0 }'
}

# agents_all: the agent list including stopped and retired sessions (they
# have no status). Falls back to the plain list where `--all` is not known.
agents_all() {
  claude agents --json --all 2>/dev/null || claude agents --json 2>/dev/null
}

# starting_q: jq condition for a session that was launched moments ago. For
# about its first second the agent view lists it with state "working" and no
# status yet, so it is not gone.
starting_q='(.status == null and .state == "working")'

# turn_ended <transcript>: the session's last turn has finished. A session
# whose turn is over still lists as busy while a background task it started
# runs, so busy alone does not mean it is mid-turn.
turn_ended() {
  local last
  last=$(jq -rR 'fromjson? // empty
      | select(.type | IN("user", "assistant", "system"))
      | [.type, (.subtype // "")] | join("/")' < $1 2>/dev/null | tail -1)
  [[ $last == system/turn_duration ]]
}
