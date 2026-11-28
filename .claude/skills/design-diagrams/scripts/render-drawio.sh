#!/usr/bin/env bash
# render-drawio.sh -- turn one .drawio source into a PNG or JPG without a GUI session.
#
# Usage:
#   render-drawio.sh SOURCE.drawio TARGET.(png|jpg) [--scale N] [--page N]
#
#   --scale N   zoom factor for the export (default 2)
#   --page N    which diagram page to export, counting from 1 (default 1)
#
# The image format follows TARGET's extension. On Linux, when no DISPLAY is set,
# the script runs a throwaway Xvfb server for this one export; Xvfb is asked to
# pick its own display number, so several renders can run side by side.
# Set up the renderer beforehand with install-drawio-renderer.sh.
#
# Output contract:
#   stdout  -- the TARGET path and nothing else, on success
#   stderr  -- the renderer's log and any error text
#   exit 0  -- image written
#   exit 1  -- the renderer ran but produced no image (or timed out)
#   exit 2  -- invalid arguments
#   exit 3  -- no renderer available; the caller should fall back to a manual
#              export by the owner
set -euo pipefail

bad_args() { echo "render-drawio: $*" >&2; echo "usage: $0 SOURCE.drawio TARGET.(png|jpg) [--scale N] [--page N]" >&2; exit 2; }
missing_renderer() { echo "NO-RENDERER: $* -- install it with install-drawio-renderer.sh" >&2; exit 3; }

(( $# >= 2 )) || bad_args "need a source and a target"
src="$1"; dst="$2"; shift 2
zoom=2; page=1
while (( $# > 0 )); do
  flag="$1"; value="${2:-}"
  [[ -n "$value" ]] || bad_args "$flag needs a value"
  case "$flag" in
    --scale) zoom="$value" ;;
    --page)  page="$value" ;;
    *)       bad_args "unknown option $flag" ;;
  esac
  shift 2
done

[[ "$zoom" =~ ^[0-9]+(\.[0-9]+)?$ ]] || bad_args "--scale takes a number"
[[ "$page" =~ ^[1-9][0-9]*$ ]]       || bad_args "--page takes a whole number from 1"
[[ -f "$src" ]]                      || bad_args "source not found: $src"
ext="$(printf '%s' "${dst##*.}" | tr '[:upper:]' '[:lower:]')"
case "$ext" in
  png)      format=png ;;
  jpg|jpeg) format=jpg ;;
  *)        bad_args "target must end in .png or .jpg" ;;
esac

drawio_home="${DRAWIO_HOME:-$HOME/.local/opt/drawio}"
os="$(uname -s)"

# Locate the draw.io executable for this platform.
find_drawio() {
  if [[ "$os" == Darwin ]]; then
    local bundle
    for bundle in "$drawio_home/app/draw.io.app" "/Applications/draw.io.app" "$HOME/Applications/draw.io.app"; do
      if [[ -x "$bundle/Contents/MacOS/draw.io" ]]; then echo "$bundle/Contents/MacOS/draw.io"; return; fi
    done
  else
    if [[ -x "$drawio_home/app/drawio" ]]; then echo "$drawio_home/app/drawio"; return; fi
    command -v drawio 2>/dev/null || true
  fi
}
exe="$(find_drawio)"
[[ -n "$exe" && -x "$exe" ]] || missing_renderer "draw.io desktop not found"

extra_flags=()
[[ "$os" == Darwin ]] || extra_flags=(--no-sandbox --disable-gpu)

scratch="$(mktemp -d)"
xvfb_pid=""
on_exit() {
  if [[ -n "$xvfb_pid" ]]; then kill "$xvfb_pid" 2>/dev/null || true; fi
  rm -rf "$scratch"
}
trap on_exit EXIT
trap 'exit 130' INT TERM

display_env=()
if [[ "$os" != Darwin && -z "${DISPLAY:-}" ]]; then
  command -v Xvfb >/dev/null || missing_renderer "Xvfb is not installed"
  # With -displayfd, Xvfb writes the display number it chose to fd 3 once it is ready.
  Xvfb -displayfd 3 -screen 0 1920x1080x24 -nolisten tcp 3>"$scratch/dpy" 2>"$scratch/xvfb.err" &
  xvfb_pid=$!
  waited=0
  until [[ -s "$scratch/dpy" ]]; do
    if ! kill -0 "$xvfb_pid" 2>/dev/null; then
      missing_renderer "Xvfb stopped during startup: $(tr '\n' ' ' < "$scratch/xvfb.err" | cut -c1-300)"
    fi
    (( waited < 100 )) || missing_renderer "Xvfb was not ready after 10 seconds"
    sleep 0.1; waited=$((waited + 1))
  done
  display_env=("DISPLAY=:$(tr -dc '0-9' < "$scratch/dpy")")
fi

# Bound the export at three minutes when a timeout tool exists (GNU timeout, or
# gtimeout from coreutils on macOS); otherwise let it run.
limit=()
for t in timeout gtimeout; do
  if command -v "$t" >/dev/null; then limit=("$t" 180); break; fi
done

rm -f "$dst"
status=0
env ${display_env[@]+"${display_env[@]}"} ${limit[@]+"${limit[@]}"} \
  "$exe" ${extra_flags[@]+"${extra_flags[@]}"} \
  --export --format "$format" --scale "$zoom" --page-index "$page" --output "$dst" "$src" \
  >"$scratch/drawio.log" 2>&1 || status=$?

if (( status == 0 )) && [[ -s "$dst" ]]; then
  # Electron prints harmless dbus/GPU chatter; keep only the remaining lines.
  grep -v -E 'dbus|Fontconfig|gpu|GPU|viz_main|ozone|libva|sandbox' "$scratch/drawio.log" >&2 || true
  echo "$dst"
  exit 0
fi

# On failure show the full log: the line that explains it may look like chatter.
cat "$scratch/drawio.log" >&2
if (( status == 124 )); then echo "render-drawio: export timed out after 180 seconds" >&2; exit 1; fi
echo "render-drawio: no image produced at $dst (renderer exit $status)" >&2
exit 1
