# bl-score

**Bayanat Labs open-programme scoring CLI.** It reads a scoping memo's score block (YAML) and prints the weighted score, the legal gate verdict, the release-tier cap and a suggested priority, using the selection rubric in [`policy/rubric.yaml`](../../policy/rubric.yaml).

> Part of the Bayanat Labs open-programme policy, version 1.0.1 (reviewed by counsel, October 2026). It ships the policy 1.0.1 rubric, so its output reports `policy_version` 1.0.1. The priority thresholds are adopted for v1.0 and provisional; the coordinator decides each case. Documentation, not legal advice.

- Licence: Apache-2.0 (code). The rubric text it ships is CC BY 4.0.
- Python 3.11 or later. Dependencies: `pyyaml`, `jsonschema`.

## Install

```bash
pip install ./tools/bl-score            # from a checkout of Bayanat-Labs/open-policies
pip install "./tools/bl-score[test]"    # with pytest
```

## Use

```bash
bl-score memo.yaml                      # one memo -> one JSON object
bl-score a.yaml b.yaml --rank           # several memos -> JSON list, best first
bl-score memos.yaml                     # a YAML list of memos -> JSON list
bl-score memo.yaml --check              # validate only (exit 0 or 2)
bl-score memo.yaml --weights impact=40,claim_strength=20,ease=20,legal_cleanliness=10,commercial_pull=10
bl-score --print-schema memo            # the memo JSON Schema
python -m bl_score memo.yaml            # same as bl-score
```

Exit codes: `0` scored; `2` a memo, the rubric or a weight override is invalid (one clear line per problem on stderr); `1` a file could not be read.

## The memo format (input)

This is the format Bayanat Labs scoping memos use. Each scoping memo (`scoping_memo.md`) keeps its score block in a companion file, `scoping_memo.score.yaml`, next to it. The JSON Schema is `src/bl_score/data/memo.schema.json`.

```yaml
candidate_id: EX-010                  # required. Canonical id (letters, digits, . _ : -)
title: "Bayanat Labs Saudi Laws"      # required. Working title, always "Bayanat Labs ..."
one_line: "Article-level corpus of Saudi laws"   # optional
scores:                               # required. Five integers, 1 to 5, using the 1/3/5 anchors
  impact: 4                           # Impact (citations, press, developer use), weight 30
  claim_strength: 4                   # Claim strength, weight 20
  ease: 4                             # Ease, weight 20
  legal_cleanliness: 5                # Legal cleanliness (gate), weight 20
  commercial_pull: 3                  # Commercial pull, weight 10
legal_tier: green                     # required. green | yellow | red (the legal tier)
effort: M                             # required. S | M | L | XL
justifications:                       # optional but expected: one line per score
  impact: "..."
  claim_strength: "..."
  ease: "..."
  legal_cleanliness: "..."
  commercial_pull: "..."
  legal_tier: "..."                   # optional
  effort: "..."                       # optional
seo_demand: 3                         # optional, 1-5. Tie-breaker only, never weighted
source_scores: {impact: 4}            # optional. Original values the scores were mapped from
memo_ref: scoping/ex-010/scoping_memo.md     # optional
scored_by: "agent name"               # optional
scored_on: 2026-10-14                 # optional, YYYY-MM-DD (quoted or unquoted)
notes: "..."                          # optional
```

Rules:

- **Scores are integers 1 to 5.** The rubric anchors 1, 3 and 5; use 2 or 4 between them. The anchors are in `policy/rubric.yaml` and in the table below.
- **The more cautious reading decides.** `legal_tier` drives the gate, but a `legal_cleanliness` score of 1 (the red anchor, "not built") gives `excluded`, and a score of 2 or 3 caps the release at Tier 2 (`tier2_only`), whatever `legal_tier` says. A score of 4 or 5 never loosens a yellow or red `legal_tier`. bl-score prints a warning whenever the two disagree (`rubric.yaml` `legal_gate.score_overrides`).
- **Dates.** `scored_on` may be written `2026-10-14` or `"2026-10-14"`; YAML reads the unquoted form as a date and bl-score turns it back into the ISO string. A date with a time is an error.
- **Unknown fields are errors.** A typo such as `scroes` is reported, not ignored.
- **Starting from another scoring scale?** Map its scores onto the five criteria first, for example: impact → impact, differentiation → claim_strength, ease → ease, rights → legal_cleanliness, buyer_fit → commercial_pull, seo_demand → seo_demand; `legal_risk.level` → legal_tier; `effort.full_agent_days` → effort (under 5 days S, 5-20 M, 21-60 L, over 60 XL). Record the originals under `source_scores`.

