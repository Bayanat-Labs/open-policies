# How Bayanat Labs builds open datasets

Version 1.0.1 · 15 Oct 2026 · Approved by the founder on 15 Oct 2026 · Text CC BY 4.0; schemas and scripts Apache-2.0 · Attribution: "Operating manual by Bayanat Labs" · Documentation, not legal advice · Contact: hello@bayanatlabs.com

This is the operating manual of the Bayanat Labs open-data programme. The Arabic edition is `manual/PUBLIC.ar.md`. Where the two editions differ, this English edition and `manual/stages.yaml` apply.

## 1. What this manual is

Every Bayanat Labs open dataset goes through the same pipeline: a stage-0 scoping memo and twelve further stages, each closed by a gate. That is 13 gates in all. Every gate is blocking. A failed gate blocks the release, and a release that skipped a gate is reverted.

The manual is the process: what happens in which order, and how each step is checked. What may be released, and under which licence, is set by the Bayanat Labs open-programme policy (`policy/` in this repository: release tiers, licence matrix and selection rubric). A scoping memo may tighten any threshold in this manual; loosening one needs written founder approval.

**Legal positions.** A stage, gate or stop rule that needs a legal position cites the recorded decision it rests on, by its decision ID. No stage waits for a separate legal sign-off.

**One source of truth.** The stage table lives only in `manual/stages.yaml`. The tables in section 3 of this manual and in the gate crosswalk are generated from it. The `bl-gates` checker of the Bayanat Labs dataset template pins `stages.yaml` by version, and every dataset card records the `manual_version` in its Creation section.

| File | What it holds |
|---|---|
| `manual/PUBLIC.md`, `manual/PUBLIC.ar.md` | This manual in English and Arabic; the stage sections are generated from `manual/stages.yaml` |
| `manual/stages.yaml` + `manual/schemas/stages.schema.json` | The 13 stages: actions, tools, inputs, outputs, gate checks, thresholds, owner, stop conditions and the G0-G7 mapping |
| `manual/gate-crosswalk.md` | Stages × release gates G0-G7, and the choices the manual makes where its sources differed |
| `manual/SCOPING_MEMO.md`, `manual/scoping_memo.schema.json`, `manual/schemas/scoping_memo_record.schema.json` | Stage-0 template; the rubric score block in the `bl-score` format; the memo record the later gates read |
| `manual/dod.yaml` | The 12-item definition of done, read by `bl-gates --dod` |
| `manual/etiquette.md`, `manual/stop_rules.md` | Crawler etiquette and stop rules |
| `manual/tooling.lock.yaml` | Pinned tools and models with verified licences |
| `manual/budget.py` | Budget estimator |
| `coordinator/` | Ledger procedure, launch-bundle checklist, metrics digest row schema, maintenance calendar |
| `scripts/validate_stages.py` | Validates `stages.yaml` and `dod.yaml`; evaluates every gate against real artefacts |

**Names used here.**

| Name | Meaning |
|---|---|
| `bl-score` | The command-line tool that applies the policy's selection rubric to a scoping memo (`tools/bl-score`) |
| `bl-gates`, `bl-card-lint`, `bl-manifest`, `bl-card-render` | The release kit of the Bayanat Labs dataset template (`Bayanat-Labs/dataset-template`) |
| `arabic-normalize` | The Bayanat Labs Arabic text normaliser (Bayanat-Norm policies) |
| Arabic recogniser pack | The Bayanat Labs Arabic PII recogniser pack for Presidio |
| In-Kingdom host | The Bayanat Labs crawl host in Saudi Arabia, used for sites that block requests from abroad |
| Decision ID | The identifier (`decision_id`) of a recorded legal decision; the only form in which a legal position is cited |
| Founder-only actions | Accounts, legal sign-off, agreements, payments, outreach, publication, infrastructure, legal incidents, destructive changes and claim approval. Agents never take them |
| G0-G7 | The eight release gates: Source, Acquisition, Processing, Privacy, Quality, Human, Legal, Claims |
| Tier 1 / 2 / 3 | Open content / manifests and our annotations only / partner-licensed content (`policy/tiers.yaml`) |

**Sources.** The stages and thresholds reflect Bayanat Labs practice and the public works cited where they are used. Where a figure matters, this manual states it in full.

## 2. The pipeline at a glance

![The 13 stages of the Bayanat Labs pipeline](stage_diagram.svg)

| Stage | Name | Gate (pass condition) | Owner | Sign-off | G gates |
|---|---|---|---|---|---|
| 0 | Scoping memo | Coordinator approves the memo and assigns the legal tier, which is not red; job.json exists with external actions off. | coordinator | coordinator | G0, G6 |
| 1 | Discovery | Provenance ledger started; every item's licence and terms checked; training opt-in settings stored as a filter column; Creative Commons uploaders screened for licence laundering; every source has a tos_basis. | agent | dataset-agent | G0 |
| 2 | Acquisition | Raw store complete with a checksum and fetch timestamp per item; etiquette followed; access denials logged, never bypassed; every Tier 2 item covered by the named collection basis. | agent | dataset-agent, coordinator | G1 |
| 3 | Normalisation | Schema validation passes on 100% of records; the normalisation version is recorded; raw and normalised fields sit side by side; speech transcripts come from manual captions or dual-ASR agreement (CER <= 15%), never auto-captions. | agent | dataset-agent | G2 |
| 4 | Deduplication | Duplicate rate and language-ID statistics reported and inside the memo's ranges; zero overlap between any benchmark test set and any training release. | agent | dataset-agent | G2 |
| 5 | Safety and PII | Zero PII hits in a 3,000-record stratified audit (a residual rate under 0.1% on the first 1,000 is also reported); R1-R7 pass; no sensitive-category labels; faces and plates blurred; no minors; audit passed before any upload outside KSA/UAE. | agent | dataset-agent, coordinator | G3 |
| 6 | Enrichment | Label distribution report exists; a manual spot-check of at least 1% per dialect by speakers of that dialect is done; every label carries annotation_origin. | agent | dataset-agent, native-reviewer | G4 |
| 7 | Human QA | Agreement meets the memo threshold (floor kappa 0.6, 0.7 for eval sets); sample sizes meet the T7 minimums; a named native reviewer signs; the QA report goes into the card. | agent | native-reviewer, coordinator | G4, G5 |
| 8 | Packaging | Viewer renders; datasets.load_dataset works in a clean environment; card linter passes; licence compatibility checked with obligations propagated; every item that needs a recorded legal decision cites it; required files present. | agent | dataset-agent, coordinator | G6, G7 |
| 9 | Baseline or benchmark | A script-computed number exists that a journalist can print, with its chart and the script that draws it. | agent | dataset-agent | G7 |
| 10 | Release | Coordinator runs the launch-bundle checklist; claims re-verified on release day (G7); the founder's go is recorded. | coordinator | coordinator, founder | G7 |
| 11 | Promotion and measurement | A metrics row for the release is added to the digest and validates against coordinator/metrics_digest_row.schema.json. | coordinator | coordinator | coordinator check |
| 12 | Maintenance | The next version date is set in job.json and on the release calendar; the policy's index-only triggers IO-1 to IO-5 were reviewed for this version. | coordinator | coordinator, founder | coordinator check |

**Roles.**

| Role | Signs | Never does |
|---|---|---|
| Dataset agent | Stage gates 1-9 for its own release, with evidence paths | Any external action: accounts, sign-ins, terms, payments, messages, publishing |
| Coordinator | Stage 0 approval, stage 10 checklist, stages 11-12; runs the ledgers, the calendar, launch bundles and metrics | Approve its own agent's work without the evidence files |
| Native reviewer | Stage 7 sign-off; dialect labels checked by speakers of that dialect | Approve labels because a model explained them persuasively |
| Founder | Stage 10 go, superlative approval, every external action | — |

Workers and evaluators are separate: one agent acquires, another transforms, another evaluates.

**How a gate is checked.** Each gate is a list of machine-checkable checks over files in four roots: the job directory, the Hugging Face dataset repo, the GitHub builder repo and the coordinator's programme workspace. There are six check types: a file exists; a file is absent (for example, no data files in the GitHub repo); a file validates against a JSON Schema; a metric in a JSON or YAML report meets a threshold (a fixed value, a memo value or another field); a named sign-off with a date and verdict is present; a row exists in a ledger, optionally with required fields filled. A fifth root, `legal_record`, is the organisation's legal record (configured path): the table of recorded decisions that legal checks read by decision ID. A check applies or is n/a only through a condition on the memo record; if the memo lacks the field, the check is an error, never n/a. Each report a check reads has a JSON Schema in `manual/schemas/reports/`, generated from the checks. Human judgement enters only through named sign-offs. `scripts/validate_stages.py --evaluate` runs every check and writes a report; the dataset template's `bl-gates` is the production checker and writes `qa/reports/gates.json`.

```bash
python scripts/validate_stages.py manual/stages.yaml --dod manual/dod.yaml --tooling manual/tooling.lock.yaml   # validate the manual
python scripts/validate_stages.py manual/stages.yaml --evaluate --stages 0-8 \
    --job <job dir> --hf <hf checkout> --gh <builder checkout> --programme <coordinator dir>
python scripts/validate_stages.py manual/stages.yaml --dod manual/dod.yaml --evaluate --phase rc --job ...
```

## 3. The thirteen stages

Generated from `manual/stages.yaml`. Paths are relative to their root: `job` = the job directory, `hf_repo` = the HF dataset repo, `gh_repo` = the GitHub builder repo, `programme` = the coordinator workspace, `legal_record` = the organisation's legal record (configured path). `memo:` values come from the approved scoping-memo record (`scoping_memo.yaml`).

