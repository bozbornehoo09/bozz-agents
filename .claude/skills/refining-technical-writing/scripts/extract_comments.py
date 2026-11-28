#!/usr/bin/env python3
"""Collect the code comments that a change introduces, so references/code-comments.md can review
them. Needs only git and the Python standard library.

Forms:
  extract_comments.py REPO               the HEAD commit (a merge is read against its first parent)
  extract_comments.py REPO COMMIT        one commit
  extract_comments.py REPO BASE..TIP     everything the range adds
  extract_comments.py REPO --staged      what the index adds on top of HEAD (use after `git add`)
  --out FILE                             also save the comment blocks as Markdown for check_prose.py:
                                         a `## <path>:<start>-<end>` section per block, markers gone

Each added comment line that leans on something a future reader cannot open (a design document,
an ADR, an issue or ticket, a pull request, by id or by link) or that writes a person into the code
(`TODO(<name>)`, `@author`) is printed as `<path>:<line>: <kind>: <text>`. A summary line closes the
output. Rule C1 of code-comments.md asks for the reason in words instead.

Exit codes, which other skills depend on:
  0  nothing flagged
  1  one or more lines flagged (all listed on stdout)
  2  git failed or the arguments were wrong (message on stderr)

A line is a comment because of where it sits in its file, not because of its shape: every changed
file is scanned whole at its new version. C-style files (Java, Kotlin, Scala, Go, Rust, C, C++, C#,
Swift, TypeScript, JavaScript) use `//` and `/* */`; Python, Ruby, shell, YAML and TOML use `#`.
An end-of-line marker counts only outside quotes, so a URL in a string is safe. Python
triple-quoted strings and shell heredocs are skipped. Not handled: a `//` line inside a multi-line
string literal of a C-style language. Docstrings and other file types are not read.
"""

import argparse
import re
import subprocess
import sys
from collections import namedtuple
from pathlib import Path

C_LIKE = frozenset(
    "java kt kts scala go rs c h cc cpp hpp cs swift ts tsx js jsx mjs cjs".split())
SHELLS = frozenset(("sh", "bash", "zsh"))
HASH_LIKE = SHELLS | frozenset(("py", "rb", "yml", "yaml", "toml"))

Comment = namedtuple("Comment", "text trailing")

# Shapes of references a reader cannot follow years later, checked in this order.
_CITATION_SHAPES = (
    ("design doc", r"\b(?:design doc|RFC doc|[HL]LD|PRD)s?\b|\bAppendix\s+[A-Z0-9]\b|§", re.I),
    ("doc link", r"(?:docs\.google\.com|notion\.so|sharepoint\.com)/|\.atlassian\.net/wiki"
                 r"|/confluence/", 0),
    ("ADR", r"\bADR[ -]?\d+", 0),
    ("pull request", r"\b(?:PR|MR)\s*#?\d+\b|\bpull request\s*#?\d+|/merge_requests/\d+"
                     r"|github\.com/[^\s/]+/[^\s/]+/pull/", re.I),
    ("issue", r"\b(?:ticket|issue|bug)\s*#\d+|/-/issues/\d+|\.atlassian\.net/browse/"
              r"|github\.com/[^\s/]+/[^\s/]+/issues/", re.I),
    # A person written into the code. TODO or FIXME on its own is fine.
    ("name", r"@author\b|\b(?:FIXME|TODO|XXX)\s*\(\s*@?[A-Za-z][\w.-]*\s*\)", 0),
)
CITATIONS = [(kind, re.compile(pattern, flags)) for kind, pattern, flags in _CITATION_SHAPES]

# A tracker-style key such as OPS-12. Public standards and registries are looked up by anyone.
KEYLIKE = re.compile(r"\b([A-Z][A-Z0-9]+)-\d+\b")
OPEN_STANDARDS = frozenset("""
    AES AL CVE CWE ECMA ES GMT HMAC HTTP HTTPS IEEE IPV ISO JDK JSR MPEG PEP RFC RSA SHA SSL TLS
    UTC UTF""".split())

HUNK = re.compile(r"^@@ -\S+ \+(\d+)")
JAVADOC_INLINE = re.compile(r"\{@(?:linkplain|link|code|literal|value)\s+([^{}]*)\}")
HEREDOC = re.compile(r"<<-?\s*[\"']?([A-Za-z_]\w*)")
QUOTES = "'\"`"


class GitError(Exception):
    pass


def family(path):
    ext = Path(path).suffix[1:]
    if ext in C_LIKE:
        return "c"
    return "hash" if ext in HASH_LIKE else None


# --- Talking to git ---------------------------------------------------------------------------

