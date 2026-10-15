# Gate crosswalk: 13 stages × release gates G0-G7

*Operating manual v1.0.1 · Approved by the founder on 15 Oct 2026 · Text CC BY 4.0 · Documentation, not legal advice.*

Every Bayanat Labs release passes eight release gates, G0 to G7: Source, Acquisition, Processing, Privacy, Quality, Human, Legal and Claims. `manual/stages.yaml` assigns each gate to one or more of the 13 stages and states its checks and thresholds. Where the sources behind a threshold gave different values, the value adopted and the alternative are both recorded (section 4). A scoping memo may tighten any default; loosening one needs written founder approval. Tables 1 and 2 are generated from `stages.yaml`; do not edit them by hand.

## 1. Every G gate maps to at least one stage

<!-- BEGIN GENERATED:gate_to_stages -->
| G gate | Name | Stages (stages.yaml) |
|---|---|---|
| G0 | Source | 0, 1 |
| G1 | Acquisition | 2 |
| G2 | Processing | 3, 4 |
| G3 | Privacy | 5 |
| G4 | Quality | 6, 7 |
| G5 | Human | 7 |
| G6 | Legal | 0, 8 |
| G7 | Claims | 8, 9, 10 |
<!-- END GENERATED:gate_to_stages -->

## 2. Every stage maps to at least one G gate or a coordinator check

<!-- BEGIN GENERATED:stage_to_gates -->
| Stage | Name | G gates | Gate (pass condition) | Number of checks |
|---|---|---|---|---|
| 0 | Scoping memo | G0, G6 | Coordinator approves the memo and assigns the legal tier, which is not red; job.json exists with external actions off. | 11 |
| 1 | Discovery | G0 | Provenance ledger started; every item's licence and terms checked; training opt-in settings stored as a filter column; Creative Commons uploaders screened for licence laundering; every source has a tos_basis. | 12 |
| 2 | Acquisition | G1 | Raw store complete with a checksum and fetch timestamp per item; etiquette followed; access denials logged, never bypassed; every Tier 2 item covered by the named collection basis. | 13 |
| 3 | Normalisation | G2 | Schema validation passes on 100% of records; the normalisation version is recorded; raw and normalised fields sit side by side; speech transcripts come from manual captions or dual-ASR agreement (CER <= 15%), never auto-captions. | 8 |
| 4 | Deduplication | G2 | Duplicate rate and language-ID statistics reported and inside the memo's ranges; zero overlap between any benchmark test set and any training release. | 5 |
| 5 | Safety and PII | G3 | Zero PII hits in a 3,000-record stratified audit (a residual rate under 0.1% on the first 1,000 is also reported); R1-R7 pass; no sensitive-category labels; faces and plates blurred; no minors; audit passed before any upload outside KSA/UAE. | 14 |
| 6 | Enrichment | G4 | Label distribution report exists; a manual spot-check of at least 1% per dialect by speakers of that dialect is done; every label carries annotation_origin. | 7 |
| 7 | Human QA | G4, G5 | Agreement meets the memo threshold (floor kappa 0.6, 0.7 for eval sets); sample sizes meet the T7 minimums; a named native reviewer signs; the QA report goes into the card. | 9 |
| 8 | Packaging | G6, G7 | Viewer renders; datasets.load_dataset works in a clean environment; card linter passes; licence compatibility checked with obligations propagated; every item that needs a recorded legal decision cites it; required files present. | 18 |
| 9 | Baseline or benchmark | G7 | A script-computed number exists that a journalist can print, with its chart and the script that draws it. | 5 |
| 10 | Release | G7 | Coordinator runs the launch-bundle checklist; claims re-verified on release day (G7); the founder's go is recorded. | 6 |
| 11 | Promotion and measurement | coordinator: Metrics row present and schema-valid (no release gate G0-G7 covers promotion). | A metrics row for the release is added to the digest and validates against coordinator/metrics_digest_row.schema.json. | 1 |
| 12 | Maintenance | coordinator: Next version date set; index-only triggers reviewed; maintenance calendar entries created (no release gate G0-G7 covers maintenance). | The next version date is set in job.json and on the release calendar; the policy's index-only triggers IO-1 to IO-5 were reviewed for this version. | 5 |
<!-- END GENERATED:stage_to_gates -->