### Stage 0: Scoping memo

**Purpose.** Decide, on one page plus tables, whether the release is worth building and legally buildable, before anything is fetched.

**Owner:** coordinator · **Sign-off:** coordinator · **G gates:** G0, G6 · **Blocking:** yes

**What the agent does**

- Fill manual/SCOPING_MEMO.md and its record scoping_memo.yaml: candidate ID, claim to make, incumbents and sizes with URLs, sources with their licences and terms, release tier, licence plan per config, collection basis for Tier 2, priority, product link, risks, QA sample and agreement threshold, budget, owner, dates, stop conditions.
- Write the rubric block scoping_memo.score.yaml in the exact bl-score format (five 1-5 scores, legal tier, effort, one-line justifications), run the pinned bl-score (manual/bl-score.pin.json: pinned by file hash, not by version) and save its JSON output as scoping_memo.score.json; record the scorer's tree hash as score_tool_sha256. A red legal tier, or a legal_cleanliness score of 1, ends the job; a score of 2-3 caps the release at Tier 2.
- Record for every source its licence route (licence_route, an input-licence ID in policy/licence-matrix.yaml) and the release tier its content may reach (release_tier), and cite any legal position only by the ID of the recorded decision it rests on (decision_ref). Free text is not accepted there.
- Re-check the claim's incumbent and every source licence on the day the memo is written.
- Write job.json (schema: manual/schemas/reports/job.schema.json) with external_actions_authorized false.

