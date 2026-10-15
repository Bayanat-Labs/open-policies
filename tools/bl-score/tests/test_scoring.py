"""Scoring: formula, legal gate, priority thresholds, monotonicity."""
import itertools

import pytest

from bl_score import CRITERIA, EFFORTS, load_rubric, score_memo, weighted_score

R = load_rubric()
PRANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, None: 4}   # None = excluded, the worst outcome
VRANK = {"tier1_eligible": 0, "tier2_only": 1, "excluded": 2}
LC = CRITERIA.index("legal_cleanliness")


def expected_verdict(tier, lc):
    """The more restrictive of legal_tier and the legal_cleanliness score (rubric.yaml legal_gate.score_overrides)."""
    by_tier = {"red": "excluded", "yellow": "tier2_only", "green": "tier1_eligible"}[tier]
    by_score = "excluded" if lc == 1 else "tier2_only" if lc <= 3 else "tier1_eligible"
    return max(by_tier, by_score, key=VRANK.get)


def memo(scores, tier="green", effort="M"):
    return {"candidate_id": "T", "title": "Bayanat Labs t", "scores": dict(zip(CRITERIA, scores)),
            "legal_tier": tier, "effort": effort}


ALL = list(itertools.product(range(1, 6), repeat=5))


def test_formula_extremes():
    assert score_memo(memo((1, 1, 1, 1, 1)))["weighted_score_0_100"] == 0
    assert score_memo(memo((5, 5, 5, 5, 5)))["weighted_score_0_100"] == 100
    assert score_memo(memo((3, 3, 3, 3, 3)))["weighted_score_0_100"] == 50


def test_formula_by_hand():
    # 30*(4/4) + 20*(3/4) + 20*(4/4) + 20*(4/4) + 10*(3/4) = 92.5
    assert score_memo(memo((5, 4, 5, 5, 4)))["weighted_score_0_100"] == 92.5


@pytest.mark.parametrize("effort", EFFORTS)
def test_red_always_excluded(effort):
    for s in ALL:
        out = score_memo(memo(s, "red", effort))
        assert out["legal_verdict"] == "excluded"
        assert out["suggested_priority"] is None
        assert out["max_release_tier"] is None


@pytest.mark.parametrize("effort", EFFORTS)
def test_yellow_caps_at_tier_2(effort):
    for s in ALL:
        out = score_memo(memo(s, "yellow", effort))
        if s[LC] == 1:   # red anchor: excluded whatever legal_tier says
            assert out["legal_verdict"] == "excluded" and out["max_release_tier"] is None
        else:
            assert out["legal_verdict"] == "tier2_only"
            assert out["max_release_tier"] == 2


def test_green_is_tier1_eligible():
    for s in ALL[::7]:
        out = score_memo(memo(s, "green"))
        if s[LC] >= 4:
            assert out["legal_verdict"] == "tier1_eligible" and out["max_release_tier"] == 1
        else:   # the more restrictive score applies
            assert out["legal_verdict"] == expected_verdict("green", s[LC])


@pytest.mark.parametrize("tier", ["green", "yellow", "red"])
def test_more_restrictive_reading_applies_everywhere(tier):
    for s in ALL:
        out = score_memo(memo(s, tier))
        assert out["legal_verdict"] == expected_verdict(tier, s[LC]), (s, tier)
        if out["legal_verdict"] == "excluded":
            assert out["suggested_priority"] is None and out["max_release_tier"] is None


@pytest.mark.parametrize("tier", ["green", "yellow"])
def test_legal_cleanliness_1_is_excluded_whatever_the_tier(tier):
    # Review gap S4: score 1 with legal_tier green used to give tier1_eligible and P0 with only a warning.
    out = score_memo(memo((5, 5, 5, 1, 5), tier, "S"))
    assert out["legal_verdict"] == "excluded"
    assert out["max_release_tier"] is None
    assert out["suggested_priority"] is None and out["priority_rule"] is None
    assert any("excluded regardless of score" in w and "more restrictive reading applies" in w for w in out["warnings"])


@pytest.mark.parametrize("lc", [2, 3])
def test_score_at_or_below_yellow_anchor_caps_green_at_tier_2(lc):
    out = score_memo(memo((5, 5, 5, lc, 5), "green", "S"))
    assert out["legal_verdict"] == "tier2_only" and out["max_release_tier"] == 2
    assert out["suggested_priority"] is not None
    assert any("capped at Tier 2 only" in w for w in out["warnings"])


