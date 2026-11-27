#!/usr/bin/env bash
# install.sh -- fetch the third-party pieces refining-technical-writing uses.
# Runs as the current user; needs curl and python3, never root.
#
#   Vale          release binary            -> ~/.local/bin/vale
#   Deslop        Vale style pack (release) -> <cache>/vale/styles/Deslop
#   Humanizer     SKILL.md + LICENSE         -> <cache>/humanizer   (pinned commit)
#
# <cache> is ${XDG_DATA_HOME:-~/.local/share}/bozz-agents/refining-technical-writing.
# Each download is compared with the sha256 recorded below and rejected on a
# mismatch. Running the script again only replaces what is out of date.
#
# Moving a pin: read the upstream changes first, then edit the version/commit and
# its checksum(s) here and the matching row in THIRD-PARTY-NOTICES.md. When the
# Humanizer commit changes, the script shows a diff of SKILL.md against the copy
# already cached so the change can be reviewed.
#
# Exit codes: 0 done, 2 unsupported platform, 3 checksum mismatch.
set -euo pipefail

# ---- pins ------------------------------------------------------------------
VALE_VERSION=3.25.1                 # released 2026-10-22
DESLOP_VERSION=v0.3.0               # released 2026-08-13
DESLOP_SHA256=e96e0fe89fd245977de777006b394cd20ab607cf715dc93f42e2aedd2497fee1
HUMANIZER_COMMIT=b48c832f0f809c1b5658edbb838c2521b72f2413   # 2026-11-10, release 4.0.0 merge
HUMANIZER_SKILL_SHA256=804a119e924ac30295b298213e0b71b3e38b2667b8ef4fb7b69e9246369b9045
HUMANIZER_LICENSE_SHA256=4ac4810254ab36d45419141aeb8e69bf50652cfafe5b2dab947d06d44e5cbf96

# Vale release asset name and sha256, per platform.
platform="$(uname -s)/$(uname -m)"
case "$platform" in
  Linux/x86_64)  VALE_ASSET=Linux_64-bit  VALE_SHA256=4bf5c5176b682b1da0830f471584d3494f1c2e27ee3029e1ad6f6661d4962182 ;;
  Linux/aarch64) VALE_ASSET=Linux_arm64   VALE_SHA256=2a69755b68118c612c455fc0c5ea1b9438519aa1c852e3fb303b3ad97141bbb0 ;;
  Darwin/x86_64) VALE_ASSET=macOS_64-bit  VALE_SHA256=e27097e84a812d45546de8d6a4ffa75538cab39c96f79b153b601240f8cefaf9 ;;
  Darwin/arm64)  VALE_ASSET=macOS_arm64   VALE_SHA256=fbcaa68d9b9e229b9c8dc918f209e93572ce943039700b7e04a423ff12f684cd ;;
  *) echo "install.sh: no Vale build is pinned for $platform" >&2; exit 2 ;;
esac

# ---- locations -------------------------------------------------------------
BIN_DIR="$HOME/.local/bin"
VALE_BIN="$BIN_DIR/vale"
CACHE="${XDG_DATA_HOME:-$HOME/.local/share}/bozz-agents/refining-technical-writing"
STYLES="$CACHE/vale/styles"
HUMANIZER="$CACHE/humanizer"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# ---- helpers ---------------------------------------------------------------
digest() {
  if command -v sha256sum >/dev/null; then sha256sum "$1" | awk '{print $1}'
  else shasum -a 256 "$1" | awk '{print $1}'; fi
}

# download <url> <dest> <sha256>: fetch, then refuse anything whose hash differs.
download() {
  curl -fsSL --retry 2 -o "$2" "$1"
  local actual
  actual="$(digest "$2")"
  if [[ "$actual" != "$3" ]]; then
    echo "install.sh: $1 has sha256 $actual, expected $3" >&2
    exit 3
  fi
}

