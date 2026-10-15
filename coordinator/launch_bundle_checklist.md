# Launch-bundle checklist (stage 10)

*Operating manual v1.0.1 · Approved by the founder on 15 Oct 2026 · Text CC BY 4.0 · Documentation, not legal advice.*

The coordinator runs this list for every release; the stage-10 gate reads the result. The unit of value is the same every time: dataset, card, baseline, technical post, announcement and listings. Agents prepare every item. The founder sends, posts, publishes and approves (founder-only actions). Agents never send email or post anything themselves.

**Rhythm.** A release every two weeks, alternating datasets and tools; one flagship per quarter with an arXiv paper; one annual report. Release on a **Tuesday or Wednesday** with a Parquet viewer, a demo Space and a one-line loader.

**How the gate reads it.** Record the run in `qa/reports/release_checklist.json`: one key per item id below (`true`, `false` or `"n/a: <reason>"`), plus `unchecked_items` (count of items neither `true` nor `n/a`), `claims_reverified_on` (date), `page_card_archive_mismatches` (count), `doi_reserved` (DOI string), `hub_page_draft_path`, `hub_page_jsonld_valid`, `hub_page_paid_family_link`, `takedown_route_live`, and a `coordinator` sign-off `{name, date, verdict: approve}`. The stage-10 gate needs `unchecked_items == 0`, the sign-off and the founder's go in `signoffs/founder_go.yaml`.

## A. T-7 to T-1: prepare (agents; coordinator checks)

| Id | Item | Owner | Evidence |
|---|---|---|---|
| LB-01 | Legal gate passed: tier assigned; G6 licence compatibility; a recorded decision cited, by decision ID, for every item whose release needs one | agent → coordinator | `qa/reports/licence_check.json` |
| LB-02 | Privacy gate G3 passed: zero PII hits in the 3,000-record stratified audit (the <0.1% rate on the first 1,000 is reported alongside) | agent → coordinator | `qa/reports/pii_audit.json` |
| LB-03 | Claims gate G7: every number script-computed; every superlative re-verified **that day** in `CLAIMS.md` with the incumbent cited; claims-register row drafted | coordinator | `CLAIMS.md`, `qa/reports/numbers.json` |
| LB-04 | Card complete: FineWeb's 11 sections plus Bayanat Labs' 5 (provenance ledger, claims ledger, takedown route, EU AI Act helper, "Not for voice cloning" on speech); README + README.ar; intended and out-of-scope uses; separate rights (training / display / redistribution / synthetic voice); paid-family block; `manual_version` in the Creation section | agent | `qa/reports/package.json` (`card_lint_errors == 0`) |
| LB-05 | Files: `croissant.json`, `SHA256SUMS`, `MANIFEST.json`, `PROVENANCE`, `LICENSE` + `LICENSES/`, `CITATION.cff`, `CHANGELOG.md`; viewer renders and `datasets.load_dataset` works in a clean environment | agent | `qa/reports/package.json` |
| LB-06 | Baseline or benchmark chart drawn by a script from the dataset's own statistics | agent | `eval/results.json`, `launch/chart.png` |
| LB-07 | Zenodo DOI **reserved** and written into the card, `CITATION.cff` and the hub page draft (publishing it is part of the founder's go) | agent; founder holds the account | `doi_reserved` |
| LB-08 | `launch/` folder in the builder repo: `chart.png` and the script that draws it; `thread.md` (EN + AR, 6-10 posts, chart first); `press.md` (one AR and one EN paragraph); `hf_post.md`; `partners.yaml`; `masader_entry.json` | agent | builder repo `launch/` |
| LB-09 | Launch-bundle drafts copied to `outbox/launch/` with status `draft_for_founder`: technical post, AR/EN press paragraph, thread with one chart and one precise number, partner list | agent | `outbox/launch/` |
| LB-10 | Hub page draft `/open/<slug>` (EN + AR) with JSON-LD that matches the visible page, visible "updated" date, named human author, cite-as block and the paid-family link | agent | `hub_page_draft_path`, `hub_page_jsonld_valid`, `hub_page_paid_family_link` |
| LB-11 | Benchmarks only: vendor preview rows ready with a 7-day right of reply; academic co-reviewer sign-off on the method; each vendor's benchmarking terms checked | agent; founder sends previews | preview log |
| LB-12 | Press note drafted; for flagships, ready to go under embargo to the press list | agent; founder sends | `outbox/launch/press.md` |
| LB-13 | Takedown route live: `hello@bayanatlabs.com` and the takedown page, linked from the card | coordinator | `takedown_route_live` |
| LB-14 | All gates G0-G7 pass in `qa/reports/gates.json`; the founder has the release candidate and its evidence | coordinator | `qa/reports/gates.json` |

## B. Launch day, in this order (founder acts; agents prepare)

| Id | Step | Who acts |
|---|---|---|
| LD-01 | Hub page `/open/<slug>` live (EN + AR) with JSON-LD; then the HF repo goes public (ungated) with its card; then the Zenodo DOI is published; IndexNow ping | Founder |
| LD-02 | Technical post on the HF org blog and the site, Arabic and English the same day: how it was built, what it beats, baseline chart, limitations | Founder |
| LD-03 | Flagships: arXiv preprint live with the HF repo, academic co-author, HF paper page claimed | Founder |
| LD-04 | HF community post from the org | Founder |
| LD-05 | Founder thread, Arabic and English, one chart and one precise number; tag the researchers whose data or models are compared | Founder |
| LD-06 | Press note: numbers first, one quote, link to the hub page (not only to HF) | Founder |
| LD-07 | Community posts in the launch channels | Founder |
| LD-08 | Listings submitted: Masader, Kaggle mirror (only after its terms are read), Awesome Arabic NLP, Wikidata item for named assets | Founder |
| LD-09 | Short outreach emails to the standing list plus the asset-specific list in `partners.yaml` | Founder |
| LD-10 | Hub index card added; newsletter queue and calendar page updated | Coordinator prepares; founder publishes |

After each founder action, the coordinator records it in `release/published.yaml` (DOI published, hub page URL, listing statuses, `launch_bundle_sent` with name, date and `verdict: sent`). The definition of done (`manual/dod.yaml`, phase `done`) reads that file.

## C. T+1 to T+7: follow-up

| Id | Item | Owner |
|---|---|---|
| FU-01 | Fix card issues raised in HF discussions and GitHub issues within 7 days; reply publicly (founder posts) | agent; founder |
| FU-02 | Add "models trained on it" and "used by" links as they appear | agent |
| FU-03 | Log every mention and backlink in the coverage register; never claim a listing, acceptance or backlink before it exists | coordinator |
| FU-04 | Schedule the first refresh and set the next-version date (stage 12) | coordinator |
| FU-05 | Add the metrics row to the digest (stage 11; `coordinator/metrics_digest_row.schema.json`) | coordinator |

## D. T+30: review

| Id | Item | Owner |
|---|---|---|
| R-01 | Apply the 30-day rule: separate a discovery problem from a utility problem; record `verdict_30d` in the metrics row | coordinator |

**Do not** publish near-identical AI-written launch posts for every release, or mass-submit to directories. One technically useful story per meaningful release.

**Date-anchored launches** (proposals): 18 Dec 2026 falls on a Friday, so the flagship keeps the date but the press note goes under embargo on Tue 15 or Wed 16 Dec; the "by 31 Oct" green releases ship Tue 27 / Wed 28 Oct, during ArabicNLP 2026. The dates are kept in the release calendar.
