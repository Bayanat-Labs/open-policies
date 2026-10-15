# Ledger procedure (coordinator)

*Operating manual v1.0.1 · Approved by the founder on 15 Oct 2026 · Text CC BY 4.0 · Documentation, not legal advice.*

The coordinator keeps three ledgers so that any record, number or claim can be traced in one query. The dataset agent writes them; the coordinator checks them at the gates named below and keeps the programme-level copies.

| Ledger | One row per | File | Schema | Started at | Checked at |
|---|---|---|---|---|---|
| Source ledger | source | `sources.jsonl` (job dir) | `templates/provenance_ledger_schema.json#/$defs/source_record` | Stage 1 | Stage 1 gate (G0), D02 |
| Provenance ledger | released item | `PROVENANCE.parquet` (JSONL under 100k rows), job dir then HF repo | `templates/provenance_ledger_schema.json` | Stage 1, before acquisition | Stage 8 gate, D02 |
| Claims ledger | claim | `CLAIMS.md` per repo + the site-wide claims register | the `CLAIMS.md` template of the dataset template | Stage 0 (draft claim) | Stage 10 gate (G7), D04 |

The claims rules are in `policy/claims-rules.md`. This page says who does what, when, and how to answer the standard questions.

## 1. Source ledger (`sources.jsonl`)

1. The agent adds a row for each source during discovery, before any payload is fetched.
2. Each row records the data, documentation and licence URLs, version or commit, retrieval date and owner; the acquisition mechanism; separate statuses for access, redistribution, derivatives, commercial reuse, training, evaluation and identifiable persons (unknown stays unknown); the licence evidence (short quote, URL, page hash); attribution, share-alike and removal obligations; host limits; the licence route and release tier; and a recheck date.
3. The coordinator rejects the stage-1 gate if any source lacks a `tos_basis`, has unread terms, or has no recorded licence.
4. On every new version the agent re-verifies each source licence and updates `recheck_by`.

## 2. Provenance ledger (`PROVENANCE.parquet`)

1. Start it at discovery. Every acquired item gets a row at fetch time with its URL, retrieval time, HTTP status, robots.txt hash, TDMRep and Content-Signal values, raw SHA-256 and licence evidence.
2. Every transform appends to `transform_chain` (step, tool, version, code commit, output hash). Never overwrite a row; append the new state.
3. A record without provenance is not released. The stage-8 gate validates every row against the schema.
4. Count acquired, accepted, rejected-by-reason, deduplicated and reviewed records separately. Repeated pages never count as new records.
5. Rows from video hosts add the host's licence status with its check time, any training opt-in value (a filter column, never an opt-out) and the laundering-screen result.

### Standard queries

"Where did this record come from?" must be one query. Examples (DuckDB SQL over the released Parquet; adapt paths):

```sql
-- 1. Where did this record come from?
SELECT item_id, source_id, source_url, upstream_version, retrieved_at, http_status,
       license_detected, license_evidence.url AS evidence_url, tos_basis, raw_sha256
FROM 'PROVENANCE.parquet' WHERE item_id = 'abc123' OR list_contains(output_ids, 'abc123');

-- 2. Takedown: every released item from a URL prefix or source
SELECT item_id, output_ids, opt_out_status FROM 'PROVENANCE.parquet'
WHERE source_url LIKE 'https://example.org/%' OR source_id = 'SRC07';

-- 3. Licence partition check: one licence per config
SELECT config, license_detected, count(*) FROM 'PROVENANCE.parquet' GROUP BY 1, 2 ORDER BY 1;

-- 4. Rows that would fail release: missing basis or evidence
SELECT item_id FROM 'PROVENANCE.parquet' WHERE tos_basis IS NULL OR license_evidence IS NULL;
```

For JSONL ledgers the same lookup is one `jq` line: `jq -c 'select(.item_id=="abc123")' PROVENANCE.jsonl`.

## 3. Claims ledger (`CLAIMS.md` and the claims register)

| Step | Who | When | What |
|---|---|---|---|
| Draft | Dataset agent | Stage 0 | The memo's `claim_to_make` gives the draft wording, or "No comparative claim" |
| Evidence | Dataset agent | Stages 8-9 | Fill `CLAIMS.md` from the template: allowed wording, unit and counting rule, our count from a script (path and output hash), licence class, date, incumbent with size, licence and URL; saved search for any "first" or "only" |
| Verify | Coordinator | Release day (stage 10) | Re-check every incumbent and count on the day; page, card and archive must agree; record `claims_reverified_on` in `qa/reports/release_checklist.json` |
| Approve | Founder | Before launch | Approves every "largest / first / only" wording and any benchmark result naming vendors or national models |
| Register | Coordinator | Launch day | Add or update the row in the site-wide claims register |
| Recheck | Coordinator | Monthly, and every new version | Competitor and claim refresh; a claim that no longer holds is withdrawn from every copy the same week |

Rules that the coordinator enforces (`policy/claims-rules.md`): count only what is released; name the licence class; date every claim; never pool tiers; never compare open data with non-commercial or request-only sets without saying so; commercial inventory figures stay out of open claims; every number is computed by a script from the released files.

## 4. Programme ledger (coordinator only)

The coordinator also keeps, in the programme workspace:

- `coordinator/release_calendar.csv` and its JSONL mirror: every release, its version, target date and next-version date (stage 12 gate).
- `coordinator/metrics_digest.jsonl`: one row per live asset per month, valid against `coordinator/metrics_digest_row.schema.json` (stage 11 gate).
- A release index: asset id, version, `manual_version` used, gate report path (`qa/reports/gates.json`), definition-of-done report, founder go date, DOI, and any post-mortem.
- The daily receipts from every agent: `external_actions` must be empty unless the founder has written a scope into the job spec.