# ---- Vale ------------------------------------------------------------------
vale_current() {
  # A real binary (not a wrapper script) reporting the pinned version.
  [[ -f "$VALE_BIN" ]] || return 1
  [[ "$(head -c 2 "$VALE_BIN")" != "#!" ]] || return 1
  local v
  v="$("$VALE_BIN" --version 2>/dev/null | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -n 1)"
  [[ "$v" == "$VALE_VERSION" ]]
}

if vale_current; then
  echo "Vale $VALE_VERSION: already at $VALE_BIN"
else
  archive="vale_${VALE_VERSION}_${VALE_ASSET}.tar.gz"
  download "https://github.com/vale-cli/vale/releases/download/v${VALE_VERSION}/${archive}" "$tmp/$archive" "$VALE_SHA256"
  tar -xzf "$tmp/$archive" -C "$tmp" vale
  mkdir -p "$BIN_DIR"
  if [[ -e "$VALE_BIN" ]]; then
    kept="$VALE_BIN.previous-$(date +%Y%m%d-%H%M%S)"
    mv "$VALE_BIN" "$kept"
    echo "Kept the earlier $VALE_BIN as $kept"
  fi
  install -m 0755 "$tmp/vale" "$VALE_BIN"
  echo "Vale: installed $("$VALE_BIN" --version) at $VALE_BIN"
fi

# ---- Deslop ----------------------------------------------------------------
stamp="$STYLES/Deslop/.version"
if [[ -f "$stamp" && "$(cat "$stamp")" == "$DESLOP_VERSION" ]]; then
  echo "Deslop $DESLOP_VERSION: already in $STYLES"
else
  download "https://github.com/JMill/deslop/releases/download/${DESLOP_VERSION}/Deslop.zip" "$tmp/deslop.zip" "$DESLOP_SHA256"
  mkdir -p "$STYLES"
  rm -rf "$STYLES/Deslop"
  python3 -I - "$tmp/deslop.zip" "$STYLES" <<'PY'
import sys, zipfile
with zipfile.ZipFile(sys.argv[1]) as z:
    z.extractall(sys.argv[2])
PY
  printf '%s\n' "$DESLOP_VERSION" > "$stamp"
  echo "Deslop: installed $DESLOP_VERSION in $STYLES"
fi

# ---- Humanizer -------------------------------------------------------------
cached_commit="$(cat "$HUMANIZER/SHA" 2>/dev/null || true)"
if [[ "$cached_commit" == "$HUMANIZER_COMMIT" && -f "$HUMANIZER/SKILL.md" ]]; then
  echo "Humanizer ${HUMANIZER_COMMIT:0:7}: already in $HUMANIZER"
else
  base="https://raw.githubusercontent.com/blader/humanizer/$HUMANIZER_COMMIT"
  download "$base/SKILL.md" "$tmp/SKILL.md" "$HUMANIZER_SKILL_SHA256"
  download "$base/LICENSE"  "$tmp/LICENSE"  "$HUMANIZER_LICENSE_SHA256"
  mkdir -p "$HUMANIZER"
  if [[ -f "$HUMANIZER/SKILL.md" ]]; then
    echo "Humanizer moves from ${cached_commit:0:7} to ${HUMANIZER_COMMIT:0:7}; SKILL.md changes:"
    diff -u "$HUMANIZER/SKILL.md" "$tmp/SKILL.md" || true
  fi
  mv -f "$tmp/SKILL.md" "$tmp/LICENSE" "$HUMANIZER/"
  printf '%s\n' "$HUMANIZER_COMMIT" > "$HUMANIZER/SHA"
  date -u +%Y-%m-%dT%H:%MZ > "$HUMANIZER/DATE"
  echo "Humanizer: installed ${HUMANIZER_COMMIT:0:7} in $HUMANIZER"
fi

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo "Tip: $BIN_DIR is not on PATH; the skill still looks for Vale there." ;;
esac
