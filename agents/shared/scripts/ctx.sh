#!/bin/zsh
# Usage: ctx.sh <session-name prefix>
#
# For every Claude Code session listed by `claude agents --json` whose name
# begins with the prefix and which reports a status, prints one line:
#   <name with the prefix removed> <status> <size>k
# where <size> is the session's newest call in thousands of tokens, from
# `ctxpct.sh -k` in this folder ("?" when unknown), the unit the size caps
# use. Requires jq.

emulate -L zsh
prefix=$1
dir=${0:A:h}

claude agents --json |
  jq -r --arg p "$prefix" '
    .[] | select(.status != null and ((.name // "") | startswith($p)))
        | [.sessionId, (.name | ltrimstr($p)), .status] | @tsv' |
  while IFS=$'\t' read -r sid short state; do
    print -r -- "$short $state $(zsh $dir/ctxpct.sh -k $sid)k"
  done