def call_git(repo, args):
    """stdout of one git command. Bytes that are not UTF-8 become U+FFFD; callers split on "\\n"
    only, so a carriage return or form feed in a file cannot throw the numbering off."""
    proc = subprocess.run(["git", "-C", str(repo), "-c", "core.quotepath=off"] + list(args),
                          capture_output=True)
    if proc.returncode != 0:
        why = proc.stderr.decode("utf-8", "replace").strip()
        raise GitError(why or "git %s failed with status %d" % (args[0], proc.returncode))
    return proc.stdout.decode("utf-8", "replace")


class Change:
    """The change under review: the index, a range, or a single commit."""

    # Fixed diff settings, so a user's diff config (colors, prefixes, drivers) cannot leak in.
    PINNED = ["-U0", "--no-color", "--no-ext-diff", "--no-textconv",
              "--src-prefix=a/", "--dst-prefix=b/"]

    def __init__(self, repo, rev, staged):
        self.repo, self.rev, self.staged = repo, rev, staged
        self.is_range = not staged and ".." in rev

    def diff(self):
        if self.staged:
            return call_git(self.repo, ["diff", "--cached"] + self.PINNED + ["--"])
        if self.is_range:
            return call_git(self.repo, ["diff"] + self.PINNED + [self.rev, "--"])
        return call_git(self.repo, ["show", "--format=", "--diff-merges=first-parent"]
                        + self.PINNED + [self.rev, "--"])

    def new_text(self, path):
        if self.staged:
            spec = ":" + path
        else:
            tip = self.rev.split("..", 1)[1].lstrip(".") if self.is_range else self.rev
            spec = (tip or "HEAD") + ":" + path
        return call_git(self.repo, ["show", spec])

    def label(self):
        if self.staged:
            return "the staged change"
        if self.is_range:
            return self.rev
        return call_git(self.repo, ["rev-parse", "--short", self.rev]).strip()


def added_lines(diff_text):
    """Map each file the change keeps to the new-side numbers of the lines it adds."""
    result = {}
    current = None
    in_header = False
    lineno = 0
    for row in diff_text.split("\n"):
        if row.startswith("diff --git "):
            current, in_header = None, True
            continue
        if in_header and row.startswith("+++ "):
            # git wraps odd paths in quotes and ends a path that has a space with a tab.
            name = row[4:].rstrip("\t").strip('"')
            current = name[2:] if name.startswith("b/") else None  # /dev/null: file deleted
            continue
        if row.startswith("@@"):
            in_header = False
            found = HUNK.match(row)
            lineno = int(found.group(1)) if found else 0
            continue
        if current and not in_header and row.startswith("+"):
            result.setdefault(current, []).append(lineno)
            lineno += 1
    return result


# --- Finding comments in a file ---------------------------------------------------------------

def marker_outside_quotes(line, marker):
    """Index of the first `marker` that follows whitespace and sits outside quotes, else -1."""
    open_quote = None
    pos, size = 0, len(line)
    while pos < size:
        char = line[pos]
        if open_quote is not None:
            if char == "\\":
                pos += 1
            elif char == open_quote:
                open_quote = None
        elif char in QUOTES:
            open_quote = char
        elif pos and line[pos - 1].isspace() and line.startswith(marker, pos):
            return pos
        pos += 1
    return -1


def scan_c_like(lines):
    found = {}
    inside_block = False
    for lineno, line in enumerate(lines, 1):
        text = line.strip()
        if inside_block or text.startswith("/*"):
            rest = text if inside_block else text[2:]
            inside_block = "*/" not in rest
            body = rest.partition("*/")[0].strip().lstrip("*").strip()
            found[lineno] = Comment(body, False)
        elif text.startswith("//"):
            found[lineno] = Comment(text.lstrip("/").strip(), False)
        else:
            cut = marker_outside_quotes(line, "//")
            if cut != -1:
                found[lineno] = Comment(line[cut:].lstrip("/").strip(), True)
    return found


def heredoc_word(code):
    """The terminator a shell line opens a heredoc with, or None (`<<<` is a here-string)."""
    cut = marker_outside_quotes(code, "<<")
    if cut == -1 or code[cut:cut + 3] == "<<<":
        return None
    match = HEREDOC.match(code, cut)
    return match.group(1) if match else None


def scan_hash_like(lines, path):
    ext = Path(path).suffix[1:]
    python, shell = ext == "py", ext in SHELLS
    found = {}
    open_triple = None
    heredoc_end = None
    for lineno, line in enumerate(lines, 1):
        text = line.strip()
        if heredoc_end is not None:
            if text == heredoc_end:
                heredoc_end = None
            continue
        if open_triple is not None:
            if open_triple in line:
                open_triple = None
            continue
        if text.startswith("#"):
            shebang = lineno == 1 and text.startswith("#!")
            if not shebang:
                found[lineno] = Comment(text.lstrip("#").strip(), False)
            continue
        cut = marker_outside_quotes(line, "#")
        code = line
        if cut != -1:
            found[lineno] = Comment(line[cut:].lstrip("#").strip(), True)
            code = line[:cut]
        if python:
            open_triple = None
            for delim in ('"""', "'''"):
                if code.count(delim) % 2 == 1:
                    open_triple = delim
                    break
        elif shell:
            heredoc_end = heredoc_word(code)
    return found


