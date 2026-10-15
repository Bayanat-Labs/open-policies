#!/usr/bin/env python3
# Copyright 2026 Bayanat Labs
# SPDX-License-Identifier: Apache-2.0
"""Check that the public open-policies repository carries no internal material.

Bayanat Labs runs this check before every public commit of this repository. It scans every
text file and fails on any match in the categories below. Each category lists its regular
expressions in PATTERNS; the comments there say what each one is for.

Categories
  local-path         Paths on a personal machine or in a working directory.
  evidence-id        Identifiers and file layout of an evidence archive. A public reference
                     must be a URL a reader can open, not an archive ID.
  line-reference     Line numbers pointing into other documents.
  counsel            Accounts of exchanges with legal advisers. A public file cites a legal
                     position only by the ID of the recorded decision it rests on.
  money              Budgets, prices and rates: currency amounts in any form.
  calibration        Throughput or speed figures measured on Bayanat Labs hardware.
  personal-data      E-mail addresses (other than the public contact and example domains),
                     phone numbers, Saudi national ID and IBAN shapes.
  internal-marker    Markers that belong to drafts.
  brand              The brand name without "Labs". Always write "Bayanat Labs".
  extra-term         Optional extra terms given with --deny-list.

Extra terms
  --deny-list FILE (repeatable) adds optional extra terms: one literal per line, lines
  starting with "#" are comments, and a line starting with "case:" is matched with case; all
  other terms ignore case. A term that starts or ends with a letter or digit must stand as a
  whole word. A hit on an extra term is reported by position only.

Allowed matches
  ALLOW lists the few matches that are correct in context, each with its reason.

Usage
  python scripts/public_leak_check.py [ROOT] [--deny-list FILE ...] [--json OUT.json]
ROOT defaults to the repository root. Exit code 0 when there are no hits, 1 otherwise.
Standard library only.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.dirname(HERE)
SELF = os.path.relpath(os.path.abspath(__file__), DEFAULT_ROOT).replace(os.sep, "/")

SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "build", "dist", ".mypy_cache", ".ruff_cache"}
BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".gz", ".whl", ".parquet", ".pyc"}
# Bidirectional controls and joiners used in Arabic text. They are removed before matching, so
# they cannot split a term.
INVISIBLE = dict.fromkeys(map(ord, "\u200e\u200f\u2066\u2067\u2068\u2069\u202a\u202b\u202c\u202d\u202e\u200b\u200c\u200d\ufeff"))

# BEGIN PATTERNS
PATTERNS = [
    # local-path: a home directory on macOS or Linux, temporary and cache folders, a Windows profile.
    ("local-path", "home directory", r"/(?:Users|home)/[A-Za-z0-9._-]+"),
    ("local-path", "temporary folder", r"/private/(?:tmp|var)/|/var/folders/"),
    ("local-path", "windows profile", r"\b[A-Za-z]:\\\\?(?:Users|Documents and Settings)\\\\?"),
    # local-path: per-item work folders of a working directory.
    ("local-path", "internal workspace", r"\bwork/(?:[a-z]{2}\d{3}|_[a-z]+)\b"),
    # evidence-id: archive IDs and the archive's file layout.
    ("evidence-id", "archive ID", r"\bEV-[0-9a-f]{10}\b"),
    ("evidence-id", "archive layout", r"\b(?:text|html|pdf)/EV-|\bEVIDENCE\.jsonl\b"),
    # line-reference: "line 7", "lines 3-9", "L123", and the Arabic forms.
    ("line-reference", "line number", r"\blines? \d{1,5}(?:\s*[-\u2013]\s*\d{1,5})?\b"),
    # (an SVG path command such as "L10 20" is a coordinate pair, not a line reference)
    ("line-reference", "L-number", r"(?<![\w.-])L\d{2,5}\b(?![\s,]*-?\d)"),
    ("line-reference", "Arabic line number", r"(?:\u0627\u0644\u0623\u0633\u0637\u0631|\u0627\u0644\u0633\u0637\u0631|\u0623\u0633\u0637\u0631|\u0633\u0637\u0631)\s*\d"),
    # counsel: an exchange with counsel, or what counsel said.
    ("counsel", "counsel exchange", r"(?i)\bcounsel(?:'s)?\s+(?:pack|memo|e-?mail|letter|call|meeting|session|notes?|opinion|reply|response|cover|said|says|told|advised|advises|confirmed|thinks|view)\b"),
    ("counsel", "privilege", r"(?i)\bprivileged\b|attorney[- ]client|\bcover[ _-]note\b|\bagenda item\b"),
    ("counsel", "Arabic counsel exchange", r"(?:\u0645\u0630\u0643\u0631\u0629|\u0631\u0633\u0627\u0644\u0629|\u062c\u0644\u0633\u0629|\u0628\u0631\u064a\u062f) (?:\u0627\u0644)?\u0645\u0633\u062a\u0634\u0627\u0631"),
    # money: currency symbols or codes next to an amount.
    ("money", "currency amount", r"[$\u20ac\u00a3\uFDFC]\s?\d|\b(?:USD|SAR|EUR|AED|GBP)\s?\d|\d[\d,.]*\s?(?:USD|SAR|EUR|AED|GBP|dollars?|riyals?)\b"),
    ("money", "example rate", r"(?i)--rate\s+\d|\brate\b[^\n]{0,40}\be\.g\.\s*\d"),
    # calibration: speed figures (real-time factor, documents or characters per second, hardware runs).
    ("calibration", "real-time factor", r"\bRTF\b\s*(?:of|=|:|is)?\s*\d"),
    ("calibration", "throughput", r"\d[\d,.]*\s*(?:docs|documents|chars|characters|records)\s*(?:/|per)\s*s(?:ec(?:ond)?)?\b"),
    ("calibration", "hardware run", r"(?i)\bm3[ -]?pro\b[^\n]{0,60}\d+(?:\.\d+)?\s*(?:x|h|hours?|s|seconds?|minutes?)\b"),
    # personal-data: contact details and identifiers.
    ("personal-data", "e-mail address", r"[A-Za-z0-9._%+-]+@(?!bayanatlabs\.com\b|example\.(?:org|com|net)\b)[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}"),
    ("personal-data", "phone number", r"(?<![\w.])\+\d{1,3}[\s-]?\(?\d{1,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,4}\b"),
    # (a 10-digit file size such as "size: 1687094687" in the tooling lock is not an ID)
    ("personal-data", "Saudi ID or IBAN", r"(?<!size: )(?<![\w.-])[12]\d{9}(?![\w.-])|\bSA\d{2}[0-9A-Z]{20}\b"),
    # internal-marker: draft and internal-only labels.
    ("internal-marker", "internal label", r"\bINTERNAL\b|internal:(?:start|end)|(?i:\bdo not publish\b|\bnot (?:yet )?published\b|\bfor founder review\b)"),
    # brand: "Bayanat" must be followed by "Labs" ("Bayanat-Norm" is the name of a normalisation policy family).
    ("brand", "bare Bayanat", r"\bBayanat\b(?![ -](?:Labs|Norm))"),
]
# Exact matches that are correct in context: (path glob, pattern name, matched text, reason).
ALLOW = [
    ("policy/scripts/validate_policy.py", "internal label", "do not publish",
     "the validator rejects a public file whose banner still carries this marker"),
    ("manual/budget.py", "real-time factor", "RTF 0",
     "published Emilia-Pipe figure (arXiv:2501.15907), cited as a placeholder seed, not a Bayanat Labs measurement"),
]
# END PATTERNS
COMPILED = [(cat, name, re.compile(rx)) for cat, name, rx in PATTERNS]


def list_files(root: str) -> list[str]:
    """Tracked files when ROOT is a git checkout, else every file under ROOT."""
    if os.path.isdir(os.path.join(root, ".git")):
        try:
            out = subprocess.run(["git", "-C", root, "ls-files", "-z"], capture_output=True, check=True).stdout
            files = [f for f in out.decode("utf-8").split("\0") if f]
            if files:
                return sorted(files)
        except (OSError, subprocess.CalledProcessError):
            pass
    found = []
    for d, dirs, fs in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS and not x.endswith(".egg-info"))
        for fn in sorted(fs):
            found.append(os.path.relpath(os.path.join(d, fn), root).replace(os.sep, "/"))
    return found


def load_deny(paths: list[str]) -> list[tuple[str, re.Pattern]]:
    terms = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            for raw in f:
                t = raw.strip()
                if not t or t.startswith("#"):
                    continue
                flags = re.IGNORECASE
                if t.startswith("case:"):
                    t, flags = t[len("case:"):].strip(), 0
                left = r"(?<![A-Za-z0-9])" if t[0].isalnum() else ""
                right = r"(?![A-Za-z0-9])" if t[-1].isalnum() else ""
                terms.append((t, re.compile(left + re.escape(t) + right, flags)))
    return terms


def normalise(raw: str) -> tuple[str, list[int]]:
    """Remove invisible controls and collapse whitespace runs to one space; keep a map from each
    character of the result to its 1-based line number in the file."""
    out, where, line, prev_space = [], [], 1, False
    for ch in raw:
        if ch == "\n":
            line += 1
        if ord(ch) in INVISIBLE:
            continue
        if ch.isspace():
            if not prev_space:
                out.append(" ")
                where.append(line - 1 if ch == "\n" else line)
            prev_space = True
            continue
        out.append(ch)
        where.append(line)
        prev_space = False
    return "".join(out), where


def pattern_block(raw: str) -> tuple[int, int]:
    """Line span of this file's own pattern table, which is exempt from the regex categories."""
    lines = raw.splitlines()
    try:
        return lines.index("# BEGIN PATTERNS") + 1, lines.index("# END PATTERNS") + 1
    except ValueError:
        return 0, -1


