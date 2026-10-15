"""Scoring logic for bl-score.

weighted_score_0_100 = sum over criteria of weight x (score - 1) / 4, with weights in
percent summing to 100. The legal gate is applied separately: red -> excluded (no
priority), yellow -> tier2_only (release tier capped at 2), green -> tier1_eligible.
The more restrictive of the two readings applies (rubric.yaml legal_gate.score_overrides): a
legal_cleanliness score of 1 (red anchor) gives excluded and a score of 2 or 3 caps the release at Tier 2, whatever
legal_tier says (rubric.yaml legal_gate.score_overrides).
Suggested priority follows the ordered threshold rules in rubric.yaml.
"""
from __future__ import annotations

import copy
import datetime
import functools
import json
import math
from dataclasses import dataclass, field
from importlib import resources
from typing import Any, Mapping

import yaml
from jsonschema import Draft202012Validator

CRITERIA = ("impact", "claim_strength", "ease", "legal_cleanliness", "commercial_pull")
EFFORTS = ("S", "M", "L", "XL")
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
BORDERLINE_MARGIN = 2.5
VERDICT_RANK = {"tier1_eligible": 0, "tier2_only": 1, "excluded": 2}
VERDICT_MAX_TIER = {"tier1_eligible": 1, "tier2_only": 2, "excluded": None}
# Used when a rubric file has no legal_gate.score_overrides (the shipped rubric.yaml states the same rule).
DEFAULT_SCORE_OVERRIDES = ({"max_score": 1, "legal_verdict": "excluded"},
                           {"max_score": 3, "legal_verdict": "tier2_only"})


class MemoError(ValueError):
    """Raised when a memo does not match the memo schema. `errors` holds one clear line per problem."""

    def __init__(self, errors: list[str], source: str | None = None):
        self.errors = errors
        self.source = source
        prefix = f"{source}: " if source else ""
        super().__init__(prefix + "invalid memo:\n  " + "\n  ".join(errors))


class RubricError(ValueError):
    """Raised when a rubric file or a weight override is invalid."""


def _data(name: str) -> str:
    return resources.files("bl_score").joinpath("data", name).read_text(encoding="utf-8")


def memo_schema() -> dict:
    return json.loads(_data("memo.schema.json"))


@functools.lru_cache(maxsize=1)
def _memo_validator() -> Draft202012Validator:
    return Draft202012Validator(memo_schema())


@functools.lru_cache(maxsize=1)
def _default_rubric() -> "Rubric":
    return load_rubric()


def output_schema() -> dict:
    return json.loads(_data("output.schema.json"))


@dataclass
class Rubric:
    weights: dict[str, float]
    thresholds: list[dict[str, Any]]
    gate: dict[str, dict[str, Any]]
    policy_version: str
    thresholds_status: str
    anchors: dict[str, dict[str, str]] = field(default_factory=dict)
    score_overrides: list[dict[str, Any]] = field(default_factory=lambda: [dict(o) for o in DEFAULT_SCORE_OVERRIDES])

    def with_weights(self, weights: Mapping[str, float]) -> "Rubric":
        new = copy.deepcopy(self)
        new.weights = check_weights(weights)
        return new


def check_weights(weights: Mapping[str, float]) -> dict[str, float]:
    missing = [c for c in CRITERIA if c not in weights]
    extra = [k for k in weights if k not in CRITERIA]
    if missing or extra:
        raise RubricError(f"weights must name exactly {', '.join(CRITERIA)}; missing {missing}, unknown {extra}")
    w = {c: float(weights[c]) for c in CRITERIA}
    if any(v < 0 for v in w.values()):
        raise RubricError("weights must be non-negative")
    total = sum(w.values())
    if not math.isclose(total, 100.0, abs_tol=1e-6):
        raise RubricError(f"weights must sum to 100 (got {total:g})")
    return w


