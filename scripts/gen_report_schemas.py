#!/usr/bin/env python3
"""Generate one JSON Schema per report file that the gate checks read.

Usage
  gen_report_schemas.py [--stages manual/stages.yaml] [--dod manual/dod.yaml]
                        [--memo-schema manual/schemas/scoping_memo_record.schema.json]
                        [--out manual/schemas/reports] [--check]

For every `metric` and `signoff` check in stages.yaml and dod.yaml, the field it reads is declared in
the schema of its file, with a type taken from the check:
  is_true / is_false              boolean
  >=, <=, >, < and value_field    number
  == / != / in / not_in           the type of the value (or of the memo field for value_ref)
  not_null / exists               any type (the key may be null until the gate runs)
  signoff                         object with name, date, verdict and optional role
A field is required when a stage check reads it without an applies_if condition and with an op other than
not_null or exists (absence of those already fails the gate). Extra keys are allowed (notes, _na blocks).
Numbers and booleans can therefore never be replaced by a string such as "n/a": a check is n/a only
through a memo condition, never because a report says so.
Files that have their own schema (memo, score block, ledgers, digest rows) are skipped.

--check compares the generated schemas with the files in --out and exits 1 on any difference.
Apache-2.0. Bayanat Labs operating manual. Local files only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ITEM = HERE.parent
SKIP_PATHS = {"scoping_memo.yaml", "scoping_memo.score.yaml", "scoping_memo.score.json"}
ID_BASE = "https://bayanatlabs.com/open/schemas/reports/"


def schema_name(path: str) -> str:
    stem = path.rsplit(".", 1)[0]
    for prefix in ("qa/reports/", "validation/", "signoffs/"):
        if stem.startswith(prefix):
            stem = stem[len(prefix):]
            break
    return stem.replace("/", "_")


def memo_type(memo_schema: dict, dotted: str) -> dict:
    node = memo_schema
    for part in dotted.split("."):
        node = (node.get("properties") or {}).get(part)
        if node is None:
            return {}
    t = node.get("type")
    return {"type": t} if t else {}


def value_type(v) -> dict:
    if isinstance(v, bool):
        return {"type": "boolean"}
    if isinstance(v, (int, float)):
        return {"type": "number"}
    if isinstance(v, str):
        return {"type": "string"}
    if isinstance(v, list) and v:
        return value_type(v[0])
    return {}


def field_schema(c: dict, memo_schema: dict) -> dict:
    if c["type"] == "signoff":
        return {"type": "object", "required": ["name", "date", "verdict"],
                "properties": {"name": {"type": ["string", "null"]}, "date": {"type": ["string", "null"]},
                               "verdict": {"type": "string"}, "role": {"type": "string"}}}
    op = c["op"]
    if op in ("is_true", "is_false"):
        return {"type": "boolean"}
    if op in (">=", "<=", ">", "<") or "value_field" in c:
        return {"type": "number"}
    if op in ("not_null", "exists"):
        return {}
    if op == "contains":
        return {"type": ["array", "string"]}
    if "value_ref" in c:
        return memo_type(memo_schema, c["value_ref"][len("memo:"):])
    return value_type(c.get("value"))


def put(schema: dict, dotted: str, leaf: dict, required: bool, check_id: str) -> None:
    parts = dotted.split(".")
    node = schema
    for i, part in enumerate(parts):
        last = i == len(parts) - 1
        props = node.setdefault("properties", {})
        if last:
            cur = props.get(part)
            merged = dict(leaf) if cur is None else cur
            if cur is not None and leaf and cur.get("type") != leaf.get("type"):
                types = set()
                for t in (cur.get("type"), leaf.get("type")):
                    types |= set(t if isinstance(t, list) else [t]) if t else set()
                merged["type"] = sorted(types) if types else merged.get("type")
            ids = sorted(set((merged.get("x-checks") or []) + [check_id]))
            merged["x-checks"] = ids
            props[part] = merged
        else:
            props.setdefault(part, {"type": "object"})
            node = props[part]
    if required:  # mark the field and every parent object as required
        node = schema
        for i, part in enumerate(parts):
            req = node.setdefault("required", [])
            if part not in req:
                req.append(part)
                req.sort()
            node = node["properties"][part]


def build(stages_doc: dict, dod_doc: dict | None, memo_schema: dict) -> dict[str, dict]:
    checks = []
    for s in stages_doc["stages"]:
        for c in s["gate"]["checks"]:
            checks.append((c, True))
    if dod_doc:
        for it in dod_doc.get("items", []):
            for ph in ("rc", "done"):
                for c in it["checks"].get(ph) or []:
                    checks.append((c, False))
        for pc in dod_doc.get("preconditions", []):
            checks.append((pc["check"], False))
    out: dict[str, dict] = {}
    for c, from_stage in checks:
        if c["type"] not in ("metric", "signoff"):
            continue
        path = c["path"]
        if path in SKIP_PATHS or not path.endswith((".json", ".yaml", ".yml")):
            continue
        name = schema_name(path)
        sch = out.setdefault(name, {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"{ID_BASE}{name}.schema.json",
            "title": f"Bayanat Labs gate report: {c['root']}:{path}",
            "description": ("Generated by scripts/gen_report_schemas.py from the checks in manual/stages.yaml and manual/dod.yaml "
                            "that read this file; do not edit by hand. Declares the type of every field a check reads. "
                            "Extra keys are allowed. A check is n/a only through a memo condition, never because the report says so. "
                            "Apache-2.0."),
            "type": "object",
            "x-root": c["root"],
            "x-path": path,
            "properties": {},
        })
        required = from_stage and not c.get("applies_if") and (c["type"] == "signoff" or c["op"] not in ("not_null", "exists"))
        put(sch, c["field"], field_schema(c, memo_schema), required, c["id"])
    return dict(sorted(out.items()))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stages", default=str(ITEM / "manual/stages.yaml"))
    ap.add_argument("--dod", default=str(ITEM / "manual/dod.yaml"))
    ap.add_argument("--memo-schema", default=str(ITEM / "manual/schemas/scoping_memo_record.schema.json"))
    ap.add_argument("--out", default=str(ITEM / "manual/schemas/reports"))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    stages_doc = yaml.safe_load(Path(a.stages).read_text(encoding="utf-8"))
    dod_doc = yaml.safe_load(Path(a.dod).read_text(encoding="utf-8")) if Path(a.dod).exists() else None
    memo_schema = json.loads(Path(a.memo_schema).read_text(encoding="utf-8"))
    schemas = build(stages_doc, dod_doc, memo_schema)
    index = {name: {"root": s["x-root"], "path": s["x-path"], "schema": f"{name}.schema.json"} for name, s in schemas.items()}
    files = {f"{name}.schema.json": json.dumps(s, indent=2, ensure_ascii=False) + "\n" for name, s in schemas.items()}
    files["INDEX.json"] = json.dumps({"generated_by": "scripts/gen_report_schemas.py", "manual_version": stages_doc["manual_version"],
                                      "reports": index}, indent=2) + "\n"
    out = Path(a.out)
    if a.check:
        diffs = [f for f, body in files.items() if not (out / f).exists() or (out / f).read_text(encoding="utf-8") != body]
        extra = [p.name for p in out.glob("*.json") if p.name not in files] if out.exists() else []
        for f in diffs + extra:
            print(f"STALE {out / f}", file=sys.stderr)
        print(f"check: {len(files)} file(s), {len(diffs) + len(extra)} stale", file=sys.stderr)
        return 1 if diffs or extra else 0
    out.mkdir(parents=True, exist_ok=True)
    for p in out.glob("*.json"):
        if p.name not in files:
            p.unlink()
    for f, body in files.items():
        (out / f).write_text(body, encoding="utf-8")
    print(f"wrote {len(files)} file(s) to {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