`scripts/validate_stages.py` fails if either direction breaks: a G gate with no stage, a stage with neither a G gate nor a `coordinator_check`, or a `cr_gates` block that disagrees with the stage entries.

## 3. Gate by gate: what each gate requires

| Gate | What it requires (checks in `stages.yaml`) |
|---|---|
| G0 Source | Stage 0: the coordinator approves the memo and assigns the legal tier. Stage 1: provenance ledger started; every source has a recorded licence and terms basis (`tos_basis`) and its terms read and filed; rights signals per item (robots.txt, TDMRep, Content-Signal); training opt-in settings stored as a filter column; Creative Commons uploaders screened for licence laundering; a probe of at least 10 records; no login, paywall or protection circumvention. Checks `S0.*`, `S1.*` |
| G1 Acquisition | At least 3 s between requests per host, 5 s for government, small or slowing hosts, concurrency 1 (C-01); User-Agent with a contact address; backoff on 429; checksums and fetch timestamps for 100% of items; access denials logged, never bypassed; no IP rotation; every Tier 2 item covered by a named collection basis |
| G2 Processing | Schema validation on 100% of records; normalisation version recorded, with the recipe in C-03; duplicate and language-ID statistics inside the memo's ranges; zero overlap between any benchmark test set and any training release |
| G3 Privacy | Zero PII hits in at least 3,000 stratified records, with the rate on the first 1,000 also reported (C-04); re-identification tests R1-R7; no sensitive-category labels; faces and plates blurred; no minors; audit passed before any upload outside KSA/UAE |
| G4 Quality | Agreement floor κ ≥ 0.6 (≥ 0.7 for eval sets), which the memo may raise (C-05); sample sizes fixed in the memo (C-06); per-stratum error rates with intervals; a 1% dialect spot-check by speakers of that dialect |
| G5 Human | A named native reviewer signs off every public release; dialect labels are checked by speakers of that dialect; automated review only screens internal pilots (C-09) |
| G6 Legal | Licence compatibility checked; SA and NC obligations propagated; every item whose release needs a recorded legal decision cites it by decision ID (`S8.decision_cited`, `S8.undecided_points_logged`; C-10); no tool or model flagged non-commercial or unknown on the release path |
| G7 Claims | Every number script-computed; superlatives re-verified on release day in `CLAIMS.md` and approved by the founder; page, card and archive agree; synthetic data labelled; the coordinator's checklist and the founder's go at stage 10 (C-12, C-13) |
| — (no G gate) | Coordinator checks at stage 11 (metrics row) and stage 12 (next version date, index-only review) |

## 4. Choices the manual makes

Each row records the value adopted in `stages.yaml` and the alternative that was considered. The founder approved all twenty-one choices for v1.0 on 15 Oct 2026; the alternative stays on record.

