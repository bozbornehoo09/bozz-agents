#!/bin/sh
# Entry point for the plugin's PostToolUse size-cap hook (hooks/hooks.json).
# The hook runs in every session that has the plugin enabled, so this wrapper
# only hands stdin to agents/shared/scripts/ctxcap.sh, which gates itself, and
# exits 0 without a word where zsh is not installed.
command -v zsh >/dev/null 2>&1 || exit 0
here=$(cd "$(dirname "$0")" && pwd) || exit 0
exec zsh "$here/../agents/shared/scripts/ctxcap.sh"
