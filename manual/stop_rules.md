# Stop rules

*Operating manual v1.0.1 · Approved by the founder on 15 Oct 2026 · Text CC BY 4.0 · Documentation, not legal advice.*

A stop rule says what happens when something goes wrong, so that no release is delayed forever and no gate is quietly weakened. Two principles sit above all of them:

1. **Never bypass a gate and never wait indefinitely.** If a source fails a gate, record the failure and continue with an independently cleared source.
2. **Stop, record, then decide.** Every stop is logged in the job's daily receipt with the reason, and the item's status in the tracker changes (`blocked_rights`, `blocked_founder` or `dropped`).

Stage-specific stop conditions are listed under each stage in `manual/stages.yaml`; this page collects the programme-level rules.

## 1. Programme stop rules

| # | Trigger | Rule | Related |
|---|---|---|---|
| SR-1 | A release cannot pass the legal gate | Convert it to Tier 2 (identifiers, metadata and our own annotations plus a rebuild script) or drop it. Never delay it indefinitely | `policy/stop-rules.md` SR-1 |
| SR-2 | A benchmark test set leaks | Rotate the test set and publish a new version within 30 days | `policy/stop-rules.md` SR-2 |
| SR-3 | A partner withdraws content | Remove it within the SLA (30 days) and correct the public counter | `policy/stop-rules.md` SR-3 |
| SR-4 | We cannot license verbatim text or transcripts | They stay internal: aggregate statistics, benchmark scoring and internal tooling only. Never published, even gated or labelled "research only" | `policy/tiers.yaml` internal-only rule |
| SR-5 | Index-only triggers: the source's terms changed after collection, an item received a takedown, a video is no longer Creative Commons at re-verification, an audit found residual PII, or a portal licence cannot be read | Move the affected items from published content to index-only (Tier 2). An index entry that itself carries personal data is removed, not kept (`policy/index-only-rules.yaml` IO-4) | `policy/index-only-rules.yaml` IO-1 to IO-5 |
| SR-6 | A source is blocked | Substitute a cleared opportunity; do not weaken the gate | — |

## 2. Stop and ask: an agent halts and reports when

- The rights for the planned use are unclear, or the terms forbid it.
- A source returns 403 or 429 repeatedly, or shows a login wall, CAPTCHA or WAF challenge.
- Personal data appears that the scoping memo did not plan for.
- A model or tool needs gated terms accepted, or its licence bars commercial use or is unknown. Such a tool may not produce released artefacts.
- The approved compute or download budget is reached. The agent reports the partial result rather than overrunning.
- A step would need an external action: creating an account, signing in, accepting terms, paying, sending a message or publishing. Only the founder does these.

## 3. Stage stops

| Stage | Trigger | Rule |
|---|---|---|
| 0 Scoping memo | Legal tier red, or the rubric's legal verdict is "excluded" | Drop the candidate and move to a cleared source |
| 1 Discovery | robots.txt, TDMRep or Content-Signal reserves the content; or a GPTBot, CCBot or Google-Extended block | The host is identifiers-only |
| 1 Discovery | A source's terms have not been read | Read and file them before touching the source |
| 2 Acquisition | HTTP 429 | Honour `Retry-After`, back off; after 3 consecutive 429s pause the host 24 h |
| 2 Acquisition | 401, 403, login wall, CAPTCHA, WAF | Stop and log; the source moves to "permission required" |
| 2 Acquisition | A site blocks requests from outside Saudi Arabia | In-Kingdom host only; if blocked there too, stop and draft an official access request |
| 2 Acquisition | Tier 2 item without a named collection basis | No scaling beyond the pilot until a basis exists |
| 2 Acquisition | Tier 3 source without the partner's written permission on file | Do not collect (`policy/tiers.yaml` Tier 3) |
| 3 Normalisation | A task needs a distinction that normalisation folds | Use the raw or diacritised field; never fold silently |
| 4 Deduplication | Any overlap between a benchmark test set and a training release | Remove the items or rotate the test set; never ship with overlap |
| 5 Safety and PII | Any PII hit in the 3,000-record audit | Fix, redact or drop, then re-audit on a fresh stratified sample; no upload outside KSA/UAE until it passes |
| 5 Safety and PII | Possible child sexual abuse material (hash match) | Do not open, view or redistribute; quarantine the reference; notify the founder at once |
| 5 Safety and PII | Probable child voice or image | Drop it and log the count, never the content |
| 6 Enrichment | Systematic dialect-label errors | Fix and re-audit the stratum |
| 7 Human QA | Agreement below the memo threshold | Fix the guideline, relabel, re-measure; never lower the threshold |
| 7 Human QA | No named native reviewer | The release waits; it never ships on machine review alone |
| 8 Packaging | Licence incompatibility | One configuration per licence, or drop the incompatible part |
| 9 Baseline | No printable number | The release does not ship |
| 10 Release | Founder says no-go | The release stays "ready to publish"; nothing goes public |
| 10 Release | A claim fails release-day re-verification | Remove the superlative from every copy |
| 11 Promotion | A listing, acceptance or backlink does not exist yet | Never claim it |
| 12 Maintenance | Takedown, platform request, PII or child-safety report | Act within the SLA in `coordinator/maintenance_calendar.md` |

## 4. Thresholds are never loosened to get past a stop

A scoping memo may tighten any threshold. Loosening one needs written founder approval, recorded in the memo's deviations block and in `manual/CHANGELOG.md`. After any release that failed or skipped a gate, the coordinator writes a post-mortem and the next quarterly review considers a manual change.