| Criterion | Weight | 1 | 3 | 5 |
|---|---|---|---|---|
| impact | 30 | Nobody searches for it; no downstream use | Useful to Arabic NLP researchers | Used by model labs, cited by press and AI assistants, pulled by leaderboards |
| claim_strength | 20 | Many equivalents exist | Better than incumbents on one axis | No credible incumbent for a precise "first/largest" claim |
| ease | 20 | Needs humans at scale or partner consent | Agent-buildable with some human QA | Agent-buildable from dumps/APIs in days |
| legal_cleanliness (gate) | 20 | Red legal tier: not built | Yellow: manifests and our own annotations only | Green: full content redistributable under an open licence |
| commercial_pull | 10 | No product link | Feeds one service page | Feeds a product family and a sales conversation (Voice, Search, Bench, Documents, Agents) |

## The output

```json
{
  "candidate_id": "EX-001",
  "title": "Bayanat Labs example corpus of official documents (illustrative)",
  "scores": {"impact": 5, "claim_strength": 4, "ease": 5, "legal_cleanliness": 5, "commercial_pull": 4},
  "legal_tier": "green",
  "effort": "S",
  "weighted_score_0_100": 92.5,
  "legal_verdict": "tier1_eligible",
  "max_release_tier": 1,
  "suggested_priority": "P0",
  "priority_rule": "score >= 75 and effort in S/M",
  "seo_demand": 4,
  "warnings": [],
  "weights": {"impact": 30.0, "claim_strength": 20.0, "ease": 20.0, "legal_cleanliness": 20.0, "commercial_pull": 10.0},
  "thresholds_status": "Adopted for v1.0, provisional. The coordinator decides each case.",
  "policy_version": "1.0.1"
}
```

| Field | Meaning |
|---|---|
| `weighted_score_0_100` | Σ weight × (score − 1) / 4 with weights in percent: all 1s give 0, all 5s give 100 |
| `legal_verdict` | `excluded` (red, or `legal_cleanliness` 1: not built, regardless of score), `tier2_only` (yellow, or `legal_cleanliness` 2-3: manifests and own annotations only), `tier1_eligible` (green with `legal_cleanliness` 4-5) |
| `max_release_tier` | `null` when excluded, `2` for `tier2_only`, `1` for `tier1_eligible` |
| `suggested_priority` | First matching rule: score ≥ 75 and effort S or M → P0; ≥ 60 → P1; ≥ 45 → P2; else P3. `null` when excluded |
| `warnings` | Gate notes, score/tier disagreements, P0 blocked by effort, borderline scores (within 2.5 points of a threshold), missing justifications |
| `policy_version` | Version of the rubric used |

## Tests

```bash
pytest tools/bl-score
```

The tests check that the weights sum to 100, red is always excluded, yellow always caps at Tier 2, a `legal_cleanliness` of 1 is excluded and 2-3 caps at Tier 2 whatever the tier, the README memo example above scores as documented, the score, the legal verdict and the priority never get worse when any one criterion goes up (all 3,125 score combinations, every effort code), schema errors name the field and the problem, and every example in `examples/` reproduces its `.expected.json`. When run inside the repository, a test also checks that the vendored `src/bl_score/data/rubric.yaml` (apart from its version label) and its schema match `policy/rubric.yaml` and `policy/schemas/rubric.schema.json`; after editing the rubric, copy them across.

## Examples

| File | Shows |
|---|---|
| `examples/green_p0.yaml` | Green, score 92.5, effort S → P0 |
| `examples/yellow_tier2.yaml` | Yellow → `tier2_only`, release tier capped at 2 |
| `examples/red_excluded.yaml` | Red with top scores → `excluded`, no priority |
| `examples/effort_blocks_p0.yaml` | Score 90 but effort L → P1 with a warning |
| `examples/batch.yaml` | A YAML list; equal scores ordered by `seo_demand` with `--rank` |
| `examples/invalid_memo.yaml` | Every kind of error message (exit 2) |

All examples are illustrative, not scoring decisions for real candidates.
