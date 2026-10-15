"""Schema validation errors name the field and say what is wrong."""
import pytest

from bl_score import MemoError, score_memo, validate_memo


def errors(m):
    with pytest.raises(MemoError) as ei:
        validate_memo(m, source="memo.yaml")
    return ei.value.errors, str(ei.value)


def test_valid_memo_passes(base_memo):
    assert validate_memo(base_memo) is base_memo


def test_missing_field(base_memo):
    del base_memo["effort"]
    errs, text = errors(base_memo)
    assert errs == ["(top level): missing required field 'effort'"]
    assert text.startswith("memo.yaml: invalid memo:")


def test_missing_score(base_memo):
    del base_memo["scores"]["ease"]
    errs, _ = errors(base_memo)
    assert errs == ["scores: missing required field 'ease'"]


@pytest.mark.parametrize("bad", [0, 6, -1, 10])
def test_out_of_range(base_memo, bad):
    base_memo["scores"]["impact"] = bad
    errs, _ = errors(base_memo)
    assert errs == [f"scores.impact: must be an integer from 1 to 5 (got {bad!r})"]


@pytest.mark.parametrize("bad", [3.5, "3", True, None])
def test_wrong_type(base_memo, bad):
    base_memo["scores"]["ease"] = bad
    errs, _ = errors(base_memo)
    assert len(errs) == 1 and errs[0].startswith("scores.ease: must be an integer from 1 to 5")


def test_bad_enum(base_memo):
    base_memo["legal_tier"] = "amber"
    base_memo["effort"] = "XXL"
    errs, _ = errors(base_memo)
    assert "legal_tier: must be one of green, yellow, red (got 'amber')" in errs
    assert "effort: must be one of S, M, L, XL (got 'XXL')" in errs


def test_unknown_field_typo(base_memo):
    base_memo["scroes"] = {}
    errs, _ = errors(base_memo)
    assert len(errs) == 1 and "unknown field(s) 'scroes'" in errs[0] and "allowed:" in errs[0]


def test_unknown_criterion(base_memo):
    base_memo["scores"]["rights"] = 5
    errs, _ = errors(base_memo)
    assert len(errs) == 1 and errs[0].startswith("scores: unknown field(s) 'rights'")


def test_not_a_mapping():
    with pytest.raises(MemoError, match="must be a mapping"):
        validate_memo(["a", "b"])


def test_bad_date(base_memo):
    base_memo["scored_on"] = "14/10/2026"
    errs, _ = errors(base_memo)
    assert errs[0].startswith("scored_on: '14/10/2026' does not match the required format")


def test_score_memo_raises_on_invalid(base_memo):
    base_memo["scores"]["impact"] = 9
    with pytest.raises(MemoError):
        score_memo(base_memo)


def test_unquoted_yaml_date_is_accepted(base_memo):
    # Regression: YAML reads `scored_on: 2026-10-14` as a date.
    import datetime
    import yaml
    base_memo["scored_on"] = yaml.safe_load("d: 2026-10-14")["d"]
    assert isinstance(base_memo["scored_on"], datetime.date)
    assert validate_memo(base_memo)["scored_on"] == "2026-10-14"
    assert score_memo(base_memo)["weighted_score_0_100"] == 50  # scores without raising


def test_quoted_date_still_accepted(base_memo):
    base_memo["scored_on"] = "2026-10-14"
    assert validate_memo(base_memo)["scored_on"] == "2026-10-14"


def test_datetime_is_rejected_clearly(base_memo):
    import datetime
    base_memo["scored_on"] = datetime.datetime(2026, 10, 14, 9, 30)
    errs, _ = errors(base_memo)
    assert len(errs) == 1 and errs[0].startswith("scored_on: must be of type string")
