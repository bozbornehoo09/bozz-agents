#!/usr/bin/env bash
# review-loop.sh <loop-dir> <repo-dir> <base> <description-file> <spec-file|-> [<precedent-dir>...]
#
# Runs a single pre-flight review loop (preparing-code-reviews, step 6) on the
# commits <base>..HEAD of <repo-dir>. There are three stages, and every
# session in them is a new, read-only reviewer that starts with no memory:
#
#   lenses     one session per code-review brief, all at once; each writes
#              1-review-<lens>.md, and the set is concatenated into 1-review.md
#   challenge  one session that tests every finding against the code and
#              writes 2-challenge.md
#   defense    one session that keeps or concedes each finding, lists the
#              survivors and ends with code-review's Verdict line (3-final.md)
#
# stderr of each session lands in <output>.err. On success the script prints
# the COUNTS and Verdict lines of 3-final.md.
#
# Retries: a session that exits non-zero, or whose output lacks its expected
# closing line, gets exactly one more attempt after REVIEW_RETRY_PAUSE seconds
# (default 30). Exit status: 0 the loop finished; 1 a session failed on its
# retry; 2 an argument or input is missing or invalid.
#
# Optional environment:
#   REVIEW_CMD       reviewer command line, split on spaces. The prompt is
#                    passed as its final argument; its stdout is the result.
#                    e.g. REVIEW_CMD="codex exec --sandbox read-only".
#                    Default: `claude -p` with read-only tools, given access to
#                    only the directories this loop needs.
#   REVIEW_BRIEFS    brief files to use, space-separated. Default: the
#                    code-review skill's references/lens-*.md; if there are
#                    none, every references/*.md except templates (_*.md) and
#                    register.md.
#   CODE_REVIEW_DIR  location of the code-review skill (default: the sibling
#                    directory ../../code-review relative to this script).
#   DECLINED         DECLINED.md files from earlier loops, space-separated.
#   DECISIONS        decision files (ADRs, a decision log, plan notes).
#   REGISTER         the project's overrides register, if one exists.
set -u

die() { local code=$1; shift; echo "$*" >&2; exit "$code"; }