**Tools** (keys into `manual/tooling.lock.yaml`; `bayanatlabs:` = Bayanat Labs' own tools): `bayanatlabs:bl-score`

**Inputs:** the candidate's scoping entry; each source's licence and terms; the organisation's legal record (configured path): recorded decisions by decision_id, the only citable source for a legal position; open-programme policy: rubric, tiers, licence matrix (policy/ in Bayanat-Labs/open-policies); manual/bl-score.pin.json (bl-score tree hash); budget estimate from manual/budget.py

**Outputs:** `job:scoping_memo.md`; `job:scoping_memo.yaml`; `job:scoping_memo.score.yaml`; `job:scoping_memo.score.json`; `job:job.json`

**Gate.** Coordinator approves the memo and assigns the legal tier, which is not red; job.json exists with external actions off.

| Check | Machine-checkable expression |
|---|---|
| `S0.memo` | `exists(job:scoping_memo.md, job:scoping_memo.yaml, job:scoping_memo.score.yaml, job:scoping_memo.score.json)` |
| `S0.memo_schema` | `valid(job:scoping_memo.yaml, manual/schemas/scoping_memo_record.schema.json)` |
| `S0.score_schema` | `valid(job:scoping_memo.score.yaml, manual/scoping_memo.schema.json)` |
| `S0.legal_tier` | `job:scoping_memo.score.yaml:legal_tier in ["green", "yellow"]` |
| `S0.rubric_scored` | `job:scoping_memo.score.json:legal_verdict in ["tier1_eligible", "tier2_only"]` |
| `S0.score_tool_pinned` | `job:scoping_memo.yaml:score_tool_sha256 in ["daf73c4e0139cb2d7e489dce2db293e5ea50880df1ceb2effc9e794161da27bc"]` |
| `S0.same_candidate` | `job:scoping_memo.score.json:candidate_id == memo:candidate_id` |
| `S0.coordinator_approval` | `signoff(job:scoping_memo.yaml:decision.coordinator, role=coordinator, verdict=approve)` |
| `S0.legal_tier_assigned` | `job:scoping_memo.yaml:decision.legal_tier_assigned is_true` |
| `S0.job_spec` | `valid(job:job.json, manual/schemas/reports/job.schema.json)` |
| `S0.no_external_actions` | `job:job.json:external_actions_authorized is_false` |

| Threshold | Default (a memo may tighten, never loosen) | Adopted from |
|---|---|---|
| `T0.legal` Legal tier allowed to proceed | green or yellow; red is not built | policy/rubric.yaml legal gate |
| `T0.tighten_only` Memo overrides | tighten only; loosening needs written founder approval | Bayanat Labs practice |

**Stop conditions**

- Legal tier red, or bl-score legal_verdict excluded: drop the candidate, record why, and move to an independently cleared source.
- A source's terms have not been read: read and file them before the memo can be approved.
- The claim needs a 'first' or 'only' and no saved search exists: write 'no comparative claim' until the search is done.
- Coordinator rejects or asks for revision: no fetching of any payload.

### Stage 1: Discovery

**Purpose.** List every candidate item and record its rights signals before acquiring any payload.

**Owner:** agent · **Sign-off:** dataset-agent · **G gates:** G0 · **Blocking:** yes

**What the agent does**

- Enumerate dumps, APIs, sitemaps, RSS feeds and channel upload playlists.
- Record per item: robots.txt (hashed), TDMRep, Content-Signal, and for video hosts the licence status and any training opt-in setting the host exposes.
- Start sources.jsonl (one row per source) and the per-item provenance ledger.
- Check every item's licence and its own terms. Treat a GPTBot, CCBot or Google-Extended block as a statement of intent: such hosts are IDs-only.
- Store a host's training opt-in setting as a filter column. It is off by default, so it is never treated as an opt-out.
- Screen Creative Commons uploaders for licence laundering: a provenance review per uploader, fingerprint matches against known rights-holder material, exclusion of uploaders who re-post mixed-licence material.
- Standard-licence items are released as Tier 2 (API metadata and IDs). Automatic captions are never used as transcripts.
- Probe 10-100 representative records, or the smallest permitted file, before any bulk run.

**Tools** (keys into `manual/tooling.lock.yaml`; `bayanatlabs:` = Bayanat Labs' own tools): `bayanatlabs:discover`

**Inputs:** `job:scoping_memo.yaml`; `job:job.json`; `legal_record:.`

**Outputs:** `job:sources.jsonl`; `job:PROVENANCE.parquet or PROVENANCE.jsonl (under 100k rows)`; `job:qa/reports/discovery.json`

**Gate.** Provenance ledger started; every item's licence and terms checked; training opt-in settings stored as a filter column; Creative Commons uploaders screened for licence laundering; every source has a tos_basis.

| Check | Machine-checkable expression |
|---|---|
| `S1.sources` | `exists(job:sources.jsonl)` |
| `S1.sources_schema` | `valid(job:sources.jsonl, templates/provenance_ledger_schema.json#/$defs/source_record)` |
| `S1.ledger_started` | `exists_any(job:PROVENANCE.parquet, job:PROVENANCE.jsonl)` |
| `S1.report` | `exists(job:qa/reports/discovery.json)` |
| `S1.red_excluded` | `job:qa/reports/discovery.json:red_items_included == 0` |
| `S1.tos_basis` | `job:qa/reports/discovery.json:sources_without_tos_basis == 0` |
| `S1.terms_read` | `job:qa/reports/discovery.json:sources_terms_not_reviewed == 0` |
| `S1.rights_signals` | `[if memo:third_party_sources is_true] job:qa/reports/discovery.json:items_missing_rights_signals == 0` |
| `S1.trainability_column` | `[if memo:uses_video_host is_true] job:qa/reports/discovery.json:video_host.trainability_stored_as_filter_column is_true` |
| `S1.laundering_screen` | `[if memo:uses_video_host is_true] job:qa/reports/discovery.json:video_host.cc_uploaders_unscreened == 0` |
| `S1.no_auto_captions` | `[if memo:uses_video_host is_true] job:qa/reports/discovery.json:video_host.auto_captions_used == 0` |
| `S1.probe` | `[if memo:third_party_sources is_true] job:qa/reports/discovery.json:probe_records >= 10` |

| Threshold | Default (a memo may tighten, never loosen) | Adopted from |
|---|---|---|
| `T1.probe` Probe before bulk | 10-100 records or the smallest permitted file | Bayanat Labs practice |
| `T1.cohorts` New source cohorts in parallel | at most 3 | Bayanat Labs practice |
| `T1.red` Items in scope whose licence or terms do not allow the release | 0 | Bayanat Labs practice |

**Stop conditions**

- robots.txt, TDMRep (tdm-reservation: 1) or Content-Signal (ai-train=no) reserves the content: the host is IDs-only.
- Terms unread for a source: read and file them before touching it.
- Licence laundering suspected on an uploader: exclude the uploader.
- Real personal data appears that the memo did not plan for: stop and ask the coordinator.

### Stage 2: Acquisition

**Purpose.** Fetch only what the memo allows, politely, resumably and with a checksum per object.

**Owner:** agent · **Sign-off:** dataset-agent, coordinator · **G gates:** G1 · **Blocking:** yes

**What the agent does**

- Fetch with the User-Agent BayanatLabs-OpenData/1.0 (+https://bayanatlabs.com/open; hello@bayanatlabs.com); never spoof a browser UA.
- At most 1 request per 3 s per host (1 per 5 s for government portals, small sites and slowing hosts); concurrency 1 per host; honour a longer Crawl-delay.
- Resumable downloads; SHA-256 per object; fetch timestamp and HTTP status per object; raw payloads in the content-addressed staging store.
- Hosts that block requests from outside Saudi Arabia only from the Bayanat Labs in-Kingdom host; never through proxies, VPNs or mirrors.
- Creative Commons video, only where the memo sets video_media_download and check S2.media_download_decision passes: yt-dlp with --download-archive, sleep and rate limits, one stable IP per worker; no proxy rotation, no CAPTCHA, WAF or bot-detection bypass, never personal cookies; residual terms-of-service risk recorded in the memo.
- Every Tier 2 item is covered by the collection basis named in the memo (academic partner under EU DSM Art. 3/4, written permission, or a recorded decision that permits it); scale stays capped until one exists.
- Tier 3: the partner's written permission is on file before collection, and its reference goes in permission_doc_id on every row (policy/tiers.yaml Tier 3).

**Tools** (keys into `manual/tooling.lock.yaml`; `bayanatlabs:` = Bayanat Labs' own tools): `bayanatlabs:fetch`, `yt-dlp`, `huggingface_hub`

**Inputs:** `job:sources.jsonl`; `job:job.json`; `legal_record:.`

**Outputs:** `job:intake/manifest.parquet`; `job:intake/objects/<sha256>`; `job:qa/reports/acquisition.json`

**Gate.** Raw store complete with a checksum and fetch timestamp per item; etiquette followed; access denials logged, never bypassed; every Tier 2 item covered by the named collection basis.

| Check | Machine-checkable expression |
|---|---|
| `S2.manifest` | `exists(job:intake/manifest.parquet)` |
| `S2.report` | `exists(job:qa/reports/acquisition.json)` |
| `S2.checksums` | `job:qa/reports/acquisition.json:items_with_sha256 == items_total` |
| `S2.timestamps` | `job:qa/reports/acquisition.json:items_with_retrieved_at == items_total` |
| `S2.user_agent` | `[if memo:third_party_sources is_true] job:qa/reports/acquisition.json:user_agent == "BayanatLabs-OpenData/1.0 (+https://bayanatlabs.com/open; hello@bayanatlabs.com)"` |
| `S2.rate` | `[if memo:third_party_sources is_true] job:qa/reports/acquisition.json:min_seconds_between_requests_per_host >= 3` |
| `S2.rate_gov` | `[if memo:third_party_sources is_true] job:qa/reports/acquisition.json:min_seconds_between_requests_government_or_small_hosts >= 5` |
| `S2.pinned_upstream` | `[if memo:third_party_sources is_false] job:qa/reports/acquisition.json:upstream_commit not_null` |
| `S2.concurrency` | `job:qa/reports/acquisition.json:max_concurrency_per_host <= 1` |
| `S2.denials_not_bypassed` | `job:qa/reports/acquisition.json:access_denials_bypassed == 0` |
| `S2.no_rotation` | `job:qa/reports/acquisition.json:proxy_or_ip_rotation_used is_false` |
| `S2.tier2_basis` | `job:qa/reports/acquisition.json:tier2_items_without_collection_basis == 0` |
| `S2.media_download_decision` | `[if memo:video_media_download is_true] row(legal_record:., decision_id=memo:media_download_decision_ref, nonempty=answer+effective_date+source)` |

| Threshold | Default (a memo may tighten, never loosen) | Adopted from |
|---|---|---|
| `T2.rate` Requests per host | at most 1 per 3 s; 1 per 5 s for government, small or slowing hosts; concurrency 1 | Bayanat Labs practice (slower than the 1 request per second also considered) |
| `T2.429` 429 handling | honour Retry-After, back off exponentially; after 3 consecutive 429s pause the host 24 h; never retry from another IP | Bayanat Labs practice |
| `T2.denials` 401/403/login/CAPTCHA/WAF | stop and log; source moves to permission_required | Bayanat Labs practice |
| `T2.first_party` First-party content | web-etiquette checks n/a only when every source is Bayanat Labs' own content (memo third_party_sources false); the upstream commit is pinned instead | approved by the founder for v1.0, 15 Oct 2026 |

**Stop conditions**

- HTTP 429: stop requesting from that host, honour Retry-After; after 3 consecutive 429s pause 24 h and log it.
- 401, 403, login wall, CAPTCHA or WAF challenge: stop, log the denial; never retry with another IP, account, cookie or mirror.
- Geo-blocked portal: use only the in-Kingdom host; if that is blocked too, stop and draft an official access request for the founder.
- Creative Commons video before the recorded decision that check S2.media_download_decision reads permits the download: the work stays at Tier 2 (IDs only) until it does.
- Tier 2 item without a named collection basis: do not scale beyond the pilot.
- Tier 3 source without the partner's written permission on file: do not collect.
- The approved compute or download budget is reached: stop and report the partial result.

### Stage 3: Normalisation

**Purpose.** Produce consistent, schema-valid records without destroying the original; for speech, segment and transcribe.

**Owner:** agent · **Sign-off:** dataset-agent · **G gates:** G2 · **Blocking:** yes

**What the agent does**

- Text: keep text_raw byte-exact, text_diac in NFC with diacritics, and derive text_norm with the Bayanat Labs normalisation recipe (presentation forms mapped, zero-width and bidi controls stripped except a meaningful ZWNJ, tatweel removed, alef variants to bare alef, alef maqsura to yaa, Arabic-Indic and Persian digits to ASCII, diacritics stripped with diacritization_ratio recorded); taa marbuta is kept and flagged in text_norm and folded only in text_search.
- Record normalisation_version (the Bayanat-Norm id from arabic-normalize once released) and the code commit.
- Language ID with GlotLID or fastText at the right unit (document, paragraph or segment); keep code-switch spans and cs_ratio.
- Audio: FLAC mono, 16 kHz for every non-consented release; higher-rate originals stay internal; loudness -20 dBFS in the release copy with parameters recorded.
- Speech segmentation and transcription (done here because stage 4 needs transcript MinHash and stage 5 drops clips with PII): Silero VAD into 2-20 s chunks; set music_flag (UVR-MDX-Net or Demucs only on music-flagged segments, for internal ASR only; music-flagged segments are excluded from audio releases); manual captions go to CTC forced alignment (ctc-forced-aligner with a commercially usable Arabic wav2vec2 model, never its default MMS model, which is non-commercial); without manual captions, dual ASR with Whisper large-v3 (faster-whisper) plus an Arabic second system whose licence allows release use in tooling.lock.yaml (NVIDIA FastConformer Arabic pc, or Nemotron 3.5 ASR fine-tuned on our own pseudo-labels; the pcd variant was trained partly on recitation audio whose licence is unclear), keeping a segment only if cer_between_systems <= 15% and labelling it silver. Never auto-captions.
- Validate 100% of records against the text or speech release schema.

**Tools** (keys into `manual/tooling.lock.yaml`; `bayanatlabs:` = Bayanat Labs' own tools): `bayanatlabs:arabic-normalize`, `camel-tools`, `fasttext`, `glotlid`, `ffmpeg`, `silero-vad`, `demucs`, `audio-separator`, `uvr-mdx-net-models`, `faster-whisper`, `faster-whisper-large-v3`, `whisper-large-v3`, `nemo_toolkit`, `nvidia-ar-fastconformer-pc`, `nemotron-3.5-asr`, `ctc-forced-aligner`, `wav2vec2-xlsr-53-arabic`

**Inputs:** `job:intake/manifest.parquet`

**Outputs:** `job:transforms/recipes/`; `job:validation/schema_report.json`

**Gate.** Schema validation passes on 100% of records; the normalisation version is recorded; raw and normalised fields sit side by side; speech transcripts come from manual captions or dual-ASR agreement (CER <= 15%), never auto-captions.

| Check | Machine-checkable expression |
|---|---|
| `S3.report` | `exists(job:validation/schema_report.json)` |
| `S3.all_valid` | `job:validation/schema_report.json:records_valid == records_total` |
| `S3.norm_version` | `job:validation/schema_report.json:normalisation_version not_null` |
| `S3.raw_kept` | `job:validation/schema_report.json:records_missing_raw_field == 0` |
| `S3.sample_rate` | `[if memo:modalities contains "speech" and memo:consented_audio is_false] job:validation/schema_report.json:audio.max_release_sample_rate_hz <= 16000` |
| `S3.no_auto_captions` | `[if memo:profile in ["P-SPEECH"]] job:validation/schema_report.json:audio.segments_from_auto_captions == 0` |
| `S3.dual_asr` | `[if memo:profile in ["P-SPEECH"]] job:validation/schema_report.json:audio.max_cer_between_systems_kept <= 0.15` |
| `S3.music_excluded` | `[if memo:profile in ["P-SPEECH"]] job:validation/schema_report.json:audio.music_flagged_segments_in_release == 0` |

| Threshold | Default (a memo may tighten, never loosen) | Adopted from |
|---|---|---|
| `T3.schema` Schema validation | 100% of records | Bayanat Labs practice |
| `T3.recipe` text_norm recipe | the Bayanat Labs normalisation recipe (NFKC-based, taa marbuta kept and flagged). The alternative 'Bayanat-Norm v1 = NFC plus presentation-form mapping' is recorded as choice C-03 and needs founder approval before it replaces this recipe. | Bayanat Labs practice |
| `T3.audio` Release audio | FLAC mono 16 kHz (48 kHz only for consented or public-domain sets); -20 dBFS | Bayanat Labs practice |
| `T3.dual_asr` Dual-ASR agreement | keep a segment only if cer_between_systems <= 15%; label it silver | Bayanat Labs practice |
| `T3.vad` VAD chunks | 2-20 s | Bayanat Labs practice |

**Stop conditions**

- A task needs a distinction that text_norm folds (OCR, vocalisation, phonology): use text_raw or text_diac and say so in the memo; never fold silently.
- Records fail validation: fix the transform and re-run; never drop failing records silently (count them by reason).

### Stage 4: Deduplication

**Purpose.** Remove duplicates and make sure no benchmark test item leaks into a training release.

**Owner:** agent · **Sign-off:** dataset-agent · **G gates:** G2 · **Blocking:** yes

**What the agent does**

- Text: exact SHA-256, then normalised text, then MinHash-LSH on text_norm (5-gram, Jaccard 0.8), then shared source, template, author or workflow group; keep dedup_group.
- Audio: Chromaprint fingerprints plus transcript MinHash.
- Cross-check against OpenITI, FineWeb-2 ar, YODAS, SADA, MASC and every public test set in scope, including Bayanat Labs' own published evaluation sets and fixtures.
- Report the duplicate rate and the language-ID statistics from stage 3, and compare them with the memo's ranges (ranges.duplicate_rate_max, ranges.langid_min_share over ranges.expected_languages).

**Tools** (keys into `manual/tooling.lock.yaml`; `bayanatlabs:` = Bayanat Labs' own tools): `datasketch`, `datatrove`, `chromaprint`, `pyacoustid`

**Inputs:** `job:validation/schema_report.json`

**Outputs:** `job:qa/reports/dedup.json`

**Gate.** Duplicate rate and language-ID statistics reported and inside the memo's ranges; zero overlap between any benchmark test set and any training release.

| Check | Machine-checkable expression |
|---|---|
| `S4.report` | `exists(job:qa/reports/dedup.json)` |
| `S4.dup_rate` | `job:qa/reports/dedup.json:duplicate_rate <= memo:ranges.duplicate_rate_max` |
| `S4.langid` | `job:qa/reports/dedup.json:langid.expected_language_share >= memo:ranges.langid_min_share` |
| `S4.test_overlap` | `job:qa/reports/dedup.json:test_set_overlap_items == 0` |
| `S4.cross_dedup` | `job:qa/reports/dedup.json:cross_dedup_targets_missing == 0` |

| Threshold | Default (a memo may tighten, never loosen) | Adopted from |
|---|---|---|
| `T4.minhash` Near-duplicate threshold | MinHash-LSH, 5-gram, Jaccard >= 0.8 on text_norm | Bayanat Labs practice |
| `T4.overlap` Benchmark test-set overlap with training releases | 0 | Bayanat Labs practice (gate G2) |
| `T4.ranges` Duplicate rate and language-ID share | inside the memo's ranges (ranges.duplicate_rate_max, ranges.langid_min_share) | gate G2 ('statistics in range') |

**Stop conditions**

- Any test-set overlap: remove the items from the training release, or rotate the test set; never ship with overlap.
- Version conflict is itself the task: keep conflicting versions with their dedup_group instead of deleting them.

### Stage 5: Safety and PII

**Purpose.** Remove personal data and unsafe content before anything leaves the Kingdom-side staging store.

**Owner:** agent · **Sign-off:** dataset-agent, coordinator · **G gates:** G3 · **Blocking:** yes

**What the agent does**

- Regex pack for Saudi and GCC IDs, Iqama, Emirates ID, IBANs, phones in both digit scripts, plates, emails and URLs with personal paths; Arabic NER for person names in user-generated content; Presidio with the Bayanat Labs Arabic recogniser pack.
- Text: replace PII with typed placeholders. Audio: drop clips with PII; never bleep.
- Images and video: CSAM hash checks through link-and-hash methods that never touch suspect items; NSFW classifier; blur faces and plates; strip EXIF and GPS.
- Toxicity and NSFW flags: a human reviews 100% of flagged items. Once a toxicity classifier is pinned in tooling.lock.yaml, safety.json records its key and S5.flags_reviewed is read with it; until then a pass with no classifier is vacuous and is reported as such.
- Drop any clip or image in which a child is identifiable, and log the count only. No child-speech, face or biometric set is built; the only exception is consented sign-language video.
- Run re-identification tests R1-R7.
- Run the 3,000-record stratified PII audit. It must pass before any upload to a host outside KSA/UAE (Hugging Face, GitHub, Zenodo), private repos included.

**Tools** (keys into `manual/tooling.lock.yaml`; `bayanatlabs:` = Bayanat Labs' own tools): `presidio-analyzer`, `presidio-anonymizer`, `bayanatlabs:arabic-recogniser-pack`

**Inputs:** `job:qa/reports/dedup.json`

**Outputs:** `job:qa/reports/pii_audit.json`; `job:qa/reports/reid.json`; `job:qa/reports/safety.json`

**Gate.** Zero PII hits in a 3,000-record stratified audit (a residual rate under 0.1% on the first 1,000 is also reported); R1-R7 pass; no sensitive-category labels; faces and plates blurred; no minors; audit passed before any upload outside KSA/UAE.

| Check | Machine-checkable expression |
|---|---|
| `S5.audit_file` | `exists(job:qa/reports/pii_audit.json, job:qa/reports/reid.json, job:qa/reports/safety.json)` |
| `S5.audit_n` | `job:qa/reports/pii_audit.json:n >= 3000` |
| `S5.audit_stratified` | `job:qa/reports/pii_audit.json:stratified is_true` |
| `S5.audit_hits` | `job:qa/reports/pii_audit.json:hits == 0` |
| `S5.cr_rate_reported` | `job:qa/reports/pii_audit.json:cr_first_1000.residual_rate < 0.001` |
| `S5.before_upload` | `job:qa/reports/pii_audit.json:passed_before_any_upload is_true` |
| `S5.reid` | `job:qa/reports/reid.json:failed_tests == 0` |
| `S5.reid_complete` | `job:qa/reports/reid.json:tests_not_completed_count == 0` |
| `S5.sensitive_labels` | `job:qa/reports/reid.json:sensitive_category_fields == 0` |
| `S5.minors` | `job:qa/reports/safety.json:identifiable_minor_items_remaining == 0` |
| `S5.flags_reviewed` | `job:qa/reports/safety.json:flagged_items_without_human_decision == 0` |
| `S5.faces_plates` | `[if memo:has_images is_true] job:qa/reports/safety.json:images.unblurred_faces_or_plates == 0` |
| `S5.csam` | `[if memo:has_images is_true] job:qa/reports/safety.json:images.csam_hash_check_done is_true` |
| `S5.exif` | `[if memo:has_images is_true] job:qa/reports/safety.json:images.exif_or_gps_remaining == 0` |

| Threshold | Default (a memo may tighten, never loosen) | Adopted from |
|---|---|---|
| `T5.pii` PII audit | 0 hits in >= 3,000 stratified records (95% upper bound about 0.1%) | Bayanat Labs practice Also reported: residual PII < 0.1% on a 1,000-item audit. |
| `T5.k` Quasi-identifier groups (R2) | every group >= 5 records, else coarsen or drop | Bayanat Labs practice |
| `T5.voice` Voice linkage (R4) | 0 names in a 500-segment sample | Bayanat Labs practice |
| `T5.images` Image check (R6) | 100% of a 300-item check passes | Bayanat Labs practice |
| `T5.flags` Toxicity, NSFW and PII flags | 100% human-reviewed | Bayanat Labs practice |

**Stop conditions**

- Any PII hit in the audit: fix the cause, redact or drop, and re-audit on a fresh stratified sample. No upload outside KSA/UAE until it passes.
- CSAM hash match: do not open, view or redistribute; quarantine the reference; notify the founder at once.
- Probable child voice or image: drop before release and log the count, never the content.
- Residual PII found after release: stop serving the affected files within 24 h and move the release to index-only until fixed. An index entry that itself carries personal data is removed, not kept (policy index-only rule IO-4).

### Stage 6: Enrichment

**Purpose.** Add labels and quality signals, each marked with where it came from.

**Owner:** agent · **Sign-off:** dataset-agent, native-reviewer · **G gates:** G4 · **Blocking:** yes

**What the agent does**

- Dialect or country top-3 with probabilities (text dialect ID, ADI-20 speech models, channel geography), each with its label origin. Only models cleared for the release path in tooling.lock.yaml may produce released labels; the others give internal pre-labels for human review.
- pyannote speaker pseudo-IDs, salted per release.
- gender_est and city_hint, labelled as estimates; never presented as fact.
- DNSMOS P.835, SNR and bandwidth; the TorchAudio-SQUIM objective model (squim-objective, CC BY 4.0) as a second proxy, never the subjective model (squim-subjective, non-commercial); topics; code-switch ratio; length statistics.
- LLM suggestions (Qwen3 or ALLaM via vLLM) for punctuation and labels only with a 5% CER change guard; record annotation_origin.

**Tools** (keys into `manual/tooling.lock.yaml`; `bayanatlabs:` = Bayanat Labs' own tools): `pyannote.audio`, `pyannote-community-1`, `adi20-whisper`, `sentence-aldi`, `camelbert-did-nadi`, `camelbert-did-madar26`, `camel-tools`, `dnsmos`, `onnxruntime`, `torchaudio`, `squim-objective`, `vllm`, `qwen3-8b`, `allam-7b-instruct`

**Inputs:** `job:qa/reports/pii_audit.json`

**Outputs:** `job:annotations/`; `job:qa/reports/labels.json`

**Gate.** Label distribution report exists; a manual spot-check of at least 1% per dialect by speakers of that dialect is done; every label carries annotation_origin.

| Check | Machine-checkable expression |
|---|---|
| `S6.report` | `exists(job:qa/reports/labels.json)` |
| `S6.distribution` | `job:qa/reports/labels.json:label_distribution exists` |
| `S6.spotcheck` | `job:qa/reports/labels.json:min_spotcheck_fraction_per_dialect >= 0.01` |
| `S6.native_dialect` | `job:qa/reports/labels.json:spotchecks_by_non_dialect_speakers == 0` |
| `S6.origin` | `job:qa/reports/labels.json:labels_missing_annotation_origin == 0` |
| `S6.estimates` | `job:qa/reports/labels.json:estimates_presented_as_fact == 0` |
| `S6.llm_guard` | `[if memo:uses_llm_suggestions is_true] job:qa/reports/labels.json:llm_edits_over_cer_guard == 0` |

| Threshold | Default (a memo may tighten, never loosen) | Adopted from |
|---|---|---|
| `T6.spotcheck` Dialect spot-check | >= 1% per dialect label, by speakers of that dialect | Bayanat Labs practice; gate G5 (speakers of that dialect) |
| `T6.llm` LLM change guard | reject any change that moves CER by more than 5% | Bayanat Labs practice |
| `T6.dnsmos` Speech quality floor | dnsmos_ovrl >= 3.0 unless the memo sets a stricter value | Bayanat Labs practice |

**Stop conditions**

- Systematic dialect errors in the spot-check: fix and re-audit the stratum before stage 7.
- A label encodes a sensitive category about a person: remove the field (back to stage 5).

### Stage 7: Human QA

**Purpose.** Measure quality with paid native reviewers on a stratified sample fixed in the memo, and record a named sign-off.

**Owner:** agent · **Sign-off:** native-reviewer, coordinator · **G gates:** G4, G5 · **Blocking:** yes

**What the agent does**

- Guideline calibration on 50 records before scaling; rater instructions in Arabic.
- Text or label QA: 1,000 records per subset, stratified, never below 200 per stratum family. Speech: the larger of 2% of segments (memo picks 2-5%) and 2 h per subset.
- Transcripts: CER against gold. Labels: agreement. PII: re-check.
- Three raters adjudicate disagreements; store adjudicated labels.
- Report counts and error rates per stratum with 95% intervals; zero errors in n bounds the error at about 3/n, not zero.
- A named native reviewer signs off; dialect labels are checked by speakers of that dialect. Automated review may screen internal pilots only.

**Tools** (keys into `manual/tooling.lock.yaml`; `bayanatlabs:` = Bayanat Labs' own tools): `bayanatlabs:qa-sampler`

**Inputs:** `job:qa/reports/labels.json`; `job:scoping_memo.yaml`

**Outputs:** `job:qa/reports/qa_report.json`; `job:qa/reports/QA_REPORT.md`; `job:qa/signoff.yaml`

**Gate.** Agreement meets the memo threshold (floor kappa 0.6, 0.7 for eval sets); sample sizes meet the T7 minimums; a named native reviewer signs; the QA report goes into the card.

| Check | Machine-checkable expression |
|---|---|
| `S7.report` | `exists(job:qa/reports/qa_report.json, job:qa/reports/QA_REPORT.md)` |
| `S7.kappa_floor` | `job:qa/reports/qa_report.json:kappa >= 0.6` |
| `S7.kappa_eval` | `[if memo:qa.is_eval_set is_true] job:qa/reports/qa_report.json:kappa >= 0.7` |
| `S7.kappa_memo` | `job:qa/reports/qa_report.json:kappa >= memo:qa.agreement_threshold` |
| `S7.sample` | `job:qa/reports/qa_report.json:sample_size >= memo:qa.sample_size` |
| `S7.calibration` | `job:qa/reports/qa_report.json:calibration_batch >= 50` |
| `S7.intervals` | `job:qa/reports/qa_report.json:per_stratum_intervals_reported is_true` |
| `S7.native_signoff` | `signoff(job:qa/signoff.yaml:native_reviewer, role=native-reviewer, verdict=approve)` |
| `S7.dialect_signoff` | `job:qa/signoff.yaml:dialects_without_native_checker == 0` |

| Threshold | Default (a memo may tighten, never loosen) | Adopted from |
|---|---|---|
| `T7.kappa` Agreement floor | kappa >= 0.6 (>= 0.7 for eval sets), or the stricter memo threshold | gate G4; Bayanat Labs practice |
| `T7.text_sample` Text or label sample | 1,000 records per subset; >= 200 per stratum family | Bayanat Labs practice |
| `T7.speech_sample` Speech sample | max(2% of segments, 2 h) per subset; capping below needs founder approval | Bayanat Labs practice (larger than the '1,000 records or 2 hours' also considered) |
| `T7.calibration` Guideline calibration | 50 records before scaling | Bayanat Labs practice |
| `T7.synthetic` Synthetic data verified by natives | >= 5% (>= 10% for eval sets) | Bayanat Labs practice |
| `T7.ocr` Documents and OCR | 300 pages checked by a human plus baseline-OCR CER | Bayanat Labs practice |
| `T7.tiebreak` Commercial ASR tie-breaker sample | 5% sample, only from vendors whose terms allow it | Bayanat Labs practice |

**Stop conditions**

- Agreement below threshold: fix the guideline, relabel the pilot and re-measure; never lower the threshold.
- No named native reviewer available: status blocked_founder (reviewer pay is a founder action).
- Sample would have to be capped below the T7 minimums: needs written founder approval, recorded as a deviation.

### Stage 8: Packaging

**Purpose.** Build a release candidate that loads, renders, carries its licences and passes the card linter.

**Owner:** agent · **Sign-off:** dataset-agent, coordinator · **G gates:** G6, G7 · **Blocking:** yes

**What the agent does**

- Parquet shards <= 500 MB (speech: Parquet with the HF Audio feature up to 1 TB; WebDataset above that or when the memo chooses it); one config per licence.
- MANIFEST.json, SHA256SUMS, LICENSE, LICENSES/ with LICENSE-sources.md, PROVENANCE.parquet (JSONL under 100k rows), CLAIMS.md, CHANGELOG.md, CITATION.cff.
- Bilingual card (README.md + README.ar.md) from the Bayanat Labs dataset template: FineWeb's 11 sections plus Bayanat Labs' 5, the QA report, re-identification results and the manual_version in the Creation section.
- Croissant fetched from the HF API, validated with mlcroissant and committed as croissant.json.
- Licence compatibility check; SA and NC obligations propagated; every item whose release needs a recorded legal decision cites the decision ID that permits it (decision_ref). Without one, the item ships at Tier 2 (IDs only) or is dropped, and the point is noted in the job's work log.
- Re-download into a clean environment and verify checksums, datasets.load_dataset, the viewer and the documented example.

**Tools** (keys into `manual/tooling.lock.yaml`; `bayanatlabs:` = Bayanat Labs' own tools): `bayanatlabs:bl-card-lint`, `bayanatlabs:bl-manifest`, `mlcroissant`, `huggingface_hub`, `datasets`

**Inputs:** `job:qa/reports/qa_report.json`

**Outputs:** `hf_repo:README.md`; `hf_repo:README.ar.md`; `hf_repo:CLAIMS.md`; `hf_repo:MANIFEST.json`; `hf_repo:SHA256SUMS`; `hf_repo:croissant.json`; `job:qa/reports/package.json`; `job:qa/reports/licence_check.json`

**Gate.** Viewer renders; datasets.load_dataset works in a clean environment; card linter passes; licence compatibility checked with obligations propagated; every item that needs a recorded legal decision cites it; required files present.

| Check | Machine-checkable expression |
|---|---|
| `S8.files` | `exists(hf_repo:README.md, hf_repo:README.ar.md, hf_repo:CLAIMS.md, hf_repo:LICENSE, hf_repo:LICENSES/LICENSE-sources.md, hf_repo:CITATION.cff, hf_repo:CHANGELOG.md, hf_repo:MANIFEST.json, hf_repo:SHA256SUMS, hf_repo:croissant.json)` |
| `S8.provenance` | `exists_any(hf_repo:PROVENANCE.parquet, hf_repo:PROVENANCE.jsonl)` |
| `S8.builder_files` | `exists(gh_repo:README.md, gh_repo:LICENSE, gh_repo:CITATION.cff, gh_repo:CHANGELOG.md, gh_repo:job.json)` |
| `S8.no_data_in_gh` | `absent(gh_repo:data/**, gh_repo:**/*.parquet, gh_repo:**/*.arrow, gh_repo:**/*.jsonl, gh_repo:**/*.flac, gh_repo:**/*.wav, gh_repo:**/*.mp3, gh_repo:**/*.opus, gh_repo:**/*.tar) except tests/**` |
| `S8.provenance_schema` | `valid(hf_repo:PROVENANCE.parquet\|PROVENANCE.jsonl, templates/provenance_ledger_schema.json)` |
| `S8.viewer` | `job:qa/reports/package.json:viewer_renders is_true` |
| `S8.loader` | `job:qa/reports/package.json:load_dataset_clean_env_ok is_true` |
| `S8.lint` | `job:qa/reports/package.json:card_lint_errors == 0` |
| `S8.croissant` | `job:qa/reports/package.json:croissant_valid is_true` |
| `S8.checksums` | `job:qa/reports/package.json:checksum_mismatches == 0` |
| `S8.manual_version` | `job:qa/reports/package.json:card_manual_version not_null` |
| `S8.licence` | `job:qa/reports/licence_check.json:incompatible_items == 0` |
| `S8.obligations` | `job:qa/reports/licence_check.json:sa_nc_obligations_propagated is_true` |
| `S8.decision_cited` | `job:qa/reports/licence_check.json:items_without_decision_ref == 0` |
| `S8.undecided_points_logged` | `job:qa/reports/licence_check.json:undecided_points_not_logged == 0` |
| `S8.release_tools` | `job:qa/reports/licence_check.json:blocked_tools_on_release_path == 0` |
| `S8.synthetic_labelled` | `job:qa/reports/package.json:synthetic_records_unlabelled == 0` |
| `S8.claims_draft` | `exists(gh_repo:qa/reports/numbers.json)` |

| Threshold | Default (a memo may tighten, never loosen) | Adopted from |
|---|---|---|
| `T8.shards` Shard size | <= 500 MB Parquet; WebDataset tar <= 8 GB | Bayanat Labs practice |
| `T8.github` GitHub files | < 100 MiB; data never in git | Bayanat Labs practice |
| `T8.manifests` Files per folder | fewer than 10k | Bayanat Labs practice |

**Stop conditions**

- Licence incompatibility: split into one config per licence or drop the incompatible part; never flatten licences.
- A tool or model with an NC or unknown licence produced released artefacts: rebuild without it.
- Viewer or loader fails in a clean environment: fix before stage 9.

### Stage 9: Baseline or benchmark

**Purpose.** Give every release a number a journalist can print, computed by a script from the released files.

**Owner:** agent · **Sign-off:** dataset-agent · **G gates:** G7 · **Blocking:** yes

**What the agent does**

- Train or evaluate something on it: Whisper fine-tune, retrieval nDCG, OCR CER or classifier F1. Any model is labelled 'reference baseline, not a product'.
- Draw the chart from a script and put it in the card.
- Benchmarks: public dev/test plus a hidden test split, canary GUID, immutable versions, human-ceiling and baseline scores.

**Tools** (keys into `manual/tooling.lock.yaml`; `bayanatlabs:` = Bayanat Labs' own tools): `bayanatlabs:eval`, `lighteval`, `lm_eval`, `nemotron-3.5-asr`

**Inputs:** `hf_repo:MANIFEST.json`

**Outputs:** `gh_repo:eval/results.json`; `gh_repo:launch/chart.png`

**Gate.** A script-computed number exists that a journalist can print, with its chart and the script that draws it.

| Check | Machine-checkable expression |
|---|---|
| `S9.results` | `exists(gh_repo:eval/results.json, gh_repo:launch/chart.png)` |
| `S9.number` | `gh_repo:eval/results.json:headline_metric.value not_null` |
| `S9.script` | `gh_repo:eval/results.json:script_sha256 not_null` |
| `S9.label` | `gh_repo:eval/results.json:model_label in ["reference baseline, not a product", "no model trained"]` |
| `S9.canary` | `[if memo:qa.is_eval_set is_true] gh_repo:eval/results.json:canary_guid not_null` |

| Threshold | Default (a memo may tighten, never loosen) | Adopted from |
|---|---|---|
| `T9.number` Printable number | at least one script-computed headline metric | Bayanat Labs practice |

**Stop conditions**

- No number can be computed: the release does not ship.
- The benchmark charter is not written before the run: write it first.

### Stage 10: Release

**Purpose.** Prepare every release item, re-verify claims on the day, and release only on the founder's go.

**Owner:** coordinator · **Sign-off:** coordinator, founder · **G gates:** G7 · **Blocking:** yes

**What the agent does**

- Prepare the hub page draft with JSON-LD and the paid-family link, the HF repo, a reserved Zenodo DOI, Kaggle and Masader listing drafts, and the launch bundle drafts in outbox/.
- Re-verify every superlative on release day in CLAIMS.md; page, card and archive must agree.
- The coordinator runs coordinator/launch_bundle_checklist.md.
- The founder gives the go; only then do repos go public, the DOI get minted and listings get submitted.

**Tools** (keys into `manual/tooling.lock.yaml`; `bayanatlabs:` = Bayanat Labs' own tools): `bayanatlabs:bl-gates`, `bayanatlabs:bl-card-render`, `huggingface_hub`

**Inputs:** `job:qa/reports/gates.json`

**Outputs:** `job:qa/reports/release_checklist.json`; `job:signoffs/founder_go.yaml`; `job:outbox/ (launch bundle drafts)`

**Gate.** Coordinator runs the launch-bundle checklist; claims re-verified on release day (G7); the founder's go is recorded.

| Check | Machine-checkable expression |
|---|---|
| `S10.gates` | `job:qa/reports/gates.json:failed == 0` |
| `S10.checklist` | `job:qa/reports/release_checklist.json:unchecked_items == 0` |
| `S10.checklist_signoff` | `signoff(job:qa/reports/release_checklist.json:coordinator, role=coordinator, verdict=approve)` |
| `S10.claims_day` | `job:qa/reports/release_checklist.json:claims_reverified_on not_null` |
| `S10.agree` | `job:qa/reports/release_checklist.json:page_card_archive_mismatches == 0` |
| `S10.founder_go` | `signoff(job:signoffs/founder_go.yaml:founder, role=founder, verdict=go)` |

| Threshold | Default (a memo may tighten, never loosen) | Adopted from |
|---|---|---|
| `T10.day` Release day | Tuesday or Wednesday | Bayanat Labs release practice |
| `T10.claims` Claims re-verification | on release day | gate G7 |

**Stop conditions**

- Founder says no-go: the release stays ready_to_publish; nothing is made public.
- A claim fails re-verification: remove the superlative from every copy before launch.

### Stage 11: Promotion and measurement

**Purpose.** Get the release seen and measure whether it is used.

**Owner:** coordinator · **Sign-off:** coordinator · **G gates:** none (coordinator check) · **Blocking:** yes

**What the agent does**

- Agents draft posts, press notes, community posts and outreach; the founder sends or posts them.
- Within 7 days: fix card issues, add 'models trained on it' links, schedule the refresh.
- Add the release's row to the monthly metrics digest; at day 30 apply the 30-day rule.

**Tools** (keys into `manual/tooling.lock.yaml`; `bayanatlabs:` = Bayanat Labs' own tools): `bayanatlabs:metrics-digest`

**Inputs:** `job:signoffs/founder_go.yaml`

**Outputs:** `programme:coordinator/metrics_digest.jsonl`

**Gate.** A metrics row for the release is added to the digest and validates against coordinator/metrics_digest_row.schema.json.

| Check | Machine-checkable expression |
|---|---|
| `S11.row` | `row(programme:coordinator/metrics_digest.jsonl, asset_id=memo:candidate_id)` |

*Coordinator check:* Metrics row present and schema-valid (no release gate G0-G7 covers promotion).

| Threshold | Default (a memo may tighten, never loosen) | Adopted from |
|---|---|---|
| `T11.followup` Post-launch fixes | within 7 days | Bayanat Labs practice |
| `T11.review` Usage review | day 30 (30-day rule) | Bayanat Labs release practice |

**Stop conditions**

- Never claim a listing, acceptance or backlink before it exists.
- A channel produced nothing across three consecutive launches: drop it from the default bundle (provisional rule).

### Stage 12: Maintenance

**Purpose.** Keep the release lawful, correct and current, and set the next version date.

**Owner:** coordinator · **Sign-off:** coordinator, founder · **G gates:** none (coordinator check) · **Blocking:** yes

**What the agent does**

- Prune removed, private or re-licensed items from manifests every 30 days; refresh or delete stored API data as each API's terms require.
- Takedowns: acknowledge within 2 business days, remove within 30 days; platform requests within 24 h; PII, child-safety or CSAM reports within 24 h.
- Quarterly refresh with a dated snapshot and changelog; re-verify every source licence and re-run the claims check for each new version.
- Rotate a leaked benchmark test set within 30 days; remove withdrawn partner content within the SLA and correct the public counter.
- At each version, review every index-only trigger of the policy (IO-1 terms changed, IO-2 takedown, IO-3 video no longer CC, IO-4 residual PII, IO-5 unreadable portal licence) and record the review in qa/reports/maintenance.json.

**Tools** (keys into `manual/tooling.lock.yaml`; `bayanatlabs:` = Bayanat Labs' own tools): `bayanatlabs:maintenance-calendar`

**Inputs:** `programme:coordinator/maintenance_calendar.md`; policy/index-only-rules.yaml (triggers IO-1 to IO-5)

**Outputs:** `job:job.json`; `job:qa/reports/maintenance.json`; `hf_repo:CHANGELOG.md`

**Gate.** The next version date is set in job.json and on the release calendar; the policy's index-only triggers IO-1 to IO-5 were reviewed for this version.

| Check | Machine-checkable expression |
|---|---|
| `S12.next_version` | `job:job.json:release.next_version_date not_null` |
| `S12.calendar` | `row(programme:coordinator/release_calendar.jsonl, item_id=memo:candidate_id, kind=next_version)` |
| `S12.changelog` | `exists(hf_repo:CHANGELOG.md)` |
| `S12.index_only_review` | `job:qa/reports/maintenance.json:index_only_review.triggers_not_reviewed == 0` |
| `S12.index_only_date` | `job:qa/reports/maintenance.json:index_only_review.reviewed_on not_null` |

*Coordinator check:* Next version date set; index-only triggers reviewed; maintenance calendar entries created (no release gate G0-G7 covers maintenance).

| Threshold | Default (a memo may tighten, never loosen) | Adopted from |
|---|---|---|
| `T12.manifest_refresh` Manifest pruning and API data refresh | every 30 days | Bayanat Labs practice; the terms of the APIs used |
| `T12.takedown` Takedown | ack 2 business days; removal <= 30 days; platform <= 24 h; PII/child-safety/CSAM <= 24 h | Bayanat Labs practice |
| `T12.leak` Leaked test set | rotated within 30 days | Bayanat Labs practice |
| `T12.refresh` Scheduled refresh | quarterly | Bayanat Labs practice |
| `T12.index_only` Index-only triggers | IO-1 to IO-5 reviewed at each version and on the monthly licence spot-check | policy/index-only-rules.yaml |

**Stop conditions**

- Video no longer CC at re-verification, terms changed, takedown hit, residual PII or unreadable portal licence: move the affected items to index-only (Tier 2). An index entry that itself carries personal data is removed, not kept (policy index-only rule IO-4).
- History purge or deletion of published data: founder approval only.
- Takedown dispute or legal threat: never argue publicly; send to the founder.

## 4. Thresholds

All defaults, by stage. A memo may tighten any of them; loosening needs written founder approval, logged in the memo's deviations block. Where the sources behind a threshold gave different values, `manual/gate-crosswalk.md` records the value adopted and the alternative.

| Id | Stage | Threshold | Default | Adopted from |
|---|---|---|---|---|
| `T0.legal` | 0 | Legal tier allowed to proceed | green or yellow; red is not built | policy/rubric.yaml legal gate |
| `T0.tighten_only` | 0 | Memo overrides | tighten only; loosening needs written founder approval | Bayanat Labs practice |
| `T1.probe` | 1 | Probe before bulk | 10-100 records or the smallest permitted file | Bayanat Labs practice |
| `T1.cohorts` | 1 | New source cohorts in parallel | at most 3 | Bayanat Labs practice |
| `T1.red` | 1 | Items in scope whose licence or terms do not allow the release | 0 | Bayanat Labs practice |
| `T2.rate` | 2 | Requests per host | at most 1 per 3 s; 1 per 5 s for government, small or slowing hosts; concurrency 1 | Bayanat Labs practice (slower than the 1 request per second also considered) |
| `T2.429` | 2 | 429 handling | honour Retry-After, back off exponentially; after 3 consecutive 429s pause the host 24 h; never retry from another IP | Bayanat Labs practice |
| `T2.denials` | 2 | 401/403/login/CAPTCHA/WAF | stop and log; source moves to permission_required | Bayanat Labs practice |
| `T2.first_party` | 2 | First-party content | web-etiquette checks n/a only when every source is Bayanat Labs' own content (memo third_party_sources false); the upstream commit is pinned instead | approved by the founder for v1.0, 15 Oct 2026 |
| `T3.schema` | 3 | Schema validation | 100% of records | Bayanat Labs practice |
| `T3.recipe` | 3 | text_norm recipe | the Bayanat Labs normalisation recipe (NFKC-based, taa marbuta kept and flagged). The alternative 'Bayanat-Norm v1 = NFC plus presentation-form mapping' is recorded as choice C-03 and needs founder approval before it replaces this recipe. | Bayanat Labs practice |
| `T3.audio` | 3 | Release audio | FLAC mono 16 kHz (48 kHz only for consented or public-domain sets); -20 dBFS | Bayanat Labs practice |
| `T3.dual_asr` | 3 | Dual-ASR agreement | keep a segment only if cer_between_systems <= 15%; label it silver | Bayanat Labs practice |
| `T3.vad` | 3 | VAD chunks | 2-20 s | Bayanat Labs practice |
| `T4.minhash` | 4 | Near-duplicate threshold | MinHash-LSH, 5-gram, Jaccard >= 0.8 on text_norm | Bayanat Labs practice |
| `T4.overlap` | 4 | Benchmark test-set overlap with training releases | 0 | Bayanat Labs practice (gate G2) |
| `T4.ranges` | 4 | Duplicate rate and language-ID share | inside the memo's ranges (ranges.duplicate_rate_max, ranges.langid_min_share) | gate G2 ('statistics in range') |
| `T5.pii` | 5 | PII audit | 0 hits in >= 3,000 stratified records (95% upper bound about 0.1%) | Bayanat Labs practice |
| `T5.k` | 5 | Quasi-identifier groups (R2) | every group >= 5 records, else coarsen or drop | Bayanat Labs practice |
| `T5.voice` | 5 | Voice linkage (R4) | 0 names in a 500-segment sample | Bayanat Labs practice |
| `T5.images` | 5 | Image check (R6) | 100% of a 300-item check passes | Bayanat Labs practice |
| `T5.flags` | 5 | Toxicity, NSFW and PII flags | 100% human-reviewed | Bayanat Labs practice |
| `T6.spotcheck` | 6 | Dialect spot-check | >= 1% per dialect label, by speakers of that dialect | Bayanat Labs practice; gate G5 (speakers of that dialect) |
| `T6.llm` | 6 | LLM change guard | reject any change that moves CER by more than 5% | Bayanat Labs practice |
| `T6.dnsmos` | 6 | Speech quality floor | dnsmos_ovrl >= 3.0 unless the memo sets a stricter value | Bayanat Labs practice |
| `T7.kappa` | 7 | Agreement floor | kappa >= 0.6 (>= 0.7 for eval sets), or the stricter memo threshold | gate G4; Bayanat Labs practice |
| `T7.text_sample` | 7 | Text or label sample | 1,000 records per subset; >= 200 per stratum family | Bayanat Labs practice |
| `T7.speech_sample` | 7 | Speech sample | max(2% of segments, 2 h) per subset; capping below needs founder approval | Bayanat Labs practice (larger than the '1,000 records or 2 hours' also considered) |
| `T7.calibration` | 7 | Guideline calibration | 50 records before scaling | Bayanat Labs practice |
| `T7.synthetic` | 7 | Synthetic data verified by natives | >= 5% (>= 10% for eval sets) | Bayanat Labs practice |
| `T7.ocr` | 7 | Documents and OCR | 300 pages checked by a human plus baseline-OCR CER | Bayanat Labs practice |
| `T7.tiebreak` | 7 | Commercial ASR tie-breaker sample | 5% sample, only from vendors whose terms allow it | Bayanat Labs practice |
| `T8.shards` | 8 | Shard size | <= 500 MB Parquet; WebDataset tar <= 8 GB | Bayanat Labs practice |
| `T8.github` | 8 | GitHub files | < 100 MiB; data never in git | Bayanat Labs practice |
| `T8.manifests` | 8 | Files per folder | fewer than 10k | Bayanat Labs practice |
| `T9.number` | 9 | Printable number | at least one script-computed headline metric | Bayanat Labs practice |
| `T10.day` | 10 | Release day | Tuesday or Wednesday | Bayanat Labs release practice |
| `T10.claims` | 10 | Claims re-verification | on release day | gate G7 |
| `T11.followup` | 11 | Post-launch fixes | within 7 days | Bayanat Labs practice |
| `T11.review` | 11 | Usage review | day 30 (30-day rule) | Bayanat Labs release practice |
| `T12.manifest_refresh` | 12 | Manifest pruning and API data refresh | every 30 days | Bayanat Labs practice; the terms of the APIs used |
| `T12.takedown` | 12 | Takedown | ack 2 business days; removal <= 30 days; platform <= 24 h; PII/child-safety/CSAM <= 24 h | Bayanat Labs practice |
| `T12.leak` | 12 | Leaked test set | rotated within 30 days | Bayanat Labs practice |
| `T12.refresh` | 12 | Scheduled refresh | quarterly | Bayanat Labs practice |
| `T12.index_only` | 12 | Index-only triggers | IO-1 to IO-5 reviewed at each version and on the monthly licence spot-check | policy/index-only-rules.yaml |

## 5. Stage 0: the scoping memo and the selection rubric

Nothing is fetched until the coordinator approves a scoping memo and `job.json` exists with external actions off.

1. Copy `manual/SCOPING_MEMO.md` into the job directory as `scoping_memo.md` and fill the memo record `scoping_memo.yaml` (schema: `manual/schemas/scoping_memo_record.schema.json`).
2. Re-check the claim's incumbent and every source licence on the day.
3. Write the rubric block `scoping_memo.score.yaml` in the exact `bl-score` format (schema: `manual/scoping_memo.schema.json`, a mirror of bl-score's own; unknown fields are errors) and save bl-score's output as `scoping_memo.score.json`. Weights: Impact 30, Claim strength 20, Ease 20, Legal cleanliness 20 (a gate), Commercial pull 10, each scored 1-5 against the 1/3/5 anchors. The legal gate applies the more restrictive of two readings: the legal tier and the legal-cleanliness score. A red tier, or a score of 1, is excluded whatever the total. A yellow tier, or a score of 2 or 3, caps the release at Tier 2 even when the tier says green (`legal_gate.score_overrides` in `policy/rubric.yaml`). bl-score suggests a priority; the coordinator decides it. bl-score is pinned by the hash of its code (`manual/bl-score.pin.json`, checked by `S0.score_tool_pinned`), not by its version string, because its scoring changed while the version stayed 0.1.0; record the hash in the memo record as `score_tool_sha256`.
4. Fix QA sample sizes and the agreement threshold in the memo, up front. Human QA is the expensive step, so it is never sized after the fact.
5. For Tier 2, name the collection basis (academic partner under EU DSM Art. 3/4, written permission, or a recorded decision that permits it). Bayanat Labs relies on no Saudi text-and-data-mining exception; an exception reported in 2026 is unverified and is not relied on. Scale stays capped until a named basis exists.
6. Record for each source its licence route (`licence_route`, an input-licence ID in `policy/licence-matrix.yaml`) and the release tier its content may reach (`release_tier`), and cite any legal position by the ID of the recorded decision it rests on (`decision_ref`). Free text is not accepted there.
7. Write `job.json` (schema: `manual/schemas/reports/job.schema.json`) with `external_actions_authorized` false.
8. The coordinator approves, asks for revision or rejects, with name and date in the memo record.

Codes: **P0** ships within 60 days, **P1** by LEAP (12 Apr 2027), **P2** within year one, **P3** opportunistic. **S** under one agent-week, **M** 1-4 agent-weeks, **L** 1-3 agent-months, **XL** longer or needs a partner.

## 6. The coordinator

One coordinator agent runs the programme layer so that each dataset agent can own one release end to end.

| Duty | File | Gate |
|---|---|---|
| Approve scoping memos and assign the legal tier | `scoping_memo.yaml` decision block | Stage 0 |
| Keep the source, provenance and claims ledgers answerable in one query | `coordinator/ledger_procedure.md` | Stages 1, 8, 10 |
| Keep the release calendar | `coordinator/release_calendar.jsonl` | Stage 12 |
| Run the launch bundle | `coordinator/launch_bundle_checklist.md` | Stage 10 |
| Add the monthly metrics row | `coordinator/metrics_digest_row.schema.json` | Stage 11 |
| Keep the maintenance calendar | `coordinator/maintenance_calendar.md` | Stage 12 |
| Review the policy's index-only triggers IO-1 to IO-5 at each version | `qa/reports/maintenance.json` | Stage 12 |
| Post-mortem after any release that failed or skipped a gate | release index | Change control |

Daily loop: resume incomplete jobs; check urgent removals, failed downloads, terms changes and source drift; pick the highest-priority unblocked job within the limit of three new source cohorts; run one bounded batch; run validators; build a release candidate only when all gates pass; write the receipt, with the minutes spent per stage (`stage_minutes`, so budgets can be calibrated on real work).

## 7. Tooling

The pinned 2026 stack, by stage. Versions, sources, licences, licence evidence, hashes and the `commercial_safe` and `blocked_for_release_path` flags live in `manual/tooling.lock.yaml`; this section names the tools only.

| Stage | Tools |
|---|---|
| 2 Acquisition | The Bayanat Labs fetcher; `huggingface_hub`; yt-dlp for Creative Commons video, only where check `S2.media_download_decision` passes (never CAPTCHA, WAF or bot-detection bypass, proxy rotation or personal cookies) |
| 3 Normalisation and transcription | Bayanat Labs `arabic-normalize` and CAMeL Tools; GlotLID; FFmpeg; Silero VAD; UVR-MDX-Net or Demucs on music-flagged segments only, for internal ASR; Whisper large-v3 through faster-whisper plus an Arabic second ASR system (NVIDIA FastConformer Arabic, the "pc" variant, or Nemotron 3.5 ASR fine-tuned on our own pseudo-labels); ctc-forced-aligner with a commercially usable Arabic wav2vec2 model |
| 4 Deduplication | datasketch MinHash, datatrove, Chromaprint |
| 5 Safety and PII | Presidio with the Bayanat Labs Arabic recogniser pack; Arabic NER, toxicity and NSFW classifiers (not yet pinned) |
| 6 Enrichment | pyannote `speaker-diarization-community-1` (gated: only after the founder accepts its conditions); DNSMOS P.835; the TorchAudio-SQUIM objective model only (the subjective model is non-commercial); Qwen3 or ALLaM through vLLM for punctuation and label suggestions under a 5% CER change guard. **Internal pre-labels only, never in a release:** the ADI-20 dialect model and sentence-level ALDi (no licence grant), and the CAMeL dialect-ID models (until they are cleared for release use); their output is reviewed by speakers of each dialect and released only as human labels |
| 8-10 Packaging and release | mlcroissant, `huggingface_hub`, `datasets`; the dataset template's `bl-card-lint`, `bl-manifest`, `bl-gates`, `bl-card-render` |
| 9 Baseline | lighteval and lm-eval-harness task files for benchmarks |

Rules for tools and models:

- No tool or model whose licence is non-commercial or unknown may produce released artefacts; such entries are flagged `blocked_for_release_path` in the lock file, and the stage-8 gate checks that none was used.
- Tools are used, not vendored: Chromaprint (LGPL) and any GPL plugin never go into a Creative Commons data repository.
- Gated models need their conditions accepted on the Bayanat Labs account by the founder. Agents never accept terms. pyannote `speaker-diarization-community-1` is gated, so accepting its conditions is a founder action.
- A commercial ASR tie-breaker runs on a 5% sample only, and only from vendors whose terms allow benchmarking. Benchmark terms are re-checked when the lock file is updated.
- Licences are re-verified at every tooling bump and for every new release version.

**Release-path status (lock v0.1.0-draft, 14 Oct 2026; the lock file is the authority and may have changed).** The lock flags several tools named in this manual as not usable for released artefacts yet: ArTST v3 and the MMS alignment models (ctc-forced-aligner's default) carry non-commercial licences; the ADI-20 dialect model and the sentence-level ALDi model have no licence grant; the CAMeL dialect-ID models are not yet cleared for release use; pyannote needs its gate accepted; music-separation tools are internal only. Until a model is cleared, its output may serve only as internal pre-labels that humans review, and the stage-8 gate fails if a flagged tool produced a released artefact. `scripts/validate_stages.py --tooling manual/tooling.lock.yaml` lists every stage tool that is flagged. A blocked entry stays off the release path until its condition is met and recorded.

## 8. Crawler etiquette

The full text is `manual/etiquette.md`; the Bayanat Labs crawler page (https://www.bayanatlabs.com/open/crawler) says the same. In short: a descriptive User-Agent with a contact address; at most one request every 3 seconds per host (5 seconds for government and small sites), one connection at a time; robots.txt, TDMRep and Content-Signal obeyed, and blocks on other AI crawlers read as a statement of intent; stop on 429 and back off; stop on any access denial (401 or 403); no CAPTCHA solving and no login, paywall or WAF bypass; no proxy, IP or account rotation; data stored from an API refreshed or deleted as that API's terms require; opt-out and takedown requests honoured; everything logged so the provenance ledger answers "where did this record come from?" in one query.

## 9. Stop rules

The full list is `manual/stop_rules.md`; stage-specific stops are in `manual/stages.yaml`. The four programme rules: a release that cannot pass the legal gate is converted to Tier 2 or dropped, never delayed indefinitely; a benchmark whose test set leaks is rotated within 30 days; withdrawn partner audio is removed within the SLA and the counter corrected publicly; verbatim text or transcripts of content Bayanat Labs cannot license stay internal (aggregate statistics, scoring and internal tooling only).

## 10. Definition of done

A release is done when all 12 items in `manual/dod.yaml` are true, in two phases. **Release candidate** (`rc`) is everything agents can prepare before the founder's go; it covers every release artefact the programme requires. **Done** adds what exists only after the founder has released, listed and sent. Every gate G0-G7 must pass first.

| Id | Item | Release-candidate checks (before the founder's go) | Done checks (after launch) | Release artefacts covered |
|---|---|---|---|---|
| D01 | Scoping memo | `D01.memo`, `D01.approved` | same as release candidate | the scoping memo (approved); job.json |
| D02 | Provenance ledger | `D02.sources`, `D02.items` | same as release candidate | sources.jsonl; PROVENANCE.parquet |
| D03 | QA report | `D03.report`, `D03.signoff` | same as release candidate | the QA report |
| D04 | Claims ledger | `D04.file`, `D04.numbers`, `D04.reverified` | `D04.claims_approval` | CLAIMS.md |
| D05 | Card and release files | `D05.files`, `D05.lint`, `D05.croissant`, `D05.example` | same as release candidate | bilingual card (EN + AR); LICENSE + LICENSES/; CITATION.cff; CHANGELOG.md; MANIFEST.json; SHA256SUMS; croissant.json (validated); a runnable example that reproduces its expected output in a clean environment |
| D06 | DOI | `D06.reserved` | `D06.published` | a reserved Zenodo DOI |
| D07 | Hub page | `D07.draft`, `D07.jsonld`, `D07.family` | `D07.live` | the hub page draft with JSON-LD and the paid-family link |
| D08 | Baseline chart | `D08.chart`, `D08.number` | same as release candidate | a baseline or benchmark chart (a number a journalist can print) |
| D09 | Listings (Masader, Kaggle, Google Dataset Search) | `D09.drafts` | `D09.masader`, `D09.kaggle`, `D09.gds` | drafts of the listings (Masader, Kaggle) |
| D10 | Launch bundle sent | `D10.drafts` | `D10.sent` | the launch-bundle drafts in outbox/ (technical post, AR/EN press paragraph, thread with one chart and one precise number, partner list) |
| D11 | Metrics row created | `D11.template` | `D11.row` | a metrics row template |
| D12 | Next-version date set | `D12.date`, `D12.takedown` | `D12.calendar` | a next-version date; the takedown route live |

## 11. Change control

- Thresholds and stage definitions change only by pull request with founder approval.
- Semantic versions: patch for wording; minor for tooling bumps and new optional checks; major for any gate or threshold change. Each version gets a `CHANGELOG.md` entry and, once public, a Zenodo DOI.
- Every dataset card records the `manual_version` it was built under, in its Creation section. The dataset template's `bl-gates` pins `stages.yaml` by version.
- Quarterly review, plus a post-mortem after any release that failed or skipped a gate.
- Version path: v1.0.1, the first public version (15 Oct 2026; this version) → quarterly revisions, the first in January 2027.

## 12. Choices the manual makes

`manual/gate-crosswalk.md` section 4 lists twenty-one choices (C-01 to C-21), each with the alternative that was considered. The ones that change day-to-day work most:

- Request rate: at least 3 seconds per host for every host, APIs and dumps included (C-01).
- Normalisation: the Bayanat Labs recipe, taa marbuta kept in `text_norm` (C-03).
- PII: zero hits in at least 3,000 stratified records, with the rate on the first 1,000 also reported (C-04).
- Human QA sample: the T7 minimums (C-06).
- Release: the coordinator's checklist **and** the founder's go (C-13).
- Definition of done in two phases (C-19).

## 13. Files

This manual is published in `Bayanat-Labs/open-policies` under `manual/` and `coordinator/`, with the manual text under CC BY 4.0 and schemas and scripts under Apache-2.0.
