"""Rubric: weights sum to 100, one gate, vendored copy matches the policy file."""
import hashlib
import os

import pytest

from bl_score import CRITERIA, RubricError, check_weights, load_rubric

from conftest import ROOT

# The policy files are in policy/ of the open-policies repository (public/ in a build tree); this package
# ships a copy of policy/rubric.yaml.
_BASE = os.path.abspath(os.path.join(ROOT, "..", ".."))
_POLICY = os.path.join(_BASE, "public") if os.path.isdir(os.path.join(_BASE, "public")) else os.path.join(_BASE, "policy")
POLICY_RUBRIC = os.path.join(_POLICY, "rubric.yaml")
POLICY_SCHEMA = os.path.join(_POLICY, "schemas", "rubric.schema.json")
VENDORED = os.path.join(ROOT, "src", "bl_score", "data")


def test_weights_sum_to_100():
    r = load_rubric()
    assert sum(r.weights.values()) == 100


def test_weights_are_30_20_20_20_10():
    r = load_rubric()
    assert r.weights == {"impact": 30, "claim_strength": 20, "ease": 20, "legal_cleanliness": 20, "commercial_pull": 10}


def test_all_five_criteria_have_1_3_5_anchors():
    r = load_rubric()
    assert set(r.anchors) == set(CRITERIA)
    for c in CRITERIA:
        assert set(r.anchors[c]) == {"1", "3", "5"}


def test_gate_semantics_loaded():
    r = load_rubric()
    assert r.gate == {"red": {"legal_verdict": "excluded", "max_release_tier": None},
                      "yellow": {"legal_verdict": "tier2_only", "max_release_tier": 2},
                      "green": {"legal_verdict": "tier1_eligible", "max_release_tier": 1}}


def test_bad_weight_override_rejected():
    with pytest.raises(RubricError, match="sum to 100"):
        check_weights({"impact": 40, "claim_strength": 20, "ease": 20, "legal_cleanliness": 20, "commercial_pull": 10})
    with pytest.raises(RubricError, match="exactly"):
        check_weights({"impact": 100})


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def rubric_content(p):
    """The rubric without its version label, so a policy release that leaves the rubric unchanged does
    not need a new copy here."""
    import yaml
    with open(p, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    doc.pop("policy_version", None)
    return doc


@pytest.mark.skipif(not os.path.exists(POLICY_RUBRIC), reason="not inside the open-policies repository")
def test_vendored_rubric_matches_policy():
    assert rubric_content(os.path.join(VENDORED, "rubric.yaml")) == rubric_content(POLICY_RUBRIC), \
        "copy policy/rubric.yaml to tools/bl-score/src/bl_score/data/rubric.yaml"
    assert sha(os.path.join(VENDORED, "rubric.schema.json")) == sha(POLICY_SCHEMA)


def test_custom_rubric_file_validated(tmp_path):
    p = tmp_path / "rubric.yaml"
    p.write_text("policy_version: '0.1'\ndocument: rubric\n", encoding="utf-8")
    with pytest.raises(RubricError, match="rubric invalid"):
        load_rubric(str(p))