def comments_in(path, text):
    lines = text.split("\n")
    return scan_c_like(lines) if family(path) == "c" else scan_hash_like(lines, path)


# --- Blocks -----------------------------------------------------------------------------------

class Block:
    def __init__(self, path, first, trailing):
        self.path, self.first, self.last, self.trailing = path, first, first, trailing
        self.rows = []

    def add(self, lineno, text):
        self.rows.append((lineno, text))
        self.last = lineno

    def has_text(self):
        return any(text for _, text in self.rows)


def blocks_for(change):
    """Added comment lines in blocks. Neighbouring full-line comments in a file join one block;
    an end-of-line comment always stands alone; blocks without any text are left out."""
    out = []
    for path, numbers in added_lines(change.diff()).items():
        if family(path) is None:
            continue
        comments = comments_in(path, change.new_text(path))
        block = None
        for lineno in numbers:
            comment = comments.get(lineno)
            if comment is None:
                block = None
                continue
            contiguous = block is not None and block.last == lineno - 1
            if comment.trailing or not contiguous:
                block = Block(path, lineno, comment.trailing)
                out.append(block)
            block.add(lineno, comment.text)
            if comment.trailing:
                block = None
    return [b for b in out if b.has_text()]


def citation_kind(text):
    """What a comment line points at that a reader cannot open ("name" for a person), or None."""
    for kind, pattern in CITATIONS:
        if pattern.search(text):
            return kind
    for key in KEYLIKE.finditer(text):
        if key.group(1) not in OPEN_STANDARDS:
            return "issue"
    return None


# --- Markdown extract -------------------------------------------------------------------------

def as_paragraphs(rows):
    """Text of one block for check_prose.py. Inline doc tags become code spans, which the checker
    skips. A blank line, `<p>` or an `@tag` line starts a paragraph, so Vale does not read a run
    of tags as one sentence."""
    paragraphs = []
    for _, raw in rows:
        line = JAVADOC_INLINE.sub(lambda m: "`" + m.group(1).strip() + "`", raw)
        breaks = line == "" or line == "<p>" or line.startswith("@")
        if breaks and paragraphs and paragraphs[-1]:
            paragraphs.append("")
        if line and line != "<p>":
            paragraphs.append(line)
    while paragraphs and not paragraphs[-1]:
        paragraphs.pop()
    return "\n".join(paragraphs)


def extract_markdown(blocks, heading):
    parts = ["# Comments added by %s\n" % heading]
    for b in blocks:
        tag = " (trailing)" if b.trailing else ""
        parts.append("## %s:%d-%d%s\n\n%s\n" % (b.path, b.first, b.last, tag,
                                                  as_paragraphs(b.rows)))
    return "\n".join(parts)


# --- Entry point ------------------------------------------------------------------------------

def build_parser():
    cli = argparse.ArgumentParser(
        prog="extract_comments.py",
        description="List the comments a git change adds and flag lines that cite documents, "
                    "tickets or people (rule C1). Exit 0 clean, 1 flagged, 2 error.")
    cli.add_argument("repo", type=Path, help="git repository to read")
    cli.add_argument("rev", nargs="?", default="HEAD",
                     help="commit or BASE..TIP range (HEAD when omitted)")
    cli.add_argument("--staged", action="store_true", help="read the index against HEAD")
    cli.add_argument("--out", type=Path, metavar="FILE", help="Markdown file for the blocks")
    return cli


def run(argv=None):
    cli = build_parser()
    opts = cli.parse_args(argv)
    if opts.staged and opts.rev != "HEAD":
        cli.error("--staged already means the index against HEAD; drop the revision")
    change = Change(opts.repo, opts.rev, opts.staged)
    try:
        blocks = blocks_for(change)
        label = change.label()
    except GitError as err:
        sys.stderr.write("extract_comments: %s\n" % err)
        return 2
    if opts.out is not None:
        heading = "%s in %s" % (label, opts.repo.resolve().name)
        opts.out.write_text(extract_markdown(blocks, heading))
    hits = 0
    for b in blocks:
        for lineno, text in b.rows:
            kind = citation_kind(text)
            if kind:
                hits += 1
                print("%s:%d: %s: %s" % (b.path, lineno, kind, text))
    print("extract_comments: %d comment blocks; %d lines cite a document or name a person"
          % (len(blocks), hits))
    return 1 if hits else 0


if __name__ == "__main__":
    raise SystemExit(run())