def load_rubric(path: str | None = None) -> Rubric:
    """Load rubric.yaml (the vendored copy by default) and validate it against its schema."""
    if path is None:
        text = _data("rubric.yaml")
    else:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    doc = yaml.safe_load(text)
    schema = json.loads(_data("rubric.schema.json"))
    errs = sorted(Draft202012Validator(schema).iter_errors(doc), key=lambda e: list(e.absolute_path))
    if errs:
        raise RubricError("rubric invalid: " + "; ".join(
            f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}" for e in errs[:5]))
    weights = check_weights({c["id"]: c["weight"] for c in doc["criteria"]})
    gate = {o["legal_tier"]: {"legal_verdict": o["legal_verdict"], "max_release_tier": o["max_release_tier"]}
            for o in doc["legal_gate"]["outcomes"]}
    overrides = doc["legal_gate"].get("score_overrides") or [dict(o) for o in DEFAULT_SCORE_OVERRIDES]
    return Rubric(weights=weights, thresholds=doc["priority_thresholds"]["rules"], gate=gate,
                  policy_version=str(doc["policy_version"]),
                  thresholds_status=doc["priority_thresholds"]["status"],
                  anchors={c["id"]: c["anchors"] for c in doc["criteria"]},
                  score_overrides=sorted(overrides, key=lambda o: o["max_score"]))


def _fmt_error(e) -> str:
    path = ".".join(str(p) for p in e.absolute_path)
    where = path or "(top level)"
    v = e.validator
    if v == "required":
        missing = e.message.split("'")[1] if "'" in e.message else e.message
        return f"{where}: missing required field '{missing}'"
    if v == "additionalProperties":
        allowed = sorted(e.schema.get("properties", {}).keys())
        unknown = sorted(set(e.instance) - set(allowed)) if isinstance(e.instance, dict) else []
        return f"{where}: unknown field(s) {', '.join(repr(u) for u in unknown)}; allowed: {', '.join(allowed)}"
    if v in ("minimum", "maximum") or (v == "type" and e.schema.get("type") == "integer" and "minimum" in e.schema):
        return f"{where}: must be an integer from 1 to 5 (got {e.instance!r})"
    if v == "type":
        return f"{where}: must be of type {e.schema.get('type')} (got {type(e.instance).__name__} {e.instance!r})"
    if v == "enum":
        return f"{where}: must be one of {', '.join(map(str, e.schema['enum']))} (got {e.instance!r})"
    if v == "pattern":
        return f"{where}: {e.instance!r} does not match the required format {e.schema['pattern']}"
    return f"{where}: {e.message}"


def _coerce_dates(memo: dict) -> dict:
    """YAML reads an unquoted 2026-10-14 as a date. Turn plain dates into ISO strings so that
    `scored_on: 2026-10-14` (as the README shows) and `scored_on: "2026-10-14"` are both accepted.
    Date-times are left alone and fail the YYYY-MM-DD check with a clear message."""
    dates = {k: v.isoformat() for k, v in memo.items() if type(v) is datetime.date}
    return {**memo, **dates} if dates else memo


def validate_memo(memo: Any, source: str | None = None) -> dict:
    """Validate a memo dict; raise MemoError with clear, path-named messages.
    Returns the memo with plain YAML dates turned into ISO strings."""
    if not isinstance(memo, dict):
        raise MemoError([f"(top level): a memo must be a mapping of fields, got {type(memo).__name__}"], source)
    memo = _coerce_dates(memo)
    errs = sorted(_memo_validator().iter_errors(memo), key=lambda e: [str(p) for p in e.absolute_path])
    if errs:
        raise MemoError([_fmt_error(e) for e in errs], source)
    return memo


def weighted_score(scores: Mapping[str, int], weights: Mapping[str, float]) -> float:
    return sum(weights[c] * (scores[c] - 1) / 4.0 for c in CRITERIA)


def suggest_priority(score: float, effort: str, rubric: Rubric) -> tuple[str, str]:
    for rule in rubric.thresholds:
        if score >= rule["min_weighted_score"] and ("effort_in" not in rule or effort in rule["effort_in"]):
            cond = f"score >= {rule['min_weighted_score']:g}"
            if "effort_in" in rule:
                cond += f" and effort in {'/'.join(rule['effort_in'])}"
            return rule["priority"], cond
    return "P3", "fallback"


def score_gate(tier: str, legal_cleanliness: int, rubric: Rubric) -> tuple[dict[str, Any], bool]:
    """Return the legal gate (legal_verdict, max_release_tier) and whether the score overrode legal_tier.
    The more restrictive of legal_tier and the legal_cleanliness score applies (rubric.yaml legal_gate.score_overrides)."""
    gate = dict(rubric.gate[tier])
    by_score = next((o["legal_verdict"] for o in rubric.score_overrides if legal_cleanliness <= o["max_score"]), None)
    if by_score is not None and VERDICT_RANK[by_score] > VERDICT_RANK[gate["legal_verdict"]]:
        return {"legal_verdict": by_score, "max_release_tier": VERDICT_MAX_TIER[by_score]}, True
    return gate, False


def score_memo(memo: Mapping[str, Any], rubric: Rubric | None = None, source: str | None = None) -> dict:
    """Score one memo. Returns the output dict described in output.schema.json."""
    memo = validate_memo(dict(memo), source)
    rubric = rubric or _default_rubric()
    s = memo["scores"]
    tier, effort = memo["legal_tier"], memo["effort"]
    raw = weighted_score(s, rubric.weights)
    ws = round(raw + 0.0, 2)
    warnings: list[str] = []
    lc = s["legal_cleanliness"]
    gate, by_score = score_gate(tier, lc, rubric)
    if gate["legal_verdict"] == "excluded":
        priority, rule = None, None
        if tier == "red":
            warnings.append("legal_tier red: excluded regardless of score (not built). Score a compliant alternative as its own candidate.")
            if lc > 1:
                warnings.append(f"legal_cleanliness is {lc} but legal_tier is red; the gate follows legal_tier.")
        else:
            warnings.append(f"legal_cleanliness is {lc} (red anchor: not built) but legal_tier is {tier}; excluded regardless of score, "
                            "because the more restrictive reading applies (rubric.yaml legal_gate.score_overrides). Correct the score or the legal tier before building.")
    else:
        priority, rule = suggest_priority(ws, effort, rubric)
        if tier == "yellow":
            warnings.append("legal_tier yellow: Tier 2 only (manifests and own annotations, no verbatim content); the scoping memo must name a collection basis.")
            if lc >= 4:
                warnings.append(f"legal_cleanliness is {lc} (green anchor) but legal_tier is yellow; the more restrictive legal_tier applies.")
        if by_score:
            warnings.append(f"legal_cleanliness is {lc} (at or below the yellow anchor) but legal_tier is {tier}; capped at Tier 2 only "
                            "(manifests and own annotations, no verbatim content) because the more restrictive reading applies (rubric.yaml legal_gate.score_overrides). "
                            "The scoping memo must name a collection basis.")
        p0 = next((r for r in rubric.thresholds if r["priority"] == "P0"), None)
        if p0 and ws >= p0["min_weighted_score"] and "effort_in" in p0 and effort not in p0["effort_in"]:
            warnings.append(f"score meets the P0 threshold ({p0['min_weighted_score']:g}) but effort is {effort}; P0 needs effort {'/'.join(p0['effort_in'])}, so the suggestion is {priority}.")
        for r in rubric.thresholds:
            t = r["min_weighted_score"]
            if t > 0 and 0 < abs(ws - t) <= BORDERLINE_MARGIN:
                warnings.append(f"borderline: score {ws:g} is within {BORDERLINE_MARGIN:g} points of the {r['priority']} threshold ({t:g}); the coordinator decides.")
    just = memo.get("justifications")
    if not just:
        warnings.append("no justifications recorded; add one line per score.")
    else:
        miss = [c for c in CRITERIA if not just.get(c)]
        if miss:
            warnings.append(f"no justification for: {', '.join(miss)}.")
    return {
        "candidate_id": memo["candidate_id"],
        "title": memo["title"],
        "scores": {c: s[c] for c in CRITERIA},
        "legal_tier": tier,
        "effort": effort,
        "weighted_score_0_100": ws,
        "legal_verdict": gate["legal_verdict"],
        "max_release_tier": gate["max_release_tier"],
        "suggested_priority": priority,
        "priority_rule": rule,
        "seo_demand": memo.get("seo_demand"),
        "warnings": warnings,
        "weights": {c: rubric.weights[c] for c in CRITERIA},
        "thresholds_status": rubric.thresholds_status,
        "policy_version": rubric.policy_version,
    }


def rank(results: list[dict]) -> list[dict]:
    """Order scored results: excluded last, then by weighted score, then seo_demand (tie-breaker), then id."""
    def key(r):
        return (r["legal_verdict"] == "excluded", -r["weighted_score_0_100"], -(r.get("seo_demand") or 0), r["candidate_id"])
    return sorted(results, key=key)
