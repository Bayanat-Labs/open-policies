# Maintenance calendar (stage 12)

*Operating manual v1.0.1 · Approved by the founder on 15 Oct 2026 · Text CC BY 4.0 · Documentation, not legal advice.*

Every release is maintained. The coordinator owns this calendar; dataset agents do the work; the founder handles anything destructive, legal or public-facing. The stage-12 gate passes only when the next-version date is set in `job.json` and on the release calendar (`coordinator/release_calendar.jsonl`).

## 1. Event-driven deadlines

| Trigger | Action | Deadline | Owner | Evidence |
|---|---|---|---|---|
| Rights-holder takedown request | Acknowledge; exclude the item from the next build at once; remove it and publish a corrected version; log the ticket ID in `opt_out_status` | Acknowledge within 2 business days; removal ≤ 30 days | agent; founder replies | takedown log, `CHANGELOG.md` |
| Platform request | Remove the affected rows or IDs | ≤ 24 h | agent | `CHANGELOG.md` |
| PII, child-safety or abuse-material report | Stop serving the affected files at once (new commit without them); abuse material goes straight to the founder | ≤ 24 h | agent; founder | incident log |
| Benchmark test-set leak | Rotate the test set; publish a new version | ≤ 30 days | agent | new version |
| Partner withdraws content | Remove it and correct the public counter | ≤ 30 days | agent; founder | counter diff |
| Upstream terms change or source drift | Quarantine affected payloads, re-assess, move to index-only if needed | On detection | agent → coordinator | `sources.jsonl` recheck |
| A hosted item is removed, made private or changes licence | Prune it from the manifests; if no longer Creative Commons, move it to index-only | Within the next 30-day cycle | agent | prune log |
| Deletion notice under an API's or platform's terms | Delete the affected identifiers and data | As the terms require | agent | prune log |

Takedown handling: log the ticket; find affected items through the provenance ledger; remove or move to index-only in a new version; propagate the opt-out to future crawls and to mirrors and partners bound by our terms; never purge Hugging Face history without founder approval; never argue a takedown publicly (disputes go to the founder).

## 2. Recurring cadence

| Cadence | Task | Owner |
|---|---|---|
| Every 30 days | Prune removed, private or re-licensed items from manifests; refresh or delete stored API data where the API's terms set 30 days | agent |
| Weekly | Native review adjudication; reproducibility replay in a clean environment; issue triage; link health; portfolio balance | agent; coordinator |
| Monthly | Competitor and claim refresh; licence spot-checks; usage and conversion review; decisions on stale releases; AI-visibility sampling; metrics digest row (stage 11) | coordinator |
| Quarterly | Scheduled refresh: new dated snapshot plus changelog | agent |
| Each new version | Re-verify every source licence; re-run the claims check; update the changelog; re-check tool and model licences in `manual/tooling.lock.yaml` for tools on the release path | agent → coordinator |
| T+7 after launch | Fix card issues; add "models trained on it" links | agent |
| T+30 after launch | 30-day rule review (`verdict_30d` in the metrics row) | coordinator |

## 3. Per-release schedule (fill one block per release)

| Release | Version | Launch date | T+7 | T+30 | Next 30-day prune | Next quarterly refresh | Next-version date |
|---|---|---|---|---|---|---|---|
| <asset id> | <vMAJOR.MINOR> | <YYYY-MM-DD> | <+7 d> | <+30 d> | <if API data is stored> | <+3 months> | <YYYY-MM-DD> |

Add the next-version date as a row with `kind: next_version` in `coordinator/release_calendar.jsonl` (the machine-readable calendar); the stage-12 gate checks for it.

## 4. Manual maintenance

| When | Task |
|---|---|
| Quarterly (proposed: 12 Jan, 20 Apr, 13 Jul, 12 Oct 2027) | Review thresholds, tool pins and post-mortems; minor version for tooling bumps, major version for gate or threshold changes |
| After any release that failed or skipped a gate | Post-mortem by the coordinator; a release that skipped a gate is reverted |
| Each tooling bump | Re-verify the licence of every changed tool or model; no tool flagged non-commercial or unknown may produce released artefacts |

**Versioning.** `vMAJOR.MINOR` plus a date tag. Never change labels or a headline score under the same version. Deprecated versions stay listed with the reason. Every release has its next-version date set.
