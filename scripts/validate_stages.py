#!/usr/bin/env python3
"""Validate, flatten and evaluate the Bayanat Labs operating-manual stages file.

Usage
  validate_stages.py STAGES.yaml [--schema PATH] [--rules RULES_FILE] [--memo-schema PATH]
                     [--tooling TOOLING.lock.yaml] [--search-root DIR ...]
  validate_stages.py STAGES.yaml --emit-flat OUT.json
  validate_stages.py STAGES.yaml --dod DOD.yaml [--evaluate --phase rc|done --job DIR ...]
  validate_stages.py STAGES.yaml --evaluate --job DIR [--hf DIR] [--gh DIR] [--programme DIR]
                     [--legal-record PATH] [--search-root DIR ...] [--report OUT.json] [--stages 0-8]

Validation mode checks the file against manual/schemas/stages.schema.json and then the
cross-field rules a schema cannot express (13 stages in order, G0-G7 coverage both ways,
phase coverage, unique check ids, signoff roles, optional section references into a rules file,
memo value references, check roots, schema paths, optional tooling keys, and the legal-basis
rule: no stage may wait for a separate legal sign-off; legal positions are cited by the decision
ID of a recorded decision). Exit 0 on success, 1 on any error.

--emit-flat writes a flat output schema (stage.id, name, actions, tools, gate_check, threshold,
evidence_artifact, cr_gate, owner_role) for tools that want strings.

--evaluate runs every gate check against real artefacts (one directory per root) and prints
a JSON report; exit 1 if any applicable check fails or errors. A check whose applies_if names
a memo field that is not set is an error, never n/a (fail closed). The dataset template's bl-gates
is the production evaluator; this one exists so every gate is shown to be machine-checkable.

Apache-2.0. Bayanat Labs operating manual v1.0.1. Reads only local files; no network.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import glob
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import yaml

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover
    sys.exit("jsonschema is required (pip install jsonschema)")

HERE = Path(__file__).resolve().parent
ITEM_DIR = HERE.parent
DEFAULT_SCHEMA = ITEM_DIR / "manual" / "schemas" / "stages.schema.json"
DEFAULT_MEMO_SCHEMA = ITEM_DIR / "manual" / "schemas" / "scoping_memo_record.schema.json"
CR_GATES = ["G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7"]
STAGE_IDS = list(range(13))
# Legal-basis rule: no stage, gate or stop rule may require a separate legal sign-off or review. Legal positions
# are cited by the decision ID of a recorded decision (legal_record root: the organisation's legal record).
COUNSEL_STEP_RE = re.compile(r"(?i)\bcounsel(?:'s)?\s+(?:sign-?off|signs|review|confirm\w*|approv\w*|answer\w*)"
                             r"|\b(?:lawyer|legal)\s+sign-?off|\bsigned\s+off\s+by\s+counsel")


# ----------------------------------------------------------------------------- helpers
def load_any(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        # YAML turns unquoted 2026-10-14 into a date object; JSON Schema expects strings.
        return json.loads(json.dumps(yaml.safe_load(text), default=str))
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    if path.suffix == ".csv":
        return list(csv.DictReader(text.splitlines()))
    return json.loads(text)


def load_rows(path: Path) -> list[dict]:
    if path.suffix == ".parquet":
        try:
            import pandas as pd  # noqa: WPS433
            return json.loads(pd.read_parquet(path).to_json(orient="records", date_format="iso"))
        except Exception as exc:  # pragma: no cover - depends on optional pyarrow
            raise RuntimeError(f"cannot read parquet ({exc.__class__.__name__}); install pyarrow") from exc
    data = load_any(path)
    return data if isinstance(data, list) else [data]


def dotted_get(obj: Any, dotted: str) -> tuple[bool, Any]:
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return False, None
    return True, cur


def as_list(value: Any) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def find_file(rel: str, search_roots: list[Path]) -> Path | None:
    rel_path = rel.split("#", 1)[0]
    for root in search_roots:
        cand = root / rel_path
        if cand.exists():
            return cand
    return None


def conditions(cond: dict | None) -> list[dict]:
    """applies_if is one {field, op, value} test or {all_of: [tests]}; return the list of tests."""
    if not cond:
        return []
    return list(cond["all_of"]) if "all_of" in cond else [cond]


def schema_has_path(schema: dict, dotted: str) -> bool:
    node = schema
    for part in dotted.split("."):
        props = node.get("properties", {}) if isinstance(node, dict) else {}
        if part not in props:
            return False
        node = props[part]
    return True


# ----------------------------------------------------------------------------- validation
def validate(doc: dict, schema: dict, args) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    validator = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
    for err in sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path)):
        loc = "/".join(str(p) for p in err.absolute_path) or "(root)"
        errors.append(f"schema: {loc}: {err.message}")
    if errors:
        return errors, warnings

    stages = doc["stages"]
    ids = [s["id"] for s in stages]
    if ids != STAGE_IDS:
        errors.append(f"stage ids must be 0..12 in order, got {ids}")
    keys = [s["key"] for s in stages]
    if len(set(keys)) != len(keys):
        errors.append("stage keys are not unique")

    # check and threshold ids
    seen_checks: set[str] = set()
    for s in stages:
        for c in s["gate"]["checks"]:
            if not c["id"].startswith(f"S{s['id']}."):
                errors.append(f"stage {s['id']}: check id {c['id']} does not match its stage")
            if c["id"] in seen_checks:
                errors.append(f"duplicate check id {c['id']}")
            seen_checks.add(c["id"])
            if c["type"] == "signoff" and c["role"] not in s["signoff_roles"]:
                errors.append(f"{c['id']}: signoff role {c['role']} not listed in stage signoff_roles")
        for t in s["thresholds"]:
            if not t["id"].startswith(f"T{s['id']}."):
                errors.append(f"stage {s['id']}: threshold id {t['id']} does not match its stage")

    # check roots must be declared in the roots block
    for s in stages:
        for c in s["gate"]["checks"]:
            if c["root"] not in doc["roots"]:
                errors.append(f"{c['id']}: root {c['root']} is not declared in the roots block")
            if c.get("exclude") and c["type"] != "file_absent":
                errors.append(f"{c['id']}: exclude is only valid on file_absent checks")
            if c.get("require_nonempty") and c["type"] != "row_exists":
                errors.append(f"{c['id']}: require_nonempty is only valid on row_exists checks")

    # legal-basis rule: stage text and checks may not wait for a separate legal sign-off
    for s in stages:
        texts = [("purpose", s["purpose"]), ("gate summary", s["gate"]["summary"])]
        texts += [(f"action {i + 1}", a) for i, a in enumerate(s["actions"])]
        texts += [(f"stop condition {i + 1}", c) for i, c in enumerate(s["stop_conditions"])]
        texts += [(f"threshold {t['id']}", f"{t['name']} {t['value']}") for t in s["thresholds"]]
        texts += [(f"check {c['id']}", " ".join(str(c.get(k, "")) for k in ("id", "field", "note")))
                  for c in s["gate"]["checks"]]
        for where, text in texts:
            m = COUNSEL_STEP_RE.search(str(text))
            if m:
                errors.append(f"stage {s['id']} {where}: '{m.group(0)}' - cite the decision ID of a recorded "
                              "decision instead")
        for c in s["gate"]["checks"]:
            if "counsel" in c["id"].lower() or "counsel" in str(c.get("field", "")).lower():
                errors.append(f"{c['id']}: check reads a separate legal sign-off; read the recorded decision instead")

    # owners and roles
    for s in stages:
        if s["owner"] not in doc["owners"]:
            errors.append(f"stage {s['id']}: owner {s['owner']} not in owners")
        for r in s["signoff_roles"]:
            if r not in doc["signoff_roles"]:
                errors.append(f"stage {s['id']}: signoff role {r} not declared")

    # G0-G7 coverage, both directions, and consistency with the cr_gates block
    for g in CR_GATES:
        if g not in doc["cr_gates"]:
            errors.append(f"cr_gates block lacks {g}")
            continue
        declared = sorted(doc["cr_gates"][g]["stages"])
        actual = sorted(s["id"] for s in stages if g in s["cr_gates"])
        if not actual:
            errors.append(f"{g} is not mapped to any stage")
        if declared != actual:
            errors.append(f"{g}: cr_gates block says stages {declared}, stage entries say {actual}")
    for s in stages:
        if not s["cr_gates"] and not s.get("coordinator_check"):
            errors.append(f"stage {s['id']} maps to no G gate and has no coordinator_check")

    # phases
    if "phases" in doc:
        flat = sorted(i for v in doc["phases"].values() for i in v)
        if flat != STAGE_IDS:
            errors.append(f"phases must cover stages 0..12 exactly once, got {flat}")
        for name, members in doc["phases"].items():
            for i in members:
                if 0 <= i <= 12 and stages[i]["phase"] != name:
                    errors.append(f"stage {i} phase {stages[i]['phase']} but listed under {name}")

    # memo value references and applies_if fields
    memo_schema_path = Path(args.memo_schema) if args.memo_schema else DEFAULT_MEMO_SCHEMA
    if memo_schema_path.exists():
        memo_schema = json.loads(memo_schema_path.read_text(encoding="utf-8"))
        for s in stages:
            for c in s["gate"]["checks"]:
                refs = []
                if c.get("value_ref"):
                    refs.append(c["value_ref"])
                for cond in conditions(c.get("applies_if")):
                    refs.append(cond["field"])
                for v in (c.get("match") or {}).values():
                    if isinstance(v, str) and v.startswith("memo:"):
                        refs.append(v)
                for ref in refs:
                    if not schema_has_path(memo_schema, ref[len("memo:"):]):
                        errors.append(f"{c['id']}: {ref} is not a field of {memo_schema_path.name}")
    else:
        warnings.append(f"memo schema not found at {memo_schema_path}; memo references not checked")

    # schema files referenced by checks
    search_roots = [Path(p) for p in (args.search_root or [])] or [ITEM_DIR, ITEM_DIR.parent.parent]
    for s in stages:
        for c in s["gate"]["checks"]:
            if c.get("schema") and not find_file(c["schema"], search_roots):
                warnings.append(f"{c['id']}: schema {c['schema']} not found under {', '.join(map(str, search_roots))}")

    # tools vs tooling.lock.yaml (owned by the tooling part; warnings only)
    if args.tooling and Path(args.tooling).exists():
        lock = yaml.safe_load(Path(args.tooling).read_text(encoding="utf-8")) or {}
        entries = lock.get("tools") or lock.get("entries") or lock.get("items") or []
        names = set()
        for e in entries if isinstance(entries, list) else []:
            for k in ("key", "name", "id"):
                if isinstance(e, dict) and e.get(k):
                    names.add(str(e[k]).lower())
        if isinstance(entries, dict):
            names |= {str(k).lower() for k in entries}
        blocked = set()
        for e in entries if isinstance(entries, list) else []:
            if isinstance(e, dict) and e.get("blocked_for_release_path") is True:
                blocked.add(str(e.get("key") or e.get("name")).lower())
        for s in stages:
            for t in s["tools"]:
                if t.startswith("bayanatlabs:"):
                    continue  # Bayanat Labs' own tools are pinned by their own repositories
                if t.lower() not in names:
                    warnings.append(f"stage {s['id']}: tool key '{t}' not found in {args.tooling}")
                elif t.lower() in blocked:
                    warnings.append(f"stage {s['id']}: tool '{t}' is blocked_for_release_path in the lock "
                                    "(internal use only; the stage-8 check S8.release_tools enforces it)")
    elif args.tooling:
        warnings.append(f"tooling lock {args.tooling} not found; tool keys not cross-checked")

    return errors, warnings


# ----------------------------------------------------------------------------- flat export
def render_check(c: dict) -> str:
    root = c["root"]
    t = c["type"]
    if t == "file_exists":
        if c.get("any_of"):
            body = "exists_any(" + ", ".join(f"{root}:{p}" for p in c["any_of"]) + ")"
        else:
            body = "exists(" + ", ".join(f"{root}:{p}" for p in as_list(c["path"])) + ")"
    elif t == "file_absent":
        body = "absent(" + ", ".join(f"{root}:{p}" for p in as_list(c["path"])) + ")"
        if c.get("exclude"):
            body += " except " + ", ".join(c["exclude"])
    elif t == "schema_validates":
        target = c.get("path") or "|".join(c.get("any_of", []))
        body = f"valid({root}:{target}, {c['schema']})"
    elif t == "metric":
        if "value_ref" in c:
            rhs = c["value_ref"]
        elif "value_field" in c:
            rhs = f"{c['value_field']}"
        elif "value" in c:
            rhs = json.dumps(c["value"], ensure_ascii=False)
        else:
            rhs = ""
        body = f"{root}:{c['path']}:{c['field']} {c['op']} {rhs}".rstrip()
    elif t == "signoff":
        body = f"signoff({root}:{c['path']}:{c['field']}, role={c['role']}, verdict={c['require_verdict']})"
    elif t == "row_exists":
        match = ", ".join(f"{k}={v}" for k, v in c["match"].items())
        body = f"row({root}:{c['path']}, {match})"
        if c.get("require_nonempty"):
            body = body[:-1] + ", nonempty=" + "+".join(c["require_nonempty"]) + ")"
    else:  # pragma: no cover
        body = t
    if c.get("applies_if"):
        parts = [f"{cond['field']} {cond['op']} {json.dumps(cond.get('value')) if 'value' in cond else ''}".rstrip()
                 for cond in conditions(c["applies_if"])]
        body = "[if " + " and ".join(parts) + f"] {body}"
    return body


def flatten(doc: dict) -> dict:
    out = []
    for s in doc["stages"]:
        human = [f"human:{c['role']}" for c in s["gate"]["checks"] if c["type"] == "signoff"]
        out.append({
            "id": s["id"],
            "name": s["name"],
            "actions": s["actions"],
            "tools": s["tools"],
            "gate_check": " and ".join(render_check(c) for c in s["gate"]["checks"]),
            "threshold": "; ".join(f"{t['name']}: {t['value']}" for t in s["thresholds"]),
            "evidence_artifact": [f"{o['root']}:{o['path']}" for o in s["outputs"]],
            "cr_gate": s["cr_gates"] or ["coordinator"],
            "owner_role": s["owner"] if s["owner"] != "agent" else "dataset-agent",
            "human_signoffs": human,
            "blocking": s["blocking"],
        })
    return {"manual_version": doc["manual_version"], "schema_version": doc["schema_version"], "stages": out}


# ----------------------------------------------------------------------------- evaluation
OPS = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    ">=": lambda a, b: a is not None and b is not None and a >= b,
    "<=": lambda a, b: a is not None and b is not None and a <= b,
    ">": lambda a, b: a is not None and b is not None and a > b,
    "<": lambda a, b: a is not None and b is not None and a < b,
    "in": lambda a, b: a in (b or []),
    "not_in": lambda a, b: a not in (b or []),
    "contains": lambda a, b: isinstance(a, (list, str)) and b in a,
}


class Evaluator:
    def __init__(self, roots: dict[str, Path | None], search_roots: list[Path]):
        self.roots = roots
        self.search_roots = search_roots
        self.memo: dict | None = None
        job = roots.get("job")
        if job and (job / "scoping_memo.yaml").exists():
            self.memo = load_any(job / "scoping_memo.yaml")

    def resolve(self, value: Any) -> Any:
        if isinstance(value, str) and value.startswith("memo:"):
            if self.memo is None:
                raise RuntimeError("memo reference but job/scoping_memo.yaml is missing")
            found, v = dotted_get(self.memo, value[5:])
            if not found:
                raise RuntimeError(f"{value} not set in the memo")
            return v
        return value

    def root(self, name: str) -> Path:
        r = self.roots.get(name)
        if r is None:
            raise RuntimeError(f"no directory given for root '{name}'")
        return r

    def compare(self, actual: Any, op: str, expected: Any = None) -> bool:
        if op == "exists":
            return True
        if op == "not_null":
            return actual is not None and actual != ""
        if op == "is_true":
            return actual is True
        if op == "is_false":
            return actual is False
        return OPS[op](actual, expected)

    def check(self, c: dict) -> tuple[str, str]:
        for cond in conditions(c.get("applies_if")):
            try:
                actual = self.resolve(cond["field"])
            except RuntimeError as exc:
                # Fail closed: a missing memo flag must never silently skip a check.
                return "error", f"applies_if: {exc}"
            if not self.compare(actual, cond["op"], cond.get("value")):
                return "n/a", f"condition {cond['field']} {cond['op']} not met"
        root = self.root(c["root"])
        t = c["type"]
        if t == "file_exists":
            if c.get("any_of"):
                hits = [p for p in c["any_of"] if glob.glob(str(root / p))]
                return ("pass", f"found {hits[0]}") if hits else ("fail", f"none of {c['any_of']} exists")
            missing = [p for p in as_list(c["path"]) if len(glob.glob(str(root / p))) < c.get("min_count", 1)]
            return ("fail", f"missing: {missing}") if missing else ("pass", "all present")
        if t == "file_absent":
            excluded: set[str] = set()
            for e in c.get("exclude") or []:
                excluded |= {str(Path(x).resolve()) for x in glob.glob(str(root / e), recursive=True)}
            found = []
            for p in as_list(c["path"]):
                for x in glob.glob(str(root / p), recursive=True):
                    if Path(x).is_file() and str(Path(x).resolve()) not in excluded:
                        found.append(str(Path(x).relative_to(root)))
            found = sorted(set(found))
            return ("fail", f"{len(found)} forbidden file(s), e.g. {found[:3]}") if found else ("pass", "none present")
        if t == "schema_validates":
            targets = as_list(c.get("path")) or c.get("any_of", [])
            existing = [root / p for p in targets if (root / p).exists()]
            if not existing:
                return "fail", f"file not found: {targets}"
            schema_file = find_file(c["schema"], self.search_roots)
            if schema_file is None:
                return "error", f"schema {c['schema']} not found"
            validator = make_validator(schema_file, c["schema"])
            rows = load_rows(existing[0])
            bad = 0
            first = ""
            for i, row in enumerate(rows):
                errs = list(validator.iter_errors(row))
                if errs:
                    bad += 1
                    first = first or f"row {i}: {errs[0].message}"
            return ("fail", f"{bad}/{len(rows)} invalid; {first}") if bad else ("pass", f"{len(rows)} valid")
        if t == "metric":
            f = root / c["path"]
            if not f.exists():
                return "fail", f"file not found: {c['path']}"
            data = load_any(f)
            found, actual = dotted_get(data, c["field"])
            if not found:
                return "fail", f"field {c['field']} missing"
            if "value_ref" in c:
                expected = self.resolve(c["value_ref"])
            elif "value_field" in c:
                ok, expected = dotted_get(data, c["value_field"])
                if not ok:
                    return "fail", f"field {c['value_field']} missing"
            else:
                expected = c.get("value")
            ok = self.compare(actual, c["op"], expected)
            return ("pass" if ok else "fail"), f"{c['field']}={actual!r} {c['op']} {expected!r}"
        if t == "signoff":
            f = root / c["path"]
            if not f.exists():
                return "fail", f"file not found: {c['path']}"
            found, entry = dotted_get(load_any(f), c["field"])
            if not found or not isinstance(entry, dict):
                return "fail", f"no sign-off at {c['field']}"
            if not entry.get("name"):
                return "fail", "sign-off has no name"
            try:
                dt.date.fromisoformat(str(entry.get("date"))[:10])
            except ValueError:
                return "fail", "sign-off has no valid date"
            if entry.get("role") and entry["role"] != c["role"]:
                return "fail", f"sign-off role {entry['role']} != {c['role']}"
            if entry.get("verdict") != c["require_verdict"]:
                return "fail", f"verdict {entry.get('verdict')!r} != {c['require_verdict']!r}"
            return "pass", f"signed by {entry['name']} on {entry['date']}"
        if t == "row_exists":
            f = root / c["path"]
            if not f.exists():
                return "fail", f"file not found: {c['path']}"
            match = {k: self.resolve(v) for k, v in c["match"].items()}
            rows = [r for r in load_rows(f) if all(r.get(k) == v for k, v in match.items())]
            if not rows:
                return "fail", f"no row matching {match}"
            empty = [k for k in c.get("require_nonempty") or [] if rows[-1].get(k) in (None, "")]
            if empty:
                return "fail", f"matching row has empty {empty}"
            if c.get("schema"):
                schema_file = find_file(c["schema"], self.search_roots)
                if schema_file is None:
                    return "error", f"schema {c['schema']} not found"
                validator = make_validator(schema_file, c["schema"])
                errs = list(validator.iter_errors(rows[-1]))
                if errs:
                    return "fail", f"matching row invalid: {errs[0].message}"
            return "pass", f"{len(rows)} matching row(s)"
        return "error", f"unknown check type {t}"


def make_validator(schema_file: Path, ref: str):
    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    pointer = ref.split("#", 1)[1] if "#" in ref else ""
    if not pointer:
        return Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
    from referencing import Registry, Resource  # bundled with jsonschema >= 4.18
    uri = schema.get("$id", "urn:bayanatlabs:schema")
    registry = Registry().with_resource(uri, Resource.from_contents(schema))
    wrapper = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$ref": f"{uri}#{pointer}"}
    return Draft202012Validator(wrapper, registry=registry, format_checker=Draft202012Validator.FORMAT_CHECKER)


def parse_stage_range(spec: str | None) -> set[int]:
    if not spec:
        return set(STAGE_IDS)
    out: set[int] = set()
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out |= set(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return out


def evaluate(doc: dict, args) -> dict:
    roots = {
        "job": Path(args.job) if args.job else None,
        "hf_repo": Path(args.hf) if args.hf else None,
        "gh_repo": Path(args.gh) if args.gh else None,
        "programme": Path(args.programme) if args.programme else None,
        "legal_record": Path(args.legal_record) if getattr(args, "legal_record", None) else None,
    }
    search_roots = [Path(p) for p in (args.search_root or [])] or [ITEM_DIR, ITEM_DIR.parent.parent]
    ev = Evaluator(roots, search_roots)
    wanted = parse_stage_range(args.stages_spec)
    report = {"manual_version": doc["manual_version"], "evaluated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
              "stages": [], "summary": {"pass": 0, "fail": 0, "n/a": 0, "error": 0}}
    for s in doc["stages"]:
        if s["id"] not in wanted:
            continue
        results = []
        for c in s["gate"]["checks"]:
            try:
                status, detail = ev.check(c)
            except Exception as exc:  # report, never crash the whole run
                status, detail = "error", f"{exc.__class__.__name__}: {exc}"
            report["summary"][status] += 1
            results.append({"id": c["id"], "status": status, "detail": detail})
        passed = all(r["status"] in ("pass", "n/a") for r in results)
        report["stages"].append({"id": s["id"], "name": s["name"], "gate_passed": passed,
                                 "cr_gates": s["cr_gates"], "checks": results})
    report["all_passed"] = report["summary"]["fail"] == 0 and report["summary"]["error"] == 0
    return report


# ----------------------------------------------------------------------------- definition of done
CHECK_REQUIRED = {
    "file_exists": [],
    "file_absent": ["path"],
    "schema_validates": ["schema"],
    "metric": ["path", "field", "op"],
    "signoff": ["path", "field", "role", "require_verdict"],
    "row_exists": ["path", "match"],
}


def validate_dod(dod: dict, doc: dict) -> list[str]:
    """Structural rules for manual/dod.yaml (12 items, check syntax, coverage of the release artefact list)."""
    errors: list[str] = []
    items = dod.get("items") or []
    if len(items) != 12:
        errors.append(f"dod: expected 12 items, found {len(items)}")
    ids = [i.get("id") for i in items]
    if ids != [f"D{n:02d}" for n in range(1, 13)]:
        errors.append(f"dod: item ids must be D01..D12 in order, got {ids}")
    roots = set(doc["roots"]) if doc else {"job", "hf_repo", "gh_repo", "programme"}
    seen: set[str] = set()
    all_checks = [pc["check"] for pc in dod.get("preconditions", [])]
    for it in items:
        for key in ("item", "artefacts", "evidence_path", "checks"):
            if key not in it:
                errors.append(f"dod {it.get('id')}: missing {key}")
        if "done" not in it:
            errors.append(f"dod {it.get('id')}: missing done (null in the template)")
        checks = it.get("checks", {})
        if not checks.get("rc"):
            errors.append(f"dod {it.get('id')}: needs at least one rc check")
        for phase in ("rc", "done"):
            for c in checks.get(phase, []) or []:
                if not str(c.get("id", "")).startswith(f"{it['id']}."):
                    errors.append(f"dod {it['id']}: check id {c.get('id')} does not match its item")
                all_checks.append(c)
    for c in all_checks:
        cid = c.get("id")
        if cid in seen:
            errors.append(f"dod: duplicate check id {cid}")
        seen.add(cid)
        t = c.get("type")
        if t not in CHECK_REQUIRED:
            errors.append(f"dod {cid}: unknown check type {t}")
            continue
        if c.get("root") not in roots:
            errors.append(f"dod {cid}: unknown root {c.get('root')}")
        for f in CHECK_REQUIRED[t]:
            if f not in c:
                errors.append(f"dod {cid}: {t} check lacks {f}")
        if t in ("file_exists", "schema_validates") and not (c.get("path") or c.get("any_of")):
            errors.append(f"dod {cid}: needs path or any_of")
    covered = {a for it in items for a in it.get("artefacts", [])}
    for art in dod.get("release_artefacts", []):
        if art not in covered:
            errors.append(f"dod: release artefact not covered by any item: {art}")
    return errors


def evaluate_dod(dod: dict, args, phase: str) -> dict:
    roots = {
        "job": Path(args.job) if args.job else None,
        "hf_repo": Path(args.hf) if args.hf else None,
        "gh_repo": Path(args.gh) if args.gh else None,
        "programme": Path(args.programme) if args.programme else None,
        "legal_record": Path(args.legal_record) if getattr(args, "legal_record", None) else None,
    }
    search_roots = [Path(p) for p in (args.search_root or [])] or [ITEM_DIR, ITEM_DIR.parent.parent]
    ev = Evaluator(roots, search_roots)
    phases = ["rc"] if phase == "rc" else ["rc", "done"]
    report = {"manual_version": dod.get("manual_version"), "phase": phase, "items": [],
              "summary": {"pass": 0, "fail": 0, "n/a": 0, "error": 0}}

    def run(c: dict) -> dict:
        try:
            status, detail = ev.check(c)
        except Exception as exc:
            status, detail = "error", f"{exc.__class__.__name__}: {exc}"
        report["summary"][status] += 1
        return {"id": c["id"], "status": status, "detail": detail}

    report["preconditions"] = [run(pc["check"]) for pc in dod.get("preconditions", [])]
    for it in dod["items"]:
        res = [run(c) for ph in phases for c in (it["checks"].get(ph) or [])]
        report["items"].append({"id": it["id"], "item": it["item"],
                                "done": all(r["status"] in ("pass", "n/a") for r in res), "checks": res})
    report["all_done"] = report["summary"]["fail"] == 0 and report["summary"]["error"] == 0
    return report


# ----------------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("stages")
    p.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    p.add_argument("--memo-schema")
    p.add_argument("--tooling", help="manual/tooling.lock.yaml (optional cross-check, warnings only)")
    p.add_argument("--search-root", action="append", help="directories in which schema paths are resolved")
    p.add_argument("--emit-flat", metavar="OUT.json")
    p.add_argument("--evaluate", action="store_true")
    p.add_argument("--job"), p.add_argument("--hf"), p.add_argument("--gh"), p.add_argument("--programme")
    p.add_argument("--legal-record", dest="legal_record", help="the organisation's legal record (configured path): its table of recorded decisions")
    p.add_argument("--stages", dest="stages_range", help="e.g. 0-8 (evaluate mode)")
    p.add_argument("--report", help="write the evaluation report here")
    p.add_argument("--dod", metavar="DOD.yaml", help="also validate (and with --evaluate, evaluate) the definition of done")
    p.add_argument("--phase", choices=["rc", "done"], default="rc", help="definition-of-done phase (default rc)")
    args = p.parse_args(argv)
    args.stages_spec = args.stages_range
    doc = yaml.safe_load(Path(args.stages).read_text(encoding="utf-8"))
    schema = json.loads(Path(args.schema).read_text(encoding="utf-8"))

    errors, warnings = validate(doc, schema, args)
    for w in warnings:
        print(f"WARN  {w}", file=sys.stderr)
    for e in errors:
        print(f"ERROR {e}", file=sys.stderr)
    if errors:
        print(f"FAIL: {len(errors)} error(s) in {args.stages}", file=sys.stderr)
        return 1
    n_checks = sum(len(s["gate"]["checks"]) for s in doc["stages"])
    print(f"OK: {args.stages} valid: {len(doc['stages'])} stages, {n_checks} gate checks, "
          f"{len(warnings)} warning(s)", file=sys.stderr)

    if args.emit_flat:
        Path(args.emit_flat).write_text(json.dumps(flatten(doc), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.emit_flat}", file=sys.stderr)

    dod = None
    if args.dod:
        dod = yaml.safe_load(Path(args.dod).read_text(encoding="utf-8"))
        dod_errors = validate_dod(dod, doc)
        for e in dod_errors:
            print(f"ERROR {e}", file=sys.stderr)
        if dod_errors:
            print(f"FAIL: {len(dod_errors)} error(s) in {args.dod}", file=sys.stderr)
            return 1
        print(f"OK: {args.dod} valid: {len(dod['items'])} items", file=sys.stderr)

    if args.evaluate and dod is not None:
        report = evaluate_dod(dod, args, args.phase)
        text = json.dumps(report, ensure_ascii=False, indent=2)
        if args.report:
            Path(args.report).write_text(text + "\n", encoding="utf-8")
        print(text)
        return 0 if report["all_done"] else 1

    if args.evaluate:
        report = evaluate(doc, args)
        text = json.dumps(report, ensure_ascii=False, indent=2)
        if args.report:
            Path(args.report).write_text(text + "\n", encoding="utf-8")
        print(text)
        return 0 if report["all_passed"] else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
