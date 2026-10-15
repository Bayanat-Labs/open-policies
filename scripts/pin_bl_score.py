#!/usr/bin/env python3
"""Pin the bl-score scorer by file hash, not by its version string.

bl-score's scoring (legal_gate.score_overrides) and its date handling changed while the
version string stayed 0.1.0, so a version number cannot tell two scorers apart. The pin is a tree
hash over the files that decide a score: src/bl_score/*.py and src/bl_score/data/* (no tests,
README or caches). Tree hash = SHA-256 of the sorted lines "<relative path>\\t<sha256 of file>\\n".

Usage
  pin_bl_score.py BL_SCORE_DIR                      print the tree hash and per-file hashes (JSON)
  pin_bl_score.py BL_SCORE_DIR --write PIN.json     write the pin file
  pin_bl_score.py BL_SCORE_DIR --check PIN.json     exit 0 if BL_SCORE_DIR matches the pin, 1 if not

Reads files as bytes only; never imports or runs the scorer. Apache-2.0. Bayanat Labs operating manual.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def scorer_files(root: Path) -> list[Path]:
    pkg = root / "src" / "bl_score"
    if not pkg.is_dir():
        raise SystemExit(f"not a bl-score checkout (no src/bl_score): {root}")
    files = [p for p in pkg.glob("*.py")] + [p for p in (pkg / "data").glob("*") if p.is_file()]
    return sorted(files, key=lambda p: p.relative_to(root).as_posix())


def tree(root: Path) -> dict:
    rows = []
    for p in scorer_files(root):
        rows.append({"path": p.relative_to(root).as_posix(), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    blob = "".join(f"{r['path']}\t{r['sha256']}\n" for r in rows).encode("utf-8")
    version = None
    init = root / "src" / "bl_score" / "__init__.py"
    for line in init.read_text(encoding="utf-8").splitlines():
        if line.startswith("__version__"):
            version = line.split("=", 1)[1].strip().strip("\"'")
    return {"tool": "bl-score", "version_string": version,
            "tree_sha256": hashlib.sha256(blob).hexdigest(), "files": rows,
            "method": "sha256 over sorted '<path>\\t<sha256>\\n' lines for src/bl_score/*.py and src/bl_score/data/*"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("bl_score_dir")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--write", metavar="PIN.json")
    g.add_argument("--check", metavar="PIN.json")
    a = ap.parse_args(argv)
    t = tree(Path(a.bl_score_dir))
    if a.write:
        Path(a.write).write_text(json.dumps(t, indent=2) + "\n", encoding="utf-8")
        print(t["tree_sha256"])
        return 0
    if a.check:
        pin = json.loads(Path(a.check).read_text(encoding="utf-8"))
        if pin["tree_sha256"] == t["tree_sha256"]:
            print(f"OK: bl-score matches the pin {t['tree_sha256']}")
            return 0
        pinned = {r["path"]: r["sha256"] for r in pin["files"]}
        now = {r["path"]: r["sha256"] for r in t["files"]}
        changed = sorted(k for k in set(pinned) | set(now) if pinned.get(k) != now.get(k))
        print(f"DRIFT: bl-score tree {t['tree_sha256']} != pin {pin['tree_sha256']}; changed: {changed}", file=sys.stderr)
        return 1
    print(json.dumps(t, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
