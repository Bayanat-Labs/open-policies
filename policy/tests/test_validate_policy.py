"""Tests for scripts/validate_policy.py: the real policy passes, and each kind of omission
the validator guards against makes it fail."""
import importlib.util
import os
import shutil

import pytest
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
POLICY = os.path.dirname(HERE)
spec = importlib.util.spec_from_file_location("validate_policy", os.path.join(POLICY, "scripts", "validate_policy.py"))
vp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vp)

with open(os.path.join(POLICY, "rubric.yaml"), encoding="utf-8") as _f:
    VERSION = str(yaml.safe_load(_f)["policy_version"])


def run(pdir, *extra):
    return vp.main(["--policy-dir", str(pdir), "-q", *extra])


@pytest.fixture
def copy(tmp_path):
    dst = tmp_path / "policy"
    shutil.copytree(POLICY, dst, ignore=shutil.ignore_patterns("tests", "__pycache__", ".pytest_cache"))
    return dst


def edit_yaml(path, fn):
    with open(path, encoding="utf-8") as f:
        d = yaml.safe_load(f)
    fn(d)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(d, f, sort_keys=False, allow_unicode=True)


def edit_text(path, old, new):
    txt = path.read_text(encoding="utf-8")
    assert old in txt, f"{old!r} not in {path.name}"
    path.write_text(txt.replace(old, new, 1), encoding="utf-8")


def test_real_policy_passes():
    assert run(POLICY) == 0


def test_changed_weight_fails(copy):
    edit_yaml(copy / "rubric.yaml", lambda d: d["criteria"][0].__setitem__("weight", 25))
    assert run(copy) == 1


def test_changed_anchor_fails(copy):
    edit_yaml(copy / "rubric.yaml", lambda d: d["criteria"][1]["anchors"].__setitem__("5", "Unique"))
    assert run(copy) == 1


def test_missing_tier_field_fails(copy):
    edit_yaml(copy / "tiers.yaml", lambda d: d["tiers"][1].__setitem__("publishes", "IDs and URLs only"))
    assert run(copy) == 1


def test_missing_licence_row_fails(copy):
    edit_yaml(copy / "licence-matrix.yaml", lambda d: d["output_licence_tags"]["rows"].pop(5))
    assert run(copy) == 1


def test_missing_allowlist_entry_fails(copy):
    edit_yaml(copy / "licence-matrix.yaml", lambda d: d["input_licences"]["allowlist"].pop(6))
    assert run(copy) == 1


def test_missing_principle_fails(copy):
    edit_yaml(copy / "principles.yaml", lambda d: d["principles"].pop(2))
    assert run(copy) == 1


def test_missing_index_only_trigger_fails(copy):
    edit_yaml(copy / "index-only-rules.yaml", lambda d: d["rules"].pop(3))
    assert run(copy) == 1


def test_missing_stop_rule_fails(copy):
    edit_text(copy / "stop-rules.md", "rotated within 30 days", "rotated eventually")
    assert run(copy) == 1


def test_missing_version_banner_fails(copy):
    edit_text(copy / "claims-rules.md", f"Version {VERSION} ·", "Version ·")
    assert run(copy) == 1


def test_draft_marker_fails(copy):
    edit_text(copy / "gating-exception.md", "Documentation, not legal advice.", "Documentation, not legal advice. DRAFT.")
    assert run(copy) == 1


def test_missing_arabic_banner_fails(copy):
    edit_text(copy / "POLICY.ar.md", "توثيق، وليس استشارة قانونية", "توثيق")
    assert run(copy) == 1


def test_arabic_policy_section_parity_fails(copy):
    edit_text(copy / "POLICY.ar.md", "## 7. ", "### 7. ")
    assert run(copy) == 1


def test_version_mismatch_fails(copy):
    edit_yaml(copy / "rubric.yaml", lambda d: d.__setitem__("policy_version", "9.9.9"))
    assert run(copy) == 1


def test_schema_error_in_tiers_fails(copy):
    edit_yaml(copy / "tiers.yaml", lambda d: d["tiers"][0].__setitem__("number", "one"))
    assert run(copy) == 1


def test_unknown_yaml_file_fails(copy):
    (copy / "extra.yaml").write_text("document: extra\n", encoding="utf-8")
    assert run(copy) == 1
