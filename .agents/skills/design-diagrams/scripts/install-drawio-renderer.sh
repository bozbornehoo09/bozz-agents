#!/usr/bin/env bash
# install-drawio-renderer.sh -- set up what render-drawio.sh needs, as the current
# user, with no root and no package manager writes.
#
# Usage:
#   install-drawio-renderer.sh           install, or repair a partial install (safe to re-run)
#   install-drawio-renderer.sh --check   only report what is present; change nothing
#
# What gets installed:
#   draw.io desktop, a pinned release of https://github.com/jgraph/drawio-desktop
#   (Apache-2.0). The release asset is checked against the sha512 that the same
#   release lists in its electron-builder manifest before it is unpacked.
#     macOS  draw.io-<arm64|x64>-<version>.zip, manifest latest-mac.yml,
#            unpacked to $DRAWIO_HOME/app/draw.io.app. A draw.io.app already in
#            /Applications or ~/Applications is accepted as is.
#     Linux  drawio-<x86_64|arm64>-<version>.AppImage, manifest latest-linux*.yml,
#            extracted with --appimage-extract (no FUSE needed) to $DRAWIO_HOME/app.
#   Linux also needs Xvfb and the Liberation Sans font (it has Arial's metrics,
#   and draw.io styles ask for Arial/Helvetica). Those come from the system
#   package manager, so --check prints the command for the owner to run; this
#   script never calls sudo.
#
# Settings: DRAWIO_VERSION picks the release (default below); DRAWIO_HOME is the
# install root (default ~/.local/opt/drawio), which render-drawio.sh also reads.
#
# Exit 0 when everything is present, 1 when a part is missing or a step failed
# (the message says which and how to fix it), 2 on a bad argument.
set -euo pipefail

DRAWIO_VERSION="${DRAWIO_VERSION:-31.7.0}"
DRAWIO_HOME="${DRAWIO_HOME:-$HOME/.local/opt/drawio}"
RELEASES="https://github.com/jgraph/drawio-desktop/releases/download/v${DRAWIO_VERSION}"

mode=install
if (( $# > 1 )); then echo "usage: $0 [--check]" >&2; exit 2; fi
case "${1:-}" in
  "")      ;;
  --check) mode=check ;;
  *)       echo "usage: $0 [--check]" >&2; exit 2 ;;
esac

note() { printf '%s\n' "$*"; }
fail() { printf 'install-drawio-renderer: %s\n' "$*" >&2; exit 1; }

# Suggest the right install command for a system package on this distro.
suggest_pkg() {  # suggest_pkg <debian-name> <fedora-name>
  if   command -v apt-get >/dev/null; then echo "sudo apt-get install -y $1"
  elif command -v dnf     >/dev/null; then echo "sudo dnf install -y $2"
  elif command -v yum     >/dev/null; then echo "sudo yum install -y $2"
  else echo "install '$1' with the system package manager"; fi
}

installed_version() { cat "$DRAWIO_HOME/VERSION" 2>/dev/null || echo unknown; }

# Print the base64 sha512 that manifest $1 lists for asset $2 (electron-builder
# writes "- url: <asset>" with "sha512: <digest>" on the next line).
manifest_digest() {
  curl -fsSL "$RELEASES/$1" | awk -v asset="$2" '
    $1 == "-" && $2 == "url:" { hit = ($3 == asset); next }
    hit && $1 == "sha512:"    { print $2; exit }'
}

# Download asset $1 into $2 and confirm it matches the digest in manifest $3.
fetch_verified() {
  local asset="$1" dest="$2" manifest="$3" expected actual
  note "Fetching $RELEASES/$asset"
  curl -fsSL --retry 2 -o "$dest" "$RELEASES/$asset"
  expected="$(manifest_digest "$manifest" "$asset")"
  [[ -n "$expected" ]] || fail "$manifest has no sha512 entry for $asset"
  actual="$(python3 -I -c 'import base64, hashlib, sys
h = hashlib.sha512()
with open(sys.argv[1], "rb") as f:
    for block in iter(lambda: f.read(1 << 20), b""):
        h.update(block)
print(base64.b64encode(h.digest()).decode())' "$dest")"
  [[ "$actual" == "$expected" ]] || fail "sha512 of $asset does not match $manifest"
}

