#!/usr/bin/env python3
"""Size and economy measurements for a directory of Agent Skills.

For every skill this reports:

* how long the frontmatter ``description`` is — hosts keep every skill's
  description loaded, so each character is paid for in every session;
* the size of ``SKILL.md`` (read in full whenever the skill is invoked):
  line count, body word count, and a rough token estimate;
* the size of each ``references/**/*.md`` file (read in full by any step that
  opens it), and whether a long one starts with a contents list;
* how much body text it repeats from exactly one other skill's ``SKILL.md``
  (a passage two skills both carry should live in one of them; wording that
  three or more skills share is treated as a family convention and ignored);
* the strongest description overlap with a skill its description never
  mentions (a host picking between the two has no way to tell them apart);
* long body sections headed by a mode, setup step, or host name — likely
  material for a reference file that only that path reads.

Counting rules: words split on whitespace (as ``wc -w``), lines count
newlines (as ``wc -l``), tokens ~= words * 1.33, and the body is everything
after the frontmatter. Repeated text is found by matching 12-word shingles and
only counts once a contiguous run reaches PASSAGE_WORDS, so treat it as an
estimate.

Printed output: a per-skill Markdown table, a table of long branch sections
if there are any, a table of reference files, and then one line for every
limit exceeded —

    OVER <skill> <metric> <value> > <limit>
    PAGE <skill>/<reference> <lines> lines > <limit>
    CANDIDATE <skill> branch-section "<heading>" <words> > <limit>

— or the single line ``no limits crossed``. Exits 0; with ``--strict`` exits
1 if any OVER or PAGE line was printed. Needs only the Python 3 standard
library.

Invocation: measure_skills.py [SKILLS_DIR] [--skill NAME ...] [--strict]
When SKILLS_DIR is omitted, the parent directory of this skill is used.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

# Thresholds. The Agent Skills spec allows a `description` of up to 1,024
# characters and advises keeping SKILL.md below 500 lines and its body near
# 5,000 tokens; these values stay under the spec to leave room.
DESC_CHARS = 800
SKILL_LINES = 500
BODY_WORDS = 3500
SHARED_WORDS = 150       # words repeated from a single other skill
DESC_OVERLAP = 0.35      # Jaccard similarity of description content words
REF_PAGE_LINES = 2000    # past this, a reference cannot be read in one go
REF_TOC_LINES = 100      # past this, a reference should open with a contents list
BRANCH_WORDS = 300       # a single-path section longer than this should move out
SHINGLE = 12
PASSAGE_WORDS = 40
TOKENS_PER_WORD = 1.33

BRANCH_HEADING = re.compile(
    r"\b(hosts?|codex|claude code|cursor|gemini|setup|set-up|"
    r"install(ation)?|bootstrap|first[- ]run|modes?)\b",
    re.IGNORECASE,
)
FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
WORD = re.compile(r"[0-9a-z]+")
HEADING = re.compile(r"(#{2,6})\s+(.*)")
CONTENTS_HEADING = re.compile(r"^#+\s*(table of )?contents\b", re.IGNORECASE | re.MULTILINE)

# Function words dropped before comparing descriptions (kept alphabetical).
STOPWORDS = frozenset("""
    a after also an and any are as at be before by do does each every for from
    how if in into is it its no not of on one only or run runs skill skills
    than that the then these this those to two use used user users uses using
    via what when which who with you your
