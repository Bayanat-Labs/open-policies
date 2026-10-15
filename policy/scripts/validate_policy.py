#!/usr/bin/env python3
"""Validate the Bayanat Labs open-programme policy files.

Checks, in order:
  1. Every policy YAML validates against its JSON Schema in schemas/.
  2. Semantic rules: rubric weights sum to 100, exactly one gate criterion
     (legal_cleanliness), priority thresholds descend, the legal gate maps red, yellow
     and green as the policy says, three tiers, Tier 2 publishes no verbatim content,
     input allowlist and output tags kept in separate tables, no NC, Apache or MIT tag
     on data rows, five index-only triggers, every file carries the same policy version,
     POLICY.ar.md has the same sections as POLICY.md, and every YAML file in the folder
     is one the validator knows.
  3. Fidelity checklist (fidelity/checklist.yaml): every criterion, weight, anchor,
     tier, licence row, principle, index-only trigger and stop rule is present with its
     expected wording.
  4. Banners: every Markdown file states the version, the counsel review line and
     "Documentation, not legal advice" (Arabic files: the Arabic equivalents), and
     none carries a draft marker.
  5. Optional extra checks, when an extension module (validate_policy_ext.py) is present
     next to this script (reported; --require-evidence makes missing evidence a failure).
  6. Optional: a licence validation CSV has no failing rows (--licence-csv).

Usage:
  python validate_policy.py [--policy-dir DIR] [--licence-csv licence_validation.csv] [--json OUT.json]
                            [--require-evidence] [-q]
Exit code 0 when every check passes, 1 otherwise.
Requires: pyyaml, jsonschema.
"""
import argparse
import csv
import importlib.util
import json
import os
import re
import sys
import unicodedata

import yaml
from jsonschema import Draft202012Validator

HERE = os.path.dirname(os.path.abspath(__file__))
YAML_SCHEMAS = {
    "rubric.yaml": "rubric.schema.json",
    "tiers.yaml": "tiers.schema.json",
    "licence-matrix.yaml": "licence-matrix.schema.json",
    "principles.yaml": "principles.schema.json",
    "index-only-rules.yaml": "index-only-rules.schema.json",
    "fidelity/checklist.yaml": "fidelity-checklist.schema.json",
}
CORE_MD = ["POLICY.md", "POLICY.ar.md", "stop-rules.md", "gating-exception.md",
           "claims-rules.md", "CHANGELOG.md"]