needs_download() { [[ ! -x "$1" || "$(installed_version)" != "$DRAWIO_VERSION" ]]; }

prepare_download() {
  command -v curl    >/dev/null || fail "curl is required"
  command -v python3 >/dev/null || fail "python3 is required (it checks the sha512)"
  mkdir -p "$DRAWIO_HOME"
  work="$(mktemp -d)"
  trap 'rm -rf "$work"' EXIT
}

# ---------------------------------------------------------------- macOS
if [[ "$(uname -s)" == Darwin ]]; then
  for bundle in "/Applications/draw.io.app" "$HOME/Applications/draw.io.app"; do
    if [[ -x "$bundle/Contents/MacOS/draw.io" ]]; then note "present  draw.io  $bundle"; exit 0; fi
  done
  bundle="$DRAWIO_HOME/app/draw.io.app"
  if [[ "$mode" == check ]]; then
    if [[ -x "$bundle/Contents/MacOS/draw.io" ]]; then note "present  draw.io  $bundle ($(installed_version))"; exit 0; fi
    note "missing  draw.io desktop (run this script without --check)"; exit 1
  fi
  case "$(uname -m)" in
    arm64)  mac_arch=arm64 ;;
    x86_64) mac_arch=x64 ;;
    *)      fail "no draw.io build for $(uname -m)" ;;
  esac
  if needs_download "$bundle/Contents/MacOS/draw.io"; then
    prepare_download
    asset="draw.io-${mac_arch}-${DRAWIO_VERSION}.zip"
    fetch_verified "$asset" "$work/drawio.zip" latest-mac.yml
    ditto -x -k "$work/drawio.zip" "$work/unpacked"
    [[ -d "$work/unpacked/draw.io.app" ]] || fail "$asset did not contain draw.io.app"
    rm -rf "$DRAWIO_HOME/app"; mkdir -p "$DRAWIO_HOME/app"
    mv "$work/unpacked/draw.io.app" "$DRAWIO_HOME/app/"
    echo "$DRAWIO_VERSION" > "$DRAWIO_HOME/VERSION"
  fi
  note "present  draw.io  $bundle ($(installed_version))"
  exit 0
fi

# ---------------------------------------------------------------- Linux
case "$(uname -m)" in
  x86_64)        linux_arch=x86_64; manifest=latest-linux.yml ;;
  aarch64|arm64) linux_arch=arm64;  manifest=latest-linux-arm64.yml ;;
  *)             fail "no draw.io build for $(uname -m)" ;;
esac
exe="$DRAWIO_HOME/app/drawio"

report() {
  local rc=0
  if [[ -x "$exe" ]]; then note "present  draw.io  $exe ($(installed_version))"
  else note "missing  draw.io desktop (run this script without --check)"; rc=1; fi
  if command -v Xvfb >/dev/null; then note "present  Xvfb     $(command -v Xvfb)"
  else note "missing  Xvfb -- $(suggest_pkg xvfb xorg-x11-server-Xvfb)"; rc=1; fi
  if command -v fc-match >/dev/null && fc-match -f '%{family}\n' Arial | grep -qi liberation; then
    note "present  font     Liberation Sans"
  else
    note "missing  Liberation Sans -- $(suggest_pkg fonts-liberation liberation-sans-fonts); without it labels render in a wider fallback font"
    rc=1
  fi
  return "$rc"
}

if [[ "$mode" == check ]]; then report; exit $?; fi

if needs_download "$exe"; then
  prepare_download
  asset="drawio-${linux_arch}-${DRAWIO_VERSION}.AppImage"
  fetch_verified "$asset" "$work/drawio.AppImage" "$manifest"
  chmod +x "$work/drawio.AppImage"
  ( cd "$work" && ./drawio.AppImage --appimage-extract >/dev/null )
  rm -rf "$DRAWIO_HOME/app"
  mv "$work/squashfs-root" "$DRAWIO_HOME/app"
  echo "$DRAWIO_VERSION" > "$DRAWIO_HOME/VERSION"
fi

report