| # | Topic | Adopted in `stages.yaml` | Alternative on record |
|---|---|---|---|
| C-01 | Request rate | At least 3 s per host for every host, APIs and dumps included, and inside any documented quota; at least 5 s for government and small hosts; concurrency 1 | 1 request per second per host, or a faster rate for APIs and dumps that document higher limits (needs written founder approval) |
| C-02 | Parallel connections to bulk-dump hosts | 1 connection per host, resumable | 2 parallel connections |
| C-03 | Text normalisation recipe | `text_raw` byte-exact; `text_diac` NFC; `text_norm` NFKC-based with taa marbuta kept and flagged; taa marbuta folded only in `text_search`; `normalisation_version` recorded | NFC plus presentation-form mapping only (Bayanat-Norm v1). Both keep the raw text, so neither is destructive |
| C-04 | PII audit | Zero hits in at least 3,000 stratified records; the residual rate on the first 1,000 reported alongside | Residual PII under 0.1% on a 1,000-item audit |
| C-05 | Agreement | κ ≥ 0.6 (≥ 0.7 for eval sets) as a floor under the memo threshold | The memo threshold alone |
| C-06 | Human QA sample | Text: 1,000 per subset and at least 200 per stratum family. Speech: the larger of 2% of segments and 2 h per subset. A 50-record calibration batch | 1,000 records or 2 hours per subset; or 2-5% of speech segments |
| C-07 | Video downloads in acquisition | Creative Commons video is downloaded only when the memo sets `video_media_download` and check `S2.media_download_decision` passes; standard-licence video is Tier 2 (identifiers and labels) | Downloads as a routine acquisition step |
| C-08 | Privacy gate content | All of: no sensitive-category labels; faces and plates blurred; PII audio dropped; CSAM hash checks; NSFW and toxicity review; R1-R7; no minors | Any one subset of these |
| C-09 | Human sign-off | Native human sign-off for every public release; automated review only screens internal pilots | Automated review for synthetic pilots |
| C-10 | Legal decisions | Each item whose release needs a legal position cites a recorded decision by its decision ID; free text is not accepted | A separate legal review for each release |
| C-11 | Processing gate scope | Normalisation version, deduplication and language-ID statistics, and zero test-set overlap | Without the overlap check |
| C-12 | Claims gate | Script-computed numbers, release-day re-verification, synthetic labels, page-card-archive agreement and founder approval of superlatives | Without the last two |
| C-13 | Release gate owner | The coordinator's checklist **and** the founder's go | The coordinator's checklist alone |
| C-14 | Provenance file | `PROVENANCE.parquet` (JSONL under 100k rows) | `PROVENANCE.jsonl` |
| C-15 | Speech packaging | Parquet with the HF Audio feature up to 1 TB; WebDataset above that | WebDataset for non-consented speech |
| C-16 | Public-domain cutoff | Author death in or before 1955 | Author died 50 or more years ago |
| C-17 | Music in Creative Commons speech | Music-flagged segments excluded from audio releases; separation for internal ASR only (check `S3.music_excluded`) | Separate the music and keep the segment |
| C-18 | Takedown speed | Acknowledge within 2 business days; removal within 30 days; platform requests and PII, child-safety and abuse reports within 24 h | 30 days, and 24 h for platform requests |
| C-19 | Definition of done timing | Two phases in `manual/dod.yaml`: `rc` before the founder's go, `done` after launch | One list checked after launch |
| C-20 | Where speech transcription sits | VAD, music flagging, forced alignment and dual ASR at stage 3; diarisation, dialect ID and quality scores at stage 6 | ASR and alignment at stage 6 (stages 4 and 5 then have no transcripts to work on) |
| C-21 | Models whose licences bar release use | Only models cleared in `manual/tooling.lock.yaml` produce released artefacts; flagged models give internal pre-labels at most; alignment uses a commercially usable Arabic wav2vec2 model | MMS aligners, ArTST, ADI-20 and sentence-level ALDi on the release path |

## 5. Verification notes

- **PDPL cross-border transfer.** Article 29 of SDAIA's English text of the PDPL (https://sdaia.gov.sa/en/SDAIA/about/Documents/Personal%20Data%20English%20V2-23April2023-%20Reviewed-.pdf) deals with transferring personal data outside the Kingdom. The manual requires the stage-5 audit to pass before any upload to a host outside KSA/UAE, private repositories included.
- **Stored API data.** Data stored from an API is refreshed or deleted as that API's terms require; where the terms set 30 days, stage 12 and `coordinator/maintenance_calendar.md` follow them.