def test_score_4_or_5_leaves_legal_tier_in_charge():
    for lc in (4, 5):
        assert score_memo(memo((5, 5, 5, lc, 5), "green"))["legal_verdict"] == "tier1_eligible"
        assert score_memo(memo((5, 5, 5, lc, 5), "yellow"))["legal_verdict"] == "tier2_only"
        assert score_memo(memo((5, 5, 5, lc, 5), "red"))["legal_verdict"] == "excluded"


@pytest.mark.parametrize("score,effort,expected", [
    ((5, 5, 5, 5, 5), "S", "P0"), ((5, 5, 5, 5, 5), "M", "P0"),
    ((5, 5, 5, 5, 5), "L", "P1"), ((5, 5, 5, 5, 5), "XL", "P1"),
    ((5, 3, 4, 4, 3), "M", "P0"),   # 30+10+15+15+5 = 75 -> P0 (inclusive)
    ((4, 3, 3, 3, 3), "M", "P2"),   # 22.5+10+10+10+5 = 57.5
    ((3, 3, 3, 3, 3), "M", "P2"),   # 50
    ((2, 2, 3, 3, 3), "M", "P3"),   # 7.5+5+10+10+5 = 37.5
])
def test_priority_thresholds(score, effort, expected):
    out = score_memo(memo(score, "green", effort))
    assert out["suggested_priority"] == expected


def test_threshold_boundaries_inclusive():
    # exactly 75 (effort S) -> P0, exactly 60 -> P1, exactly 45 -> P2
    found = {}
    for s in ALL:
        ws = weighted_score(dict(zip(CRITERIA, s)), R.weights)
        for t in (75, 60, 45):
            if abs(ws - t) < 1e-9:
                found.setdefault(t, s)
    assert set(found) == {75, 60, 45}
    assert score_memo(memo(found[75], effort="S"))["suggested_priority"] == "P0"
    assert score_memo(memo(found[60]))["suggested_priority"] == "P1"
    assert score_memo(memo(found[45]))["suggested_priority"] == "P2"


@pytest.mark.parametrize("tier", ["green", "yellow"])
@pytest.mark.parametrize("effort", EFFORTS)
def test_monotonic_in_every_criterion(tier, effort):
    res = {s: score_memo(memo(s, tier, effort)) for s in ALL}
    for s, base in res.items():
        for i, c in enumerate(CRITERIA):
            if s[i] == 5:
                continue
            up = list(s)
            up[i] += 1
            nxt = res[tuple(up)]
            assert nxt["weighted_score_0_100"] >= base["weighted_score_0_100"], (s, c)
            assert PRANK[nxt["suggested_priority"]] <= PRANK[base["suggested_priority"]], (s, c)
            assert VRANK[nxt["legal_verdict"]] <= VRANK[base["legal_verdict"]], (s, c)


def test_strictly_increasing_when_weight_positive():
    for c in CRITERIA:
        lo = score_memo(memo(tuple(1 if x != c else 1 for x in CRITERIA)))["weighted_score_0_100"]
        hi = score_memo(memo(tuple(1 if x != c else 5 for x in CRITERIA)))["weighted_score_0_100"]
        assert hi - lo == pytest.approx(R.weights[c])


def test_effort_never_improves_priority():
    order = ["S", "M", "L", "XL"]
    for s in ALL[::3]:
        ranks = [PRANK[score_memo(memo(s, "green", e))["suggested_priority"]] for e in order]
        assert ranks == sorted(ranks)


def test_weight_override_changes_score():
    r2 = R.with_weights({"impact": 40, "claim_strength": 20, "ease": 20, "legal_cleanliness": 10, "commercial_pull": 10})
    out = score_memo(memo((5, 1, 1, 1, 1)), r2)
    assert out["weighted_score_0_100"] == 40
    assert out["weights"]["impact"] == 40


def test_warnings():
    out = score_memo(memo((5, 5, 5, 5, 5), "yellow"))
    assert any("Tier 2 only" in w for w in out["warnings"])
    assert any("more restrictive legal_tier" in w for w in out["warnings"])
    out = score_memo(memo((5, 5, 5, 3, 5), "red"))
    assert any("excluded regardless of score" in w for w in out["warnings"])
    assert any("gate follows legal_tier" in w for w in out["warnings"])
    out = score_memo(memo((5, 5, 3, 5, 5), "green", "XL"))
    assert any("P0 needs effort S/M" in w for w in out["warnings"])
    out = score_memo(memo((3, 3, 3, 3, 3), "green"))
    assert any("no justifications" in w for w in out["warnings"])


def test_output_matches_output_schema():
    from jsonschema import Draft202012Validator
    from bl_score import output_schema
    v = Draft202012Validator(output_schema())
    for s in ALL[::50]:
        for tier in ("green", "yellow", "red"):
            assert not list(v.iter_errors(score_memo(memo(s, tier))))