[ $# -ge 5 ] || die 2 "usage: $0 <loop-dir> <repo-dir> <base> <description-file> <spec-file|-> [<precedent-dir>...]"
LOOP_DIR=$1; REPO=$2; BASE=$3; DESC=$4; SPEC=$5; shift 5
PRECEDENT_DIRS=("$@")

# --- locate code-review and its briefs ------------------------------------
SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
CR_DIR="${CODE_REVIEW_DIR:-$SELF_DIR/../../code-review}"
[ -f "$CR_DIR/SKILL.md" ] || die 2 "not found: $CR_DIR/SKILL.md"
CR_DIR="$(cd "$CR_DIR" && pwd)"
CR_SKILL="$CR_DIR/SKILL.md"

BRIEFS=()
if [ -n "${REVIEW_BRIEFS:-}" ]; then
  read -r -a BRIEFS <<< "$REVIEW_BRIEFS"
else
  for f in "$CR_DIR"/references/lens-*.md; do
    [ -f "$f" ] && BRIEFS+=("$f")
  done
  if [ ${#BRIEFS[@]} -eq 0 ]; then
    for f in "$CR_DIR"/references/*.md; do
      base_name=$(basename "$f")
      case "$base_name" in _*|register.md) continue ;; esac
      [ -f "$f" ] && BRIEFS+=("$f")
    done
  fi
fi
[ ${#BRIEFS[@]} -gt 0 ] || die 2 "no review briefs found under $CR_DIR/references (start one from _brief-template.md, or set REVIEW_BRIEFS)"

# --- validate inputs ------------------------------------------------------
read -r -a DECLINED_FILES <<< "${DECLINED:-}"
read -r -a DECISION_FILES <<< "${DECISIONS:-}"
REG_FILE=${REGISTER:-}
[ "$SPEC" = "-" ] && SPEC=""

for f in "$DESC" ${SPEC:+"$SPEC"} ${REG_FILE:+"$REG_FILE"} "${BRIEFS[@]}" \
         ${DECLINED_FILES[@]+"${DECLINED_FILES[@]}"} ${DECISION_FILES[@]+"${DECISION_FILES[@]}"}; do
  [ -f "$f" ] || die 2 "not found: $f"
done
for d in ${PRECEDENT_DIRS[@]+"${PRECEDENT_DIRS[@]}"}; do
  [ -d "$d" ] || die 2 "precedent checkout is not a directory: $d"
done
HEAD_SHA=$(git -C "$REPO" rev-parse HEAD) || exit 2
git -C "$REPO" rev-parse --verify --quiet "$BASE^{commit}" >/dev/null || die 2 "base is not a commit: $BASE"
mkdir -p "$LOOP_DIR"

# --- reviewer command -----------------------------------------------------
if [ -n "${REVIEW_CMD:-}" ]; then
  read -r -a REVIEWER <<< "$REVIEW_CMD"
else
  ACCESS=()
  grant() { local d; for d in "$@"; do ACCESS+=(--add-dir "$d"); done; }
  grant "$REPO" "$LOOP_DIR" "$(dirname "$DESC")" "$CR_DIR"
  [ -n "$SPEC" ] && grant "$(dirname "$SPEC")"
  grant ${PRECEDENT_DIRS[@]+"${PRECEDENT_DIRS[@]}"}
  for f in "${BRIEFS[@]}" ${REG_FILE:+"$REG_FILE"} \
           ${DECLINED_FILES[@]+"${DECLINED_FILES[@]}"} ${DECISION_FILES[@]+"${DECISION_FILES[@]}"}; do
    grant "$(dirname "$f")"
  done
  REVIEWER=(claude -p --permission-mode dontAsk
            --allowedTools Read Grep Glob
              "Bash(git -C $REPO diff:*)" "Bash(git -C $REPO show:*)" "Bash(git -C $REPO log:*)"
            "${ACCESS[@]}" --no-session-persistence)
fi

# --- shared prompt context ------------------------------------------------
PRECEDENT_LIST="${PRECEDENT_DIRS[*]:-}"
CONTEXT="Context for this review.
- Change under review: commits $BASE..$HEAD_SHA in $REPO (read them with git -C $REPO diff $BASE..$HEAD_SHA).
- Description file, reviewed as part of the change: $DESC.
- Spec: ${SPEC:-none given; use the description file as the spec}.
- Precedent checkouts, read-only: ${PRECEDENT_LIST:-none}.
- Overrides register: ${REG_FILE:-none}.
- Decisions: ${DECISIONS:-none}.
- Declined in earlier loops (deliberate scope; do not raise them again): ${DECLINED:-none}.
Rules. $CR_SKILL defines the evidence contract, the BLOCK/FIX/SUGGEST severities, the verdict and the finding layout; each brief defines what its lens checks. Judge simplicity and correctness. When the code faithfully does what the spec says but the spec is wrong, tag the finding PLAN and quote both the spec line and the code at file:line. Open only what your task needs. Do not modify any file. Reply in Markdown with no preamble."

# --- running sessions -----------------------------------------------------
lens_of() { local n; n=$(basename "$1" .md); echo "${n#lens-}"; }

# attempt <prompt> <out> <expected-regex> <stderr-redirect-mode>
attempt() {
  if [ "$4" = append ]; then "${REVIEWER[@]}" "$1" > "$2" 2>> "$2.err"
  else "${REVIEWER[@]}" "$1" > "$2" 2> "$2.err"; fi && grep -q -E "$3" "$2"
}
# retry: the single second attempt; a second failure ends the loop with 1.
retry() {
  sleep "${REVIEW_RETRY_PAUSE:-30}"
  attempt "$1" "$2" "$3" append && return
  die 1 "reviewer session failed on retry or produced no result: $2 (details in $2.err)"
}
session() { attempt "$1" "$2" "$3" new || retry "$1" "$2" "$3"; }

lens_prompt() {
  local lens; lens=$(lens_of "$1")
  echo "TASK: lens review [$lens]. Read $CR_SKILL and then the brief $1. Review the change strictly through this one lens. $CONTEXT
Give each finding an id of the form $lens-<n>. No findings is an acceptable result. Your last line must be 'COUNTS: BLOCK <n> FIX <n> SUGGEST <n>'."
}

# Stage 1. All lenses start together. Retries wait until every first attempt
# has exited and then go one by one, so a rate-limited host sees one session
# at a time and nothing is still running when the script exits.
pids=(); retry_list=()
for b in "${BRIEFS[@]}"; do
  out="$LOOP_DIR/1-review-$(lens_of "$b").md"
  "${REVIEWER[@]}" "$(lens_prompt "$b")" > "$out" 2> "$out.err" &
  pids+=($!)
done
for i in "${!BRIEFS[@]}"; do
  out="$LOOP_DIR/1-review-$(lens_of "${BRIEFS[$i]}").md"
  wait "${pids[$i]}" && grep -q '^COUNTS:' "$out" || retry_list+=("${BRIEFS[$i]}")
done
for b in ${retry_list[@]+"${retry_list[@]}"}; do
  retry "$(lens_prompt "$b")" "$LOOP_DIR/1-review-$(lens_of "$b").md" '^COUNTS:'
done
for b in "${BRIEFS[@]}"; do
  printf '## Findings from the %s lens\n\n' "$(lens_of "$b")"
  cat "$LOOP_DIR/1-review-$(lens_of "$b").md"
  printf '\n'
done > "$LOOP_DIR/1-review.md"

# Stage 2.
session "TASK: challenge. The findings in $LOOP_DIR/1-review.md were written by others; your job is to test each one against the code it cites. A finding is BROKEN if, for example: its quote is not at its file:line; it misreads the code; the path it describes cannot be reached; existing code or a test already covers it; the spec deliberately chose this (this ground never applies to a finding that cites a register entry or a more recent owner decision); its severity is overstated; its fix would add more complexity than it removes; or another lens already raised it. Check in the code and quote, with file:line, whatever you rely on. Do not add findings. Write one line per finding, '<id>: BROKEN <reason>' or '<id>: HOLDS <reason>', or 'Nothing to challenge.' if the list is empty. $CONTEXT" \
  "$LOOP_DIR/2-challenge.md" '(^[0-9A-Za-z_-]+: (BROKEN|HOLDS)|Nothing to challenge)'

# Stage 3.
session "TASK: defense and verdict. You speak for the reviewers who wrote $LOOP_DIR/1-review.md; the challenge to their findings is $LOOP_DIR/2-challenge.md. Reread the cited code and rule on every finding: KEPT (same or higher severity, with the evidence the challenge demanded) or CONCEDED (lowered or withdrawn, with the reason), quoting at file:line the code each ruling depends on. Do not add findings. Then list the findings that survive in the review's finding layout, ids unchanged, duplicates merged into one entry, and finish with the two lines 'COUNTS: BLOCK <n> FIX <n> SUGGEST <n>' and 'Verdict: <READY | READY-WITH-FIXES | REVISE>' as code-review's rule assigns it. $CONTEXT" \
  "$LOOP_DIR/3-final.md" '^Verdict: (READY|READY-WITH-FIXES|REVISE)$'

grep -E '^(COUNTS|Verdict):' "$LOOP_DIR/3-final.md"