""".split())


@dataclass
class Skill:
    name: str
    folder: Path
    line_count: int
    description: str
    body: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def split_frontmatter(text: str) -> tuple[str, str]:
    found = FRONTMATTER.match(text)
    return (found.group(1), text[found.end():]) if found else ("", text)


def parse_description(frontmatter: str) -> str:
    """Flatten the `description` field to one line, whatever YAML style it uses."""
    rows = frontmatter.splitlines()
    for index, row in enumerate(rows):
        if not row.startswith("description:"):
            continue
        parts = [row.split(":", 1)[1].strip()]
        for follow in rows[index + 1:]:
            if follow and not follow[0].isspace():
                break
            parts.append(follow.strip())
        value = " ".join(p for p in parts if p)
        value = re.sub(r"^[|>][-+0-9]*\s*", "", value)  # block-scalar indicator
        if len(value) > 1 and value[0] in "'\"" and value[-1] == value[0]:
            quote, value = value[0], value[1:-1]
            value = value.replace("''", "'") if quote == "'" else value.replace('\\"', '"')
        return " ".join(value.split())
    return ""


def words_of(text: str) -> list[str]:
    return WORD.findall(text.lower())


def windows(words: list[str]) -> list[tuple[str, ...]]:
    """Every run of SHINGLE consecutive words, in order."""
    return [tuple(words[start:start + SHINGLE]) for start in range(len(words) - SHINGLE + 1)]


def long_run_total(positions: set[int]) -> int:
    """How many positions sit inside a consecutive run of PASSAGE_WORDS or more."""
    total, streak, last = 0, 0, None
    for pos in sorted(positions):
        streak = streak + 1 if last is not None and pos == last + 1 else 1
        if streak == PASSAGE_WORDS:
            total += PASSAGE_WORDS
        elif streak > PASSAGE_WORDS:
            total += 1
        last = pos
    return total


def body_sections(body: str) -> list[tuple[str, int]]:
    """Pair each H2-H6 heading (code fences skipped) with the words under it.

    A section ends where a heading at its own level or shallower begins.
    """
    rows = body.splitlines()
    marks: list[tuple[int, int, str]] = []
    fenced = False
    for index, row in enumerate(rows):
        if row.lstrip().startswith("```"):
            fenced = not fenced
            continue
        hit = None if fenced else HEADING.match(row)
        if hit:
            marks.append((index, len(hit.group(1)), hit.group(2).strip()))
    sections = []
    for pos, (first, depth, title) in enumerate(marks):
        stop = next((idx for idx, d, _ in marks[pos + 1:] if d <= depth), len(rows))
        sections.append((title, sum(len(row.split()) for row in rows[first + 1:stop])))
    return sections


def has_contents_list(text: str) -> bool:
    top = "\n".join(text.splitlines()[:40])
    return bool(CONTENTS_HEADING.search(top)) or top.count("](#") >= 3


def load_skills(skills_dir: Path) -> dict[str, Skill]:
    found: dict[str, Skill] = {}
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        text = read_text(skill_md)
        frontmatter, body = split_frontmatter(text)
        name = skill_md.parent.name
        found[name] = Skill(name, skill_md.parent, text.count("\n"), parse_description(frontmatter), body)
    return found


def restated_passage(name: str, body_words: dict[str, list[str]],
                     holders: dict[tuple[str, ...], set[str]]) -> tuple[str, int]:
    """The single other skill this one repeats most text from, and how many words."""
    shared_at: dict[str, set[int]] = defaultdict(set)
    for start, shingle in enumerate(windows(body_words[name])):
        if len(holders[shingle]) == 2:
            (partner,) = holders[shingle] - {name}
            shared_at[partner].update(range(start, start + SHINGLE))
    scored = [(partner, long_run_total(spots)) for partner, spots in shared_at.items()]
    return max(scored, key=lambda pair: pair[1], default=("", 0))


def closest_unnamed(skill: Skill, content: dict[str, set[str]]) -> tuple[str, float]:
    """The most similar description among skills this description does not mention."""
    mine = content[skill.name]
    best, score = "", 0.0
    for other, theirs in content.items():
        if other == skill.name or not mine or not theirs:
            continue
        if re.search(rf"(?<![\w-]){re.escape(other)}(?![\w-])", skill.description):
            continue
        similarity = len(mine & theirs) / len(mine | theirs)
        if similarity > score:
            best, score = other, similarity
    return best, score


def measure(skills_dir: Path, selected: list[str]) -> tuple[list[str], list[str]]:
    """Build the report tables and the list of crossed limits."""
    skills = load_skills(skills_dir)
    if not skills:
        raise SystemExit(f"found no */SKILL.md in {skills_dir}")
    unknown = [n for n in selected if n not in skills]
    if unknown:
        raise SystemExit(f"unknown skill(s) in {skills_dir}: {', '.join(unknown)}")

    body_words = {name: words_of(s.body) for name, s in skills.items()}
    holders: dict[tuple[str, ...], set[str]] = defaultdict(set)
    for name, toks in body_words.items():
        for shingle in windows(toks):
            holders[shingle].add(name)
    content = {name: set(words_of(s.description)) - STOPWORDS for name, s in skills.items()}

    summary = [
        "| skill | description chars | SKILL.md lines | body words | est. body tokens | references "
        "| words repeated from a single other skill | closest description not named (Jaccard) |",
        "|" + "---|" * 8,
    ]
    branch_rows: list[str] = []
    ref_rows: list[str] = []
    crossed: list[str] = []

    for name in selected or list(skills):
        skill = skills[name]
        partner, shared = restated_passage(name, body_words, holders)
        best, score = closest_unnamed(skill, content)

        refs = sorted((skill.folder / "references").glob("**/*.md"))
        for ref in refs:
            text = read_text(ref)
            label = f"{name}/{ref.relative_to(skill.folder).as_posix()}"
            n_words, n_lines = len(text.split()), text.count("\n")
            if n_lines <= REF_TOC_LINES:
                toc = "-"
            else:
                toc = "yes" if has_contents_list(text) else "no"
            ref_rows.append(f"| {label} | {n_words} | {round(n_words * TOKENS_PER_WORD)} | {n_lines} | {toc} |")
            if n_lines > REF_PAGE_LINES:
                crossed.append(f"PAGE {label} {n_lines} lines > {REF_PAGE_LINES}")

        n_body = len(skill.body.split())
        shared_cell = f"{shared} {partner}" if shared else f"{shared}"
        summary.append(
            f"| {name} | {len(skill.description)} | {skill.line_count} | {n_body} "
            f"| {round(n_body * TOKENS_PER_WORD)} | {len(refs)} | {shared_cell} | {best} {score:.2f} |"
        )

        for title, n_words in body_sections(skill.body):
            if n_words > BRANCH_WORDS and BRANCH_HEADING.search(title):
                branch_rows.append(f"| {name} | {title} | {n_words} |")
                crossed.append(f'CANDIDATE {name} branch-section "{title}" {n_words} > {BRANCH_WORDS}')

        checks = [
            ("desc-chars", len(skill.description), DESC_CHARS, ""),
            ("skill-lines", skill.line_count, SKILL_LINES, ""),
            ("body-words", n_body, BODY_WORDS, ""),
            ("shared-words", shared, SHARED_WORDS, f" (with {partner})"),
        ]
        crossed += [f"OVER {name} {metric} {value} > {limit}{note}"
                    for metric, value, limit, note in checks if value > limit]
        if score > DESC_OVERLAP:
            crossed.append(f"OVER {name} description-overlap {score:.2f} > {DESC_OVERLAP} (with {best})")

    if branch_rows:
        summary += ["", "| skill | long section headed by a mode, setup step or host | words |",
                    "|---|---|---|", *branch_rows]
    if ref_rows:
        summary += ["", f"| reference file | words | est. tokens | lines | has contents (if over {REF_TOC_LINES} lines) |",
                    "|---|---|---|---|---|", *ref_rows]
    return summary, crossed


def main(argv: list[str] | None = None) -> int:
    default_dir = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Report size and economy measurements for Agent Skills.")
    parser.add_argument("skills_dir", nargs="?", type=Path, default=default_dir,
                        help=f"folder whose subfolders hold SKILL.md files (default: {default_dir})")
    parser.add_argument("--skill", action="append", default=[], metavar="NAME",
                        help="report on this skill only (repeat for more); every skill is still compared")
    parser.add_argument("--strict", action="store_true",
                        help="return exit status 1 if an OVER or PAGE line is printed")
    args = parser.parse_args(argv)

    summary, crossed = measure(args.skills_dir, args.skill)
    print("\n".join(summary))
    print()
    print("\n".join(crossed) if crossed else "no limits crossed")
    failed = any(line.startswith(("OVER ", "PAGE ")) for line in crossed)
    return 1 if args.strict and failed else 0


if __name__ == "__main__":
    sys.exit(main())