def load_extension():
    """Optional extra checks from an extension module next to this script, or None."""
    p = os.path.join(HERE, "validate_policy_ext.py")
    if not os.path.exists(p):
        return None
    spec = importlib.util.spec_from_file_location("validate_policy_ext", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


EXT = load_extension()


def yaml_schemas(ext):
    """YAML files and their schemas, with the extension's file (if any) after principles.yaml."""
    out = {}
    for k, v in YAML_SCHEMAS.items():
        out[k] = v
        if k == "principles.yaml" and ext is not None:
            out[ext.YAML_FILE] = ext.SCHEMA_FILE
    return out


def md_files_for(ext):
    files = list(CORE_MD)
    if ext is not None:
        files.insert(2, ext.MD_FILE)
    return files


VERSION_RE = re.compile(r"Version (\d+\.\d+\.\d+)")
VERSION_AR_RE = re.compile(r"الإصدار (\d+\.\d+\.\d+)")


def norm(text):
    """Lower-case, fold quotes and dashes, drop punctuation, collapse spaces."""
    t = unicodedata.normalize("NFKC", str(text)).lower()
    t = t.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    t = re.sub(r"[^\w]+", " ", t, flags=re.UNICODE)
    return re.sub(r"\s+", " ", t).strip()


SEG = re.compile(r"^([^\[\]]+)(?:\[([^=\]]+)=([^\]]+)\])?$")


def resolve(doc, path):
    """Resolve a path like 'criteria[id=impact].anchors.1'. Raises KeyError when missing."""
    cur = doc
    for seg in path.split("."):
        m = SEG.match(seg)
        if not m:
            raise KeyError(f"bad path segment {seg!r}")
        key, fld, val = m.groups()
        if not isinstance(cur, dict) or key not in cur:
            raise KeyError(f"missing key {key!r}")
        cur = cur[key]
        if fld is not None:
            if not isinstance(cur, list):
                raise KeyError(f"{key!r} is not a list")
            hits = [x for x in cur if isinstance(x, dict) and str(x.get(fld)) == val]
            if len(hits) != 1:
                raise KeyError(f"{len(hits)} items with {fld}={val} in {key!r}")
            cur = hits[0]
    return cur


def flatten(value):
    if isinstance(value, dict):
        return " ".join(flatten(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(flatten(v) for v in value)
    return "" if value is None else str(value)


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def extension_for(pdir):
    """The extension's checks run on a folder that carries the extension's YAML file; otherwise they are
    skipped."""
    if EXT is None:
        return None
    return EXT if os.path.exists(os.path.join(pdir, EXT.YAML_FILE)) else None


def check_schemas(pdir, results, ext=None):
    docs = {}
    for yname, sname in yaml_schemas(ext).items():
        ypath = os.path.join(pdir, yname)
        spath = os.path.join(pdir, "schemas", sname)
        if not os.path.exists(ypath):
            results.append(("schema", yname, False, "file missing"))
            continue
        doc = load_yaml(ypath)
        docs[yname] = doc
        with open(spath, encoding="utf-8") as f:
            schema = json.load(f)
        Draft202012Validator.check_schema(schema)
        errs = sorted(Draft202012Validator(schema).iter_errors(doc), key=lambda e: list(e.absolute_path))
        if errs:
            msg = "; ".join(f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}" for e in errs[:5])
            results.append(("schema", yname, False, msg))
        else:
            results.append(("schema", yname, True, f"valid against schemas/{sname}"))
    return docs


def headings(path):
    with open(path, encoding="utf-8") as f:
        return [l for l in f.read().splitlines() if l.startswith("## ")]


def check_semantics(pdir, docs, results, md_files, ext=None):
    r = docs.get("rubric.yaml")
    if r:
        w = sum(c["weight"] for c in r["criteria"])
        results.append(("semantic", "rubric weights sum to 100", w == 100, f"sum={w}"))
        gates = [c["id"] for c in r["criteria"] if c["is_gate"]]
        results.append(("semantic", "exactly one gate criterion (legal_cleanliness)", gates == ["legal_cleanliness"], f"gates={gates}"))
        ids = sorted(c["id"] for c in r["criteria"])
        exp = sorted(["impact", "claim_strength", "ease", "legal_cleanliness", "commercial_pull"])
        results.append(("semantic", "five criteria, each once", ids == exp, f"ids={ids}"))
        th = [x["min_weighted_score"] for x in r["priority_thresholds"]["rules"]]
        results.append(("semantic", "priority thresholds descend and end at 0", th == sorted(th, reverse=True) and th[-1] == 0, f"{th}"))
        verdicts = {o["legal_tier"]: (o["legal_verdict"], o["max_release_tier"]) for o in r["legal_gate"]["outcomes"]}
        ok = verdicts == {"red": ("excluded", None), "yellow": ("tier2_only", 2), "green": ("tier1_eligible", 1)}
        results.append(("semantic", "legal gate: red excluded, yellow tier 2 only, green tier 1", ok, f"{verdicts}"))
    t = docs.get("tiers.yaml")
    if t:
        results.append(("semantic", "three tiers 1, 2, 3", [x["number"] for x in t["tiers"]] == [1, 2, 3], ""))
        t2 = [x for x in t["tiers"] if x["number"] == 2][0]
        results.append(("semantic", "tier 2 publishes no verbatim content", t2.get("no_verbatim_content") is True, ""))
    lm = docs.get("licence-matrix.yaml")
    if lm:
        out_tags = {row["hf_licence_tag"] for row in lm["output_licence_tags"]["rows"]}
        in_names = {x["name"] for x in lm["input_licences"]["allowlist"]}
        results.append(("semantic", "input allowlist and output tags are separate tables",
                        "output_licence_tags" in lm and "input_licences" in lm and not (out_tags & in_names), ""))
        forbidden = set()
        for n in lm["output_rules"]["never"]:
            forbidden |= set(n.get("forbidden_tags", []))
        bad = [row["id"] for row in lm["output_licence_tags"]["rows"] if row["hf_licence_tag"] in forbidden]
        results.append(("semantic", "no output row uses a forbidden NC tag", not bad, f"{bad}"))
        data_rows_apache = [row["id"] for row in lm["output_licence_tags"]["rows"] if row["hf_licence_tag"] in ("apache-2.0", "mit")]
        results.append(("semantic", "no Apache or MIT tag on data rows", not data_rows_apache, f"{data_rows_apache}"))
    io = docs.get("index-only-rules.yaml")
    if io:
        results.append(("semantic", "five index-only triggers", len(io["rules"]) >= 5, f"{len(io['rules'])}"))
    if ext is not None:
        ext.check_semantics(docs, results)
    known = set(yaml_schemas(ext))
    found = []
    for d, dirs, fs in os.walk(pdir):
        dirs[:] = [x for x in dirs if not x.startswith(".") and x != "__pycache__"]
        found += [os.path.relpath(os.path.join(d, f), pdir).replace(os.sep, "/")
                  for f in fs if f.endswith((".yaml", ".yml"))]
    unknown = sorted(f for f in found if f not in known)
    results.append(("semantic", "every YAML file in the folder is one the validator checks", not unknown,
                    f"unknown: {unknown}" if unknown else f"{len(found)} files"))
    # one version everywhere
    versions = {}
    for yname, doc in docs.items():
        if yname.startswith("fidelity/") or not isinstance(doc, dict):
            continue
        versions[yname] = str(doc.get("policy_version"))
    for name in md_files:
        p = os.path.join(pdir, name)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                head = f.read(3000)
            m = VERSION_RE.search(head) or VERSION_AR_RE.search(head)
            versions[name] = m.group(1) if m else None
    distinct = set(versions.values())
    results.append(("semantic", "every file carries the same policy version", len(distinct) == 1 and None not in distinct,
                    f"{sorted(distinct, key=str)}" if len(distinct) != 1 else f"version {distinct.pop()}"))
    en, ar = os.path.join(pdir, "POLICY.md"), os.path.join(pdir, "POLICY.ar.md")
    if os.path.exists(en) and os.path.exists(ar):
        he, ha = headings(en), headings(ar)
        nums_en = [re.match(r"## (\d+)\.", h).group(1) for h in he if re.match(r"## (\d+)\.", h)]
        nums_ar = [re.match(r"## (\d+)\.", h).group(1) for h in ha if re.match(r"## (\d+)\.", h)]
        results.append(("semantic", "POLICY.ar.md has the same numbered sections as POLICY.md",
                        nums_en == nums_ar and len(he) == len(ha), f"EN {len(he)} sections {nums_en}; AR {len(ha)} sections {nums_ar}"))



def check_fidelity(pdir, docs, results):
    cl = docs.get("fidelity/checklist.yaml")
    if not cl:
        results.append(("fidelity", "checklist", False, "checklist missing"))
        return
    md_cache = {}
    for it in cl["items"]:
        fname = it["file"]
        problems = []
        # 1. present in the policy
        try:
            if fname.endswith(".md"):
                if fname not in md_cache:
                    with open(os.path.join(pdir, fname), encoding="utf-8") as f:
                        md_cache[fname] = norm(f.read())
                hay = md_cache[fname]
                if norm(it["policy_text"]) not in hay:
                    problems.append("policy_text not found in " + fname)
            else:
                doc = docs.get(fname)
                if doc is None:
                    doc = load_yaml(os.path.join(pdir, fname))
                    docs[fname] = doc
                val = resolve(doc, it["path"]) if it.get("path") else doc
                if "expect" in it:
                    e = it["expect"]
                    if isinstance(val, list):
                        if e not in val:
                            problems.append(f"expected {e!r} in list {val!r}")
                    elif val != e:
                        problems.append(f"expected {e!r}, found {val!r}")
                if "policy_text" in it and norm(it["policy_text"]) not in norm(flatten(val)):
                    problems.append(f"policy_text not found at {it.get('path')}")
        except KeyError as ex:
            problems.append(f"path {it.get('path')}: {ex}")
        except FileNotFoundError:
            problems.append(f"{fname} missing")
        results.append(("fidelity", it["id"], not problems, "; ".join(problems) or it["kind"]))


def check_banners(pdir, results, md_files):
    for name in md_files:
        p = os.path.join(pdir, name)
        if not os.path.exists(p):
            results.append(("banner", name, False, "file missing"))
            continue
        with open(p, encoding="utf-8") as f:
            head = f.read(3000)
        if name.endswith(".ar.md"):
            ok = (VERSION_AR_RE.search(head) is not None and re.search(r"آخر مراجعة من المستشار القانوني|مراجعة المستشار القانوني", head)
                  and "توثيق، وليس استشارة قانونية" in head)
        else:
            ok = (VERSION_RE.search(head) is not None and re.search(r"(?:Last r|R)eviewed by counsel", head)
                  and re.search(r"not legal advice", head, re.I) is not None)
        ok = ok and "DRAFT" not in head and "do not publish" not in head.lower()
        results.append(("banner", name, ok, "version, counsel line and not-legal-advice notice" if ok else "banner missing or still marked draft"))


def check_licence_csv(path, results):
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    bad = [r for r in rows if r.get("result", "").startswith("FAIL")]
    results.append(("licences", os.path.basename(path), not bad, f"{len(rows)} rows, {len(bad)} failing"))


def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--policy-dir", default=os.path.dirname(here))
    ap.add_argument("--licence-csv", help="licence validation CSV")
    ap.add_argument("--json", help="write the full result list as JSON")
    ap.add_argument("--require-evidence", action="store_true")
    ap.add_argument("-q", "--quiet", action="store_true", help="print failures and the summary only")
    a = ap.parse_args(argv)
    ext = extension_for(a.policy_dir)
    md_files = md_files_for(ext)
    results = []
    docs = check_schemas(a.policy_dir, results, ext)
    check_semantics(a.policy_dir, docs, results, md_files, ext)
    check_fidelity(a.policy_dir, docs, results)
    check_banners(a.policy_dir, results, md_files)
    if ext is not None:
        ext.check_evidence(docs, results, a.require_evidence)
    if a.licence_csv:
        check_licence_csv(a.licence_csv, results)
    by = {}
    for kind, name, ok, msg in results:
        by.setdefault(kind, [0, 0])
        by[kind][0 if ok else 1] += 1
        if not ok or not a.quiet:
            print(f"[{'PASS' if ok else 'FAIL'}] {kind:9s} {name}: {msg}")
    print("\nSummary:")
    for kind, (p, f) in by.items():
        print(f"  {kind:9s} {p} pass, {f} fail")
    fid = by.get("fidelity", [0, 0])
    if fid[0] + fid[1]:
        print(f"  fidelity coverage: {100.0 * fid[0] / (fid[0] + fid[1]):.1f}% of {fid[0] + fid[1]} checklist items")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump([{"check": k, "name": n, "pass": ok, "detail": m} for k, n, ok, m in results], f, indent=1, ensure_ascii=False)
    return 0 if all(ok for _, _, ok, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())
