#!/usr/bin/env bash
#
# generate-tool-skills.sh — generate per-tool skill directories from the single
# canonical skills/ tree. Run by CI on push; not meant for hand-editing output.
#
# The Agent Skills FORMAT is portable; only the discovery DIRECTORY differs per
# tool (Claude: .claude/skills, Codex: .agents/skills, Cursor: .cursor/skills).
# `skills/` is the only authored source. The generated dirs are build output.
#
# Usage:
#   scripts/generate-tool-skills.sh            # validate canonical, then generate targets
#   scripts/generate-tool-skills.sh --check    # validate + verify targets match canonical; exit 1 on drift
#
# Env:
#   CANON    canonical skills dir (default: skills)
#   TARGETS  space-separated tool dirs (default: ".claude/skills .agents/skills")
#
set -euo pipefail

CANON="${CANON:-skills}"
read -r -a TARGETS <<< "${TARGETS:-.claude/skills .agents/skills}"
CHECK=0; VALIDATE_ONLY=0
case "${1:-}" in
  --check)         CHECK=1 ;;
  --validate-only) VALIDATE_ONLY=1 ;;
  "" )             : ;;
  * ) echo "unknown arg: $1 (use --check or --validate-only)" >&2; exit 2 ;;
esac

# ---- 1. Validate canonical against the Agent Skills spec -------------------
fail=0
echo "validating $CANON/ against the Agent Skills spec ..."
while IFS= read -r skill; do
  dir="$(basename "$(dirname "$skill")")"
  name="$(awk '/^name:/{print $2; exit}' "$skill")"
  desc="$(awk -F'description:[[:space:]]*' '/^description:/{print $2; exit}' "$skill")"
  [ -z "$name" ]        && { echo "  BAD: $skill — missing 'name'"; fail=1; }
  [ -z "$desc" ]        && { echo "  BAD: $skill — missing 'description'"; fail=1; }
  [ "$name" != "$dir" ] && { echo "  BAD: $skill — name '$name' != dir '$dir'"; fail=1; }
  printf '%s' "$name" | grep -Eq '^[a-z0-9]+(-[a-z0-9]+)*$' || { echo "  BAD: $skill — name not lowercase-kebab"; fail=1; }
  [ "${#name}" -gt 64 ] && { echo "  BAD: $skill — name >64 chars"; fail=1; }
done < <(find "$CANON" -mindepth 2 -maxdepth 2 -name SKILL.md | sort)
[ "$fail" -ne 0 ] && { echo "validation failed"; exit 1; }
echo "  OK — all skills valid"
[ "$VALIDATE_ONLY" -eq 1 ] && exit 0

# ---- 2. Generate (or --check) each target ---------------------------------
marker_note() {
  cat <<EOF
# GENERATED — do not edit

These skills are generated from the canonical \`$CANON/\` tree by
\`scripts/generate-tool-skills.sh\` (CI on push). Edit the skills under
\`$CANON/\` instead; CI regenerates this directory.
EOF
}

for target in "${TARGETS[@]}"; do
  if [ "$CHECK" -eq 1 ]; then
    echo "checking $target/ ..."
    [ ! -d "$target" ] && { echo "  DRIFT: $target missing — run scripts/generate-tool-skills.sh"; fail=1; continue; }
    tmp="$(mktemp -d)"
    rsync -a --delete --exclude='.*' --exclude='__pycache__/' --exclude='*.pyc' "$CANON"/ "$tmp"/; marker_note > "$tmp/GENERATED.md"
    if diff -rq --exclude='.*' "$tmp" "$target" >/dev/null 2>&1; then echo "  OK — in sync";
    else echo "  DRIFT: $target out of sync"; diff -rq --exclude='.*' "$tmp" "$target" || true; fail=1; fi
    rm -rf "$tmp"
  else
    echo "generating $target/ from $CANON/ ..."
    mkdir -p "$target"
    rsync -a --delete --exclude='.*' --exclude='__pycache__/' --exclude='*.pyc' "$CANON"/ "$target"/
    marker_note > "$target/GENERATED.md"
  fi
done

exit "$fail"
