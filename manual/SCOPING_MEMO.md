# Scoping memo: <canon_id> · Bayanat Labs <Name>

*Stage-0 template, operating manual v1.0.1. Sections 1-8 are the memo itself; sections 0, 9 and 10 add the machine files, the rubric and the budget. Text CC BY 4.0. Documentation, not legal advice.*

Stage 0 of the pipeline (`manual/stages.yaml` stage 0). Keep it to one page plus tables. Nothing is fetched until the coordinator approves this memo and `job.json` exists.

**Files.** Stage 0 produces four files in the job directory:

| File | What it is | Checked against |
|---|---|---|
| `scoping_memo.md` | This page, filled in | Coordinator reads it |
| `scoping_memo.score.yaml` | The rubric block, in the exact format of the `bl-score` CLI | `manual/scoping_memo.schema.json` (mirrors bl-score's own memo schema; unknown fields are errors) |
| `scoping_memo.score.json` | bl-score's output for that block, saved unchanged | Stage-0 gate reads `legal_verdict` |
| `scoping_memo.yaml` | The memo record: everything else the gates read (QA thresholds, tier, flags, budget, decision) | `manual/schemas/scoping_memo_record.schema.json` |

Where the page and the YAML files differ, fix them before asking for approval. `candidate_id` and `title` must be the same in all of them.

**Overrides.** This memo may tighten any default in `manual/stages.yaml`. It may loosen one only with written founder approval, recorded in section 10.

## 0. Machine files and the rubric score

**Step 1: the score block.** Write `scoping_memo.score.yaml` in bl-score's format (`tools/bl-score/README.md`). Keep to these fields only; bl-score rejects unknown fields.

```yaml
candidate_id: AB-001                     # required; same as the record
title: "Bayanat Labs <Name>"             # required; always starts with "Bayanat Labs"
one_line: "<one-line summary>"           # optional
scores:                                  # required; integers 1-5 against the anchors in section 9
  impact: 4
  claim_strength: 4
  ease: 4
  legal_cleanliness: 5
  commercial_pull: 3
legal_tier: green                        # required; green | yellow | red; drives the gate
effort: M                                # required; S | M | L | XL
justifications:                          # one line per score
  impact: "..."
  claim_strength: "..."
  ease: "..."
  legal_cleanliness: "..."
  commercial_pull: "..."
  legal_tier: "..."
  effort: "..."
seo_demand: 3                            # optional; tie-breaker only, never weighted
source_scores: {impact: 4}               # optional; original values the scores were mapped from
memo_ref: scoping_memo.md
scored_by: "<agent>"
scored_on: "2026-10-14"
notes: "..."                             # optional; free text
```

**Step 2: score it and keep the output.**

```bash
python scripts/pin_bl_score.py <bl-score checkout> --check manual/bl-score.pin.json   # prints the tree hash; exit 1 on drift
bl-score scoping_memo.score.yaml > scoping_memo.score.json    # exit 2 means the block is invalid
python scripts/validate_stages.py manual/stages.yaml --evaluate --job <job dir> --stages 0
```

The legal gate applies the more restrictive of the legal tier and the legal-cleanliness score (`legal_gate.score_overrides` in `policy/rubric.yaml`). A red tier or a score of 1 returns `excluded` whatever the total, and the job stops. A yellow tier or a score of 2-3 returns `tier2_only`: the release is capped at Tier 2 even if the tier says green, and bl-score adds a warning. bl-score's suggested priority is a proposal; the coordinator decides.

**Pin.** bl-score is pinned by the hash of its code, not by its version string: its scoring and its date handling changed while the version stayed 0.1.0. Run the scorer whose tree hash matches `manual/bl-score.pin.json` and copy that hash into the memo record as `score_tool_sha256`; the stage-0 check `S0.score_tool_pinned` compares it with the pinned value. bl-score accepts `scored_on` quoted or unquoted (it converts a plain YAML date to an ISO string); quoting it is still the safer habit for other tools.

**Step 3: the memo record.** Fill `scoping_memo.yaml`. The gates of later stages read `memo:` values from it (for example `qa.agreement_threshold` at stage 7).

```yaml
schema_version: 1
manual_version: "1.0.1"
candidate_id: AB-001                     # same as the score block
title: "Bayanat Labs <Name>"
score_file: scoping_memo.score.yaml
priority: P0                             # coordinator decides; bl-score only suggests
merged_ext_ids: []                       # related candidate IDs, if any
name_collision_checked: true
product_link: {family: Knowledge, page: null}
claim_to_make: {wording: "No comparative claim", comparative: false, claim_ids: [], first_or_only_search_log: null}
incumbents:
  - {name: "...", size: 0, unit: "...", licence: "...", url: "https://...", checked_at: "2026-10-14"}
sources:
  - {source_id: SRC01, url: "https://...", licence: "cc-by-4.0", tos_basis: open-license, terms_read_on: "2026-10-14",
     licence_route: IN-A02,              # input-licence ID in policy/licence-matrix.yaml; null for Bayanat Labs' own content
     release_tier: tier1_open_content,   # the tier this source's content may reach
     decision_ref: null,                 # ID of the recorded decision a legal position rests on; never free text
     open_issue: null}
release_tier: tier1_open_content          # tier1_open_content | tier2_manifests_annotations | tier3_partner_licensed
release_mode: redistributable
collection_basis_tier2: {basis: not_applicable, reference: null}   # required and not "not_applicable" for Tier 2
licence_plan:
  - {config: default, licence: cc-by-4.0, content: "Bayanat Labs annotations"}
profile: P-TXT                           # P-TXT | P-SPEECH | P-DOC | P-SYN | P-EVAL
modalities: [text]
uses_video_host: false
video_media_download: false              # true only for Creative Commons video whose download a recorded decision permits (check S2.media_download_decision)
media_download_decision_ref: null        # ID of that recorded decision; required when video_media_download is true
consented_audio: false
has_images: false
uses_llm_suggestions: false
third_party_sources: true                # false only if every source is Bayanat Labs' own content (then tos_basis synthetic or consented)
unit_of_independence: document
baseline: {task: "retrieval", metric: "nDCG@10", script: "eval/baseline.py"}
qa:
  sample_size: 1000
  sample_unit: records
  agreement_metric: kappa
  agreement_threshold: 0.6               # floor 0.6; 0.7 for eval sets; may only go up
  is_eval_set: false
  pii_audit_records: 3000                # minimum 3,000
  native_reviewers: [{name: null, dialects: [Najdi]}]
ranges:                                  # stage-4 gate compares the dedup report with these; tighten only
  duplicate_rate_max: 0.05
  langid_min_share: 0.95
  expected_languages: [ar]
budget: {estimator: "manual/budget.py <version, or its SHA-256 while it has no version string>", gpu_hours: null, gpu_type: null, rate_usd_per_gpu_hour: null, compute_cost_usd: null, human_qa_hours: null, agent_days: null}
owner: {agent: "...", coordinator: "..."}
dates: {memo_date: "2026-10-14", target_release: "2026-10-28", calendar_anchor: null, next_version_date: null}
risks:
  - {risk: "terms change", likelihood: L, mitigation: "...", stop_rule: "convert to Tier 2 or drop; never delay indefinitely"}
stop_conditions: ["legal tier turns red", "PII hit in the audit"]
deviations: []                           # see section 10
founder_actions: []                      # founder-only actions this job needs, one line each
decision:
  coordinator: {name: null, date: null, verdict: pending}   # pending | approve | revise | reject
  legal_tier_assigned: false
  conflicts_noted: []
score_tool_sha256: "<tree hash printed by scripts/pin_bl_score.py>"
```

Quote every date (`"2026-10-14"`): unquoted YAML dates become date objects and fail the schema in strict tools.

| Field | Value |
|---|---|
| Candidate ID / related IDs | <AB-001> / <related candidate IDs> |
| Working title (always "Bayanat Labs …"); name-collision check done? | <…> / <yes: HF, GitHub, PyPI, Masader searched> |
| Product family link | <Align · Voice · Agents · Documents · Search · Knowledge · Bench · Vision · Voice Studio> → <page> |
| Priority / effort | <P0–P3> / <S, M, L, XL> |
| Owner agent / coordinator | <…> / <…> |
| Target release date | <YYYY-MM-DD> (calendar anchor: <e.g. 18 Dec 2026 World Arabic Language Day>) |

## 1. What and why
<2–4 sentences: the user job, the gap (with an evidence URL), and why Bayanat Labs should build it.>

## 2. Claim to make (draft; final wording only through CLAIMS.md)
<"Largest openly licensed … as of …" or "No comparative claim">

| Incumbent | Size | Licence / access | URL | Verified on |
|---|---|---|---|---|
| <…> | <…> | <…> | <…> | <YYYY-MM-DD> |

"First" or "only" claims need a saved search of Hugging Face, Masader, Kaggle, Zenodo, ACL Anthology and arXiv: <link to search log>.

## 3. Sources, licences and release tiers

| Source ID | Source / URL | Licence | Licence route (`licence_route`) | Release tier (`release_tier`) | Named basis (`tos_basis`) | Terms read on | Open issue |
|---|---|---|---|---|---|---|---|
| <SRC01> | <…> | <…> | <IN-A01 … IN-B04> | <tier 1 / 2 / 3> | <…> | <YYYY-MM-DD> | <…> |

- Items whose licence or terms do not allow the planned release: <list>. Compliant alternative for each: <IDs only / consented / openly licensed alternative>.
- Legal positions relied on, by decision ID only (`decision_ref`): <…>.
- Items whose release needs a recorded legal decision, and the decision each one rests on (no decision: the item ships at Tier 2 or is dropped): <items>. Permission requests to draft: <items>.
- Tier 2 only: named collection basis (academic partner collecting under EU DSM Art. 3/4, written rights-holder permission, or a recorded decision that permits it): <basis + reference>. Until one exists, scale stays capped at the pilot.
- Tier 3 only: the partner's written permission is on file before collection, and its reference goes in `permission_doc_id` on every row: <permission reference>. No permission on file, no fetch (`policy/tiers.yaml` Tier 3).
- Creative Commons video downloads, if any: the recorded decision the download relies on (`media_download_decision_ref`, check `S2.media_download_decision`) and the residual terms-of-service risk: <…>.

## 4. Release plan
| Item | Plan |
|---|---|
| Tier / release mode | <Tier 1 redistributable · Tier 2 metadata_or_recipe_only · …> |
| Configs and licences (`policy/licence-matrix.yaml`) | <config → licence> |
| Formats and expected size | <Parquet shards ≤ 500 MB; N GB; host limits checked> |
| Unit of independence for splits | <source, work, speaker, channel, template> |
| Baseline or benchmark number | <task, metric, script> |
| Homes | HF `Bayanat-Labs/<slug>` · GitHub `Bayanat-Labs/<slug>` · `bayanatlabs.com/open/<slug>` · Zenodo · Masader · Kaggle |

## 5. Processing and QA
| Item | Plan |
|---|---|
| Profile | <P-TXT / P-SPEECH / P-DOC / P-SYN / P-EVAL> plus deviations (stricter only) |
| PII and re-identification risks | <UGC? voices? judgments? faces? minors?> → tests R1–R7 |
| QA sample sizes | <1,000 per subset; 3,000 PII audit; speech max(2%, 2 h); synthetic ≥ 5% (≥ 10% eval)> |
| Agreement threshold | <κ ≥ 0.6 / ≥ 0.7 eval, or stricter> |
| Named native reviewer(s) and dialects covered | <…> |
| Pilot | <probe 10–100 records, then a pilot of N> |

## 6. Effort, cost and dependencies
- Agent effort: <agent-days>. Compute: <GPU h; $ estimate>. Human QA: <person-days; $ estimate>.
- Estimates come from `manual/budget.py`. Human QA is always the expensive step, so the sample sizes in section 5 are fixed here, up front.
- Founder actions required: <permission from …; budget …; publication go>.
- Blocking dependencies: <in-Kingdom host; partner letter; consent form>.

## 7. Risks and stop rules
| Risk | Likelihood | Mitigation | Stop rule |
|---|---|---|---|
| <terms change / takedown / PII residue / weak yield> | <L, M, H> | <…> | <convert to Tier 2 or drop; never delay indefinitely> |

Standing stop rules: `manual/stop_rules.md`. Stage-specific ones: `manual/stages.yaml`.

## 8. Decision
- Coordinator: <approve / revise / reject> · <name> · <YYYY-MM-DD>
- Legal tier assigned (`decision.legal_tier_assigned`): <green / yellow> · Conflicts between rules noted (`decision.conflicts_noted`): <none / list>

## 9. Selection rubric

Score each criterion 1-5 against the anchors (2 and 4 sit between anchors). bl-score computes `weighted_score_0_100 = Σ weight × (score − 1) / 4` with weights in percent. Legal cleanliness is a **gate**: whatever the total, a red tier or a legal-cleanliness score of 1 is not built, and a yellow tier or a score of 2-3 ships as Tier 2 at most. The anchors below follow `policy/rubric.yaml`; if the two ever differ, `policy/rubric.yaml` applies.

| Criterion | Weight | 1 | 3 | 5 | Score | One-line reason |
|---|---|---|---|---|---|---|
| Impact (citations, press, developer use) | 30 | Nobody searches for it; no downstream use | Useful to Arabic NLP researchers | Used by model labs, cited by press and AI assistants, pulled by leaderboards | <1-5> | <…> |
| Claim strength | 20 | Many equivalents exist | Better than incumbents on one axis | No credible incumbent for a precise "first/largest" claim | <1-5> | <…> |
| Ease | 20 | Needs humans at scale or partner consent | Agent-buildable with some human QA | Agent-buildable from dumps/APIs in days | <1-5> | <…> |
| Legal cleanliness (gate) | 20 | Red legal tier: not built | Yellow: manifests and our own annotations only | Green: full content redistributable under an open licence | <1-5> | <…> |
| Commercial pull | 10 | No product link | Feeds one service page | Feeds a product family and a sales conversation (Voice, Search, Bench, Documents, Agents) | <1-5> | <…> |

| bl-score output | Value |
|---|---|
| weighted_score_0_100 | <…> |
| legal_verdict | <tier1_eligible / tier2_only / excluded> |
| suggested_priority (the coordinator decides) | <P0-P3> |
| warnings | <…> |
| policy version | <…> |

Codes: **P0** ships within 60 days; **P1** by LEAP (12 Apr 2027); **P2** within year one; **P3** opportunistic. **S** under one agent-week; **M** 1-4 agent-weeks; **L** 1-3 agent-months; **XL** longer, or needs a partner.

## 10. Budget, deviations and stop conditions

| Item | Value |
|---|---|
| Estimator and version | `manual/budget.py` <version, or its SHA-256 while it has no version string> |
| GPU-hours / GPU type / rate | <…> |
| Human QA hours | <…> |
| Agent-days | <…> |

| Threshold id (stages.yaml) | Default | This memo | Tighter or looser | Founder approval (required if looser) |
|---|---|---|---|---|
| <T7.speech_sample> | <max(2%, 2 h) per subset> | <…> | <tighter> | <ref or n/a> |

Stop conditions for this job (in addition to `manual/stop_rules.md`): <list>.