def allowed(rel: str, name: str, match: str) -> bool:
    return any(fnmatch.fnmatch(rel, g) and name == n and match.startswith(m) for g, n, m, _ in ALLOW)


def scan(root: str, deny: list[tuple[str, re.Pattern]]) -> tuple[int, list[dict]]:
    hits, scanned = [], 0
    for rel in list_files(root):
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            continue
        scanned += 1
        if os.path.splitext(rel)[1].lower() in BINARY_EXT:
            hits.append({"file": rel, "line": 0, "category": "binary", "pattern": "binary file", "match": rel})
            continue
        try:
            with open(path, encoding="utf-8") as f:
                raw = f.read()
        except UnicodeDecodeError:
            hits.append({"file": rel, "line": 0, "category": "binary", "pattern": "not UTF-8 text", "match": rel})
            continue
        text, where = normalise(raw)
        lo, hi = pattern_block(raw) if rel == SELF else (0, -1)
        for cat, name, rx in COMPILED:
            for m in rx.finditer(text):
                ln = where[m.start()] if m.start() < len(where) else 0
                if lo <= ln <= hi or allowed(rel, name, m.group(0)):
                    continue
                hits.append({"file": rel, "line": ln, "category": cat, "pattern": name, "match": m.group(0)})
        for term, rx in deny:
            for m in rx.finditer(text):
                ln = where[m.start()] if m.start() < len(where) else 0
                hits.append({"file": rel, "line": ln, "category": "extra-term", "pattern": "extra term",
                             "match": m.group(0)})
    return scanned, hits


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("root", nargs="?", default=DEFAULT_ROOT)
    ap.add_argument("--deny-list", action="append", default=[], metavar="FILE",
                    help="file of optional extra terms that must not appear (repeatable)")
    ap.add_argument("--json", metavar="OUT.json", help="write the result as JSON")
    a = ap.parse_args(argv)
    deny = load_deny(a.deny_list)
    scanned, hits = scan(os.path.abspath(a.root), deny)
    for h in hits:
        shown = "<extra term>" if h["category"] == "extra-term" else repr(h["match"])
        print(f"{h['file']}:{h['line']}: [{h['category']}: {h['pattern']}] {shown}")
    by_cat: dict[str, int] = {}
    for h in hits:
        by_cat[h["category"]] = by_cat.get(h["category"], 0) + 1
    print(f"public leak check: {scanned} files scanned, {len(PATTERNS)} patterns in {len({c for c, _, _ in PATTERNS})} "
          f"categories, {len(deny)} extra terms, {len(hits)} hits" + (f" {by_cat}" if by_cat else ""))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            # Extra terms are reported by position only, never by text.
            safe = [dict(h, match="<extra term>") if h["category"] == "extra-term" else h for h in hits]
            json.dump({"files_scanned": scanned, "patterns": len(PATTERNS), "extra_terms": len(deny),
                       "hits": safe}, f, indent=1, ensure_ascii=False)
    return 0 if not hits else 1


if __name__ == "__main__":
    sys.exit(main())
