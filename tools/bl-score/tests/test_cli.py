"""CLI: example memos reproduce their expected JSON; errors exit 2 with clear text."""
import glob
import json
import os

import pytest

from bl_score.cli import main

from conftest import EXAMPLES

EXPECTED = sorted(glob.glob(os.path.join(EXAMPLES, "*.expected.json")))


@pytest.mark.parametrize("expected", EXPECTED, ids=[os.path.basename(p) for p in EXPECTED])
def test_example_memos(expected, capsys):
    memo = expected.replace(".expected.json", ".yaml")
    assert main([memo]) == 0
    got = json.loads(capsys.readouterr().out)
    with open(expected, encoding="utf-8") as f:
        assert got == json.load(f)


def test_examples_exist():
    names = {os.path.basename(p) for p in EXPECTED}
    assert {"green_p0.expected.json", "yellow_tier2.expected.json", "red_excluded.expected.json",
            "effort_blocks_p0.expected.json", "batch.expected.json"} <= names


def test_invalid_example_exit_2(capsys):
    rc = main([os.path.join(EXAMPLES, "invalid_memo.yaml")])
    err = capsys.readouterr().err
    assert rc == 2
    for line in ["unknown field(s) 'scroes_note'", "legal_tier: must be one of green, yellow, red (got 'amber')",
                 "scores: missing required field 'commercial_pull'", "scores.impact: must be an integer from 1 to 5 (got 6)",
                 "scores.ease: must be an integer from 1 to 5 (got 'high')"]:
        assert line in err


def test_batch_rank_uses_seo_tiebreak(capsys):
    assert main([os.path.join(EXAMPLES, "batch.yaml"), "--rank"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert [r["candidate_id"] for r in out] == ["EX-007", "EX-006"]
    assert out[0]["weighted_score_0_100"] == out[1]["weighted_score_0_100"]


def test_multiple_files_give_list(capsys):
    assert main([os.path.join(EXAMPLES, "green_p0.yaml"), os.path.join(EXAMPLES, "red_excluded.yaml"), "--compact"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert [r["legal_verdict"] for r in out] == ["tier1_eligible", "excluded"]


def test_weights_override_and_bad_weights(capsys):
    memo = os.path.join(EXAMPLES, "green_p0.yaml")
    assert main([memo, "--weights", "impact=40,claim_strength=20,ease=20,legal_cleanliness=10,commercial_pull=10"]) == 0
    assert json.loads(capsys.readouterr().out)["weights"]["impact"] == 40
    assert main([memo, "--weights", "impact=50"]) == 2
    assert "weights must name exactly" in capsys.readouterr().err


def test_check_only(capsys):
    assert main([os.path.join(EXAMPLES, "green_p0.yaml"), "--check"]) == 0
    assert capsys.readouterr().out == ""


def test_missing_file(capsys):
    assert main(["/nonexistent/memo.yaml"]) == 1
    assert "cannot read" in capsys.readouterr().err


def test_bad_yaml(tmp_path, capsys):
    p = tmp_path / "m.yaml"
    p.write_text("scores: [unclosed", encoding="utf-8")
    assert main([str(p)]) == 2
    assert "not valid YAML" in capsys.readouterr().err


def test_print_schema(capsys):
    assert main(["--print-schema", "memo"]) == 0
    s = json.loads(capsys.readouterr().out)
    assert s["required"] == ["candidate_id", "title", "scores", "legal_tier", "effort"]


def _readme_memo():
    """The memo YAML block under 'The memo format (input)' in README.md, exactly as documented."""
    import re
    from conftest import ROOT
    with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as f:
        text = f.read()
    section = text.split("## The memo format (input)", 1)[1]
    m = re.search(r"```yaml\n(.*?)```", section, re.S)
    assert m, "README memo example not found"
    return m.group(1)


def test_readme_example_memo_scores(tmp_path, capsys):
    # Regression: the README example has an unquoted scored_on date.
    block = _readme_memo()
    assert "scored_on: 2026-10-14" in block
    p = tmp_path / "readme_memo.yaml"
    p.write_text(block, encoding="utf-8")
    assert main([str(p)]) == 0, capsys.readouterr().err
    out = json.loads(capsys.readouterr().out)
    assert out["candidate_id"] == "EX-010"
    assert out["weighted_score_0_100"] == 77.5
    assert out["legal_verdict"] == "tier1_eligible" and out["suggested_priority"] == "P0"
    assert main([str(p), "--check"]) == 0
