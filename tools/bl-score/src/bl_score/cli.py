"""Command line: bl-score MEMO.yaml [MEMO.yaml ...]

Prints JSON: one object for one memo, a list for several memos or for a file that
holds a YAML list of memos. Exit codes: 0 scored, 2 a memo or rubric is invalid,
1 a file could not be read.
"""
from __future__ import annotations

import argparse
import json
import sys

import yaml

from . import __version__
from .scoring import CRITERIA, MemoError, RubricError, load_rubric, memo_schema, output_schema, rank, score_memo


def _parse_weights(text: str) -> dict[str, float]:
    out = {}
    for part in text.split(","):
        if "=" not in part:
            raise RubricError(f"bad --weights item {part!r}; use name=value, e.g. impact=30")
        k, v = part.split("=", 1)
        out[k.strip()] = float(v)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="bl-score",
        description="Score Bayanat Labs scoping memos: weighted score (0-100), legal gate verdict, release-tier cap and suggested priority.",
        epilog="Memo format: see README.md or run 'bl-score --print-schema memo'.")
    ap.add_argument("memos", nargs="*", help="memo YAML file(s); '-' reads standard input")
    ap.add_argument("--rubric", help="path to a rubric.yaml (default: the copy shipped with this version)")
    ap.add_argument("--weights", help="override weights, e.g. impact=40,claim_strength=20,ease=20,legal_cleanliness=10,commercial_pull=10 (must sum to 100)")
    ap.add_argument("--rank", action="store_true", help="sort results: excluded last, then score, then seo_demand")
    ap.add_argument("--check", action="store_true", help="validate memos only; print nothing on success")
    ap.add_argument("--compact", action="store_true", help="print JSON on one line")
    ap.add_argument("--print-schema", choices=["memo", "output"], help="print a JSON Schema and exit")
    ap.add_argument("--version", action="version", version=f"bl-score {__version__}")
    a = ap.parse_args(argv)

    if a.print_schema:
        print(json.dumps(memo_schema() if a.print_schema == "memo" else output_schema(), indent=2))
        return 0
    if not a.memos:
        ap.print_usage(sys.stderr)
        print("bl-score: error: give at least one memo file", file=sys.stderr)
        return 1
    try:
        rubric = load_rubric(a.rubric)
        if a.weights:
            rubric = rubric.with_weights(_parse_weights(a.weights))
    except (RubricError, OSError, ValueError) as e:
        print(f"bl-score: {e}", file=sys.stderr)
        return 2 if isinstance(e, RubricError) else 1

    results, failed, many = [], False, len(a.memos) > 1
    for path in a.memos:
        try:
            text = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
        except OSError as e:
            print(f"bl-score: cannot read {path}: {e.strerror}", file=sys.stderr)
            return 1
        try:
            doc = yaml.safe_load(text)
        except yaml.YAMLError as e:
            print(f"{path}: not valid YAML: {e}", file=sys.stderr)
            failed = True
            continue
        docs = doc if isinstance(doc, list) else [doc]
        many = many or isinstance(doc, list)
        for i, m in enumerate(docs):
            src = path if not isinstance(doc, list) else f"{path}[{i}]"
            try:
                results.append(score_memo(m, rubric, source=src))
            except MemoError as e:
                print(str(e), file=sys.stderr)
                failed = True
    if failed:
        return 2
    if a.check:
        return 0
    if a.rank:
        results = rank(results)
    out = results if many else results[0]
    print(json.dumps(out, ensure_ascii=False, indent=None if a.compact else 2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
