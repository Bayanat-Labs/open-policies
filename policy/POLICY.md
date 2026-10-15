# Bayanat Labs open-programme policy

> **Version 1.0.1 · Reviewed by counsel, October 2026.**

> **Documentation, not legal advice.** This policy states how Bayanat Labs chooses, licenses and publishes open Arabic data. It summarises statutes and platform terms only to explain our own rules. It is not a legal opinion, and it is not advice to anyone else.

| Field | Value |
|---|---|
| Version | 1.0.1, 15 Oct 2026 |
| Status | Adopted |
| Reviewed by counsel | October 2026 |
| Next review | At each programme version, whenever a source's terms change, and at least quarterly (next by 15 Jan 2027) |
| Owner | Bayanat Labs |
| Languages | English (`POLICY.md`) and Arabic (`POLICY.ar.md`). The English text governs if the two differ |
| Licence of this text | CC BY 4.0 (attribution: "Policy by Bayanat Labs") |
| Machine-readable files | `rubric.yaml`, `tiers.yaml`, `licence-matrix.yaml`, `principles.yaml`, `index-only-rules.yaml`, with JSON Schemas in `schemas/` |
| Scoring tool | `tools/bl-score` (Apache-2.0) |
| Contact | hello@bayanatlabs.com |

## 1. Purpose

This policy is the gate every Bayanat Labs open release passes. It sets:

- how candidates are scored and which ones are built (selection rubric, section 8);
- what may be published, and under which licence (release tiers and licence matrix, sections 3 and 4);
- when a release falls back to index-only, and when work stops (section 5);
- that no release is gated (section 6), and how claims are counted (section 7).

Every scoping memo applies it. The dataset-card template carries its tiers and licence matrix into every repository.

Our commercial moat is rights clarity. The policy exists so that a researcher, a buyer's legal team or a journalist can see, before downloading anything, what each release contains and on what terms.

## 2. Operating principles

Machine-readable in `principles.yaml`.

1. Publish only what we can license. Our commercial moat is rights clarity, so the open programme uses three release tiers (open content; manifests plus our own annotations; partner-licensed) and never publishes verbatim text or audio we cannot license; the one written exception is ODC-By packaging of web text on the FineWeb and HPLT precedent, with per-document source URLs and a takedown route.
2. Never gate, use permissive licences, and ship the full launch bundle every time: technical blog, 11-section dataset card, paper page, founder thread, press note.
3. Every dataset ships with a benchmark or a baseline run; compute is our cheapest credibility.
4. Claims go through the claims ledger before copy: every "largest" names the unit, licence class, date and the incumbent it beats.
5. We build no models; every leaderboard carries that statement; national models appear only through their own leaderboards or by opt-in.

A second written exception covers corrections to non-commercial public datasets, released under the source's own licence (section 3). No release is gated (section 6).

## 3. Three release tiers

Full text in `tiers.yaml`. Each tier is defined by the licence class of the content it carries.

| Tier | What we publish | Licence | Content it covers | Collection basis |
|---|---|---|---|---|
| **Tier 1: open content** | Full text or audio plus our annotations | CC0 for manifests and metadata; CC BY 4.0 for our annotations; CC BY-SA 4.0 where Wikipedia-derived; ODC-By for web-text packaging; per-record `source_license` | Content under an open licence (CC0, CC BY, CC BY-SA, ODC-By, ODbL) or in the public domain, and content from consented contributors | The source's open licence, public-domain status or consent |
| **Tier 2: manifests plus our annotations** | IDs, URLs, timestamps, dialect/city labels, speaker turns, quality scores, topics, entity tags, alignment anchors, and a one-command rebuild script. No verbatim content | CC BY 4.0 on annotations, CC0 on IDs | Content that is not redistributed (standard-licence, all-rights-reserved or unclear-licence content), referenced by identifier | Named in each scoping memo: an academic partner collecting under EU DSM Art. 3/4, written rights-holder permission, or lawyer sign-off. Scale stays capped until one exists |
| **Tier 3: partner-licensed** | Content released under a written permission (CC BY or a custom open licence) | As agreed | Content licensed from a partner under a written agreement (no partner is named before an agreement exists) | Written permission on file before collection |

- **Why Tier 2 names a basis.** Bayanat Labs relies on no Saudi text-and-data-mining exception. Secondary sources report an exception for AI development in an updated Saudi Copyright Law; it is unverified and it is not relied on. Each Tier 2 scoping memo therefore names its collection basis.
- **Public-domain test.** A work counts as public domain only when this is verified for that work: the author died in or before 1955, the work is in the public domain in the United States as well, and the text is transcribed from a verified public-domain print. Laws, gazettes, judgments and official documents are outside copyright under the Saudi Copyright Law; judgments are anonymised, and notices about private persons are kept to metadata.
- **Tier 3 partners.** No partner is named in this policy until a written agreement exists. Each permission letter is reviewed individually before it is sent.
- **Internal only.** Verbatim transcripts or text of content we cannot license stay internal. They may feed aggregate statistics, benchmark scoring and internal tooling, but they are never published, even gated or "research only".
- **Two written exceptions.** (1) ODC-By packaging of web text, on the FineWeb and HPLT precedent, with per-document source URLs and a takedown route; never CC0. (2) Corrections to non-commercial public sets, released under the source's own licence and labelled as derivatives, never under a Bayanat Labs NC licence.
- **Consented contributors.** Recording and recruitment start only when the company's entity details, its registration as a data controller and in-Kingdom storage are in place; contributors and recorded data subjects are Saudi residents only.
- **Unit of value.** A release is: dataset + card from the Bayanat Labs dataset-card template (FineWeb's 11 sections plus Bayanat Labs' five) + benchmark or baseline model trained on it + technical post + announcement + Masader, Kaggle and Google Dataset Search listings.
- **Where the tier shows.** Each card's "What is being released (per subset, with licence tier)" and "Licensing" sections, and the per-record `source_license` field.

## 4. Licence matrix

Full text in `licence-matrix.yaml`. Two tables, kept apart on purpose: what we **release under** and what we may **ingest**. An ingestible licence (for example ODbL or the Saudi Open Data License) is not a release tag.

### 4.1 Output: what Bayanat Labs releases under

| ID | Content | Hugging Face tag | Required per-record fields | Why |
|---|---|---|---|---|
| OUT-01 | Manifests, IDs, timestamps, metadata | `cc0-1.0` | `source_url`, `source_license` | Pure facts; AudioSet releases the same fields under CC BY 4.0, and we waive even attribution |
| OUT-02 | Our annotations, transcripts of CC content, segmentations, labels | `cc-by-4.0` | `source_url`, `source_license`, `annotation_origin` | Companies adopt it; CC FAQ confirms TDM-friendly |
| OUT-03 | Structured reference data (gazetteer, lexicons, validators' test suites) | `cc-by-4.0` or `cdla-permissive-2.0` | `source_url`, `source_license` | CDLA explicitly frees model outputs |
| OUT-04 | Wikipedia-derived text | `cc-by-sa-4.0`, separate config | `page_url`, `revision_id`, `source_license` | Wikimedia terms of use §7 |
| OUT-05 | Web-text packaging (crawl-derived text) | `odc-by` | `source_url`, `source_license` | FineWeb norm; does not pretend to license contents. Written exception only |
| OUT-06 | GPL-licensed inputs | `gpl-3.0`, separate repo | `source_url`, `source_license` | Never mixed into CC repos |
| OUT-07 | Verbatim-only inputs (terms that forbid modification) | `other`, source terms in `LICENSE` | `source_url`, `source_license` | Their terms forbid modification |
| OUT-08 | ODbL-derived data | `odbl`, separate config | `source_url`, `source_license` | Inherited share-alike database licence |
| OUT-09 | CC BY media whose licence version is shown per item | `cc-by-3.0` or `cc-by-4.0`, per item: the CC BY version the item's page shows at collection; separate config | `source_url`, `source_license`, `licence_shown_at_collection`, `channel_attribution`, `licence_reverified_at` | Some hosts label media only "CC BY" and link a single legal code, so each item keeps the version label and legal-code link its page shows at collection, never an assumed version |
| OUT-10 | Bayanat Labs-authored data and docs | `cc-by-4.0` | `source_license`, `synthetic` | Our own work |
| OUT-11 | Corrections to non-commercial sets | the source's licence | `source_url`, `source_license`, `derivative_of` | Labelled as derivatives |
| OUT-12 | Partner-licensed content (Tier 3) | as agreed | `source_url`, `source_license`, `permission_doc_id` | Written permission |

Synthetic data in releases (OUT-10) comes only from generators under Apache-2.0 or MIT, logged per record.

Code is `apache-2.0`. Rules on our own work: never `cc-by-nc`, never ND, never Apache or MIT for data, never a custom licence, never CC0 on web-crawl derivatives, never relicense upstream content. Where sources mix, the card states: "Underlying content is not licensed by Bayanat Labs; see per-record fields".

### 4.2 Input: what Bayanat Labs may ingest

| Allowlist | Conditions |
|---|---|
| CC0 | none |
| CC BY | keep each source's version; for media labelled per item, the version each item's page shows at collection |
| CC BY-SA | share-alike inherited; separate config |
| ODC-BY | none |
| ODbL | separate config |
| PD (public domain) | verified per work; not a licence |
| the Saudi Open Data License | attribution, the licence copy and notices kept intact; sources under it stay index-only (IO-5) until its text has been read and filed; kept separate from CC BY data |
| written permission | signed, on file before collection |

**Blocklist:** NC (unless intentional), ND, unknown, all rights reserved. Mixed licences are split into per-licence subsets, and SA data stays separate from CC BY data. Non-commercial and research-only sets are run only by an academic partner under its own agreement; Bayanat Labs keeps no copies and publishes no scores on them. Sources with an all-rights-reserved notice ship as manifests or links only until written permission exists.

Every tag and allowlist entry was checked on 2026-10-14 against the SPDX licence list (version 3.29.0) and the Hugging Face licence identifier list. Public domain, the Saudi Open Data License and written permission have no SPDX identifier; they are marked as such rather than forced into one.

## 5. Index-only and stop rules

**Index-only** (`index-only-rules.yaml`). A release moves from publish to index-only (Tier 2: IDs, URLs, metadata and our annotations, no content) when:

| ID | Trigger |
|---|---|
| IO-1 | anything whose source terms changed since collection |
| IO-2 | any item hit by a takedown |
| IO-3 | any video whose licence is no longer Creative Commons at re-verification |
| IO-4 | any record with residual PII found in audit |
| IO-5 | any source whose portal licence could not be read |

**Stop rules** (`stop-rules.md`): a release that cannot pass the legal gate is converted to Tier 2 or dropped, never delayed indefinitely; a benchmark whose test set leaks is rotated within 30 days; any partner audio whose permission is withdrawn is removed within the SLA and the counter corrected publicly.

## 6. Gating exception

Every release is ungated, with no exception (`gating-exception.md`). Safety sets with residual sensitivity are not gated either: they are kept as hidden test sets and evaluated by submission. Gating never makes unlicensable content publishable.

## 7. Claims rules

From the claims ledger rules (`claims-rules.md`): count only what is released; name the licence class; date every claim; never pool tiers; never compare an open set with a non-commercial or request-only set without saying so; "first" claims require a saved search of Hugging Face, Masader, Kaggle, Zenodo, the ACL Anthology and arXiv; commercial inventory figures stay out of open-data claims. This policy makes no "first" claim about itself.

## 8. Selection rubric

"Every candidate is scored on five criteria, and anything that fails the legal gate is dropped regardless of score." (`rubric.yaml`)

| Criterion | Weight | Score 1 | Score 3 | Score 5 |
|---|---|---|---|---|
| Impact (citations, press, developer use) | 30% | Nobody searches for it; no downstream use | Useful to Arabic NLP researchers | Used by model labs, cited by press and AI assistants, pulled by leaderboards |
| Claim strength | 20% | Many equivalents exist | Better than incumbents on one axis | No credible incumbent for a precise "first/largest" claim |
| Ease | 20% | Needs humans at scale or partner consent | Agent-buildable with some human QA | Agent-buildable from dumps/APIs in days |
| Legal cleanliness (gate) | 20% | Red legal tier: not built | Yellow: manifests and our own annotations only | Green: full content redistributable under an open licence |
| Commercial pull | 10% | No product link | Feeds one service page | Feeds a product family and a sales conversation (Voice, Search, Bench, Documents, Agents) |

- **Weighted score.** `weighted_score_0_100 = Σ weight × (score − 1) / 4`, weights in percent. All 1s give 0; all 5s give 100.
- **Legal gate.** The more restrictive of the memo's legal tier and its legal-cleanliness score applies. Red gives `excluded` (not built, no priority); yellow gives `tier2_only` (manifests and own annotations only; yellow never means "publish with caveats"); green gives `tier1_eligible`. A legal-cleanliness score of 1 (the red anchor) gives `excluded` and a score of 2 or 3 caps the release at `tier2_only`, whatever the legal tier says.
- **Priority codes.** P0 ships within 60 days; P1 by LEAP on 12 Apr 2027; P2 within year one; P3 opportunistic.
- **Effort codes.** S under one agent-week; M one to four agent-weeks; L one to three agent-months; XL longer or needing a partner.
- **Suggested priority (adopted for v1.0, provisional; the coordinator decides each case).** Score ≥ 75 with effort S or M gives P0; ≥ 60 gives P1; ≥ 45 gives P2; otherwise P3.
- **Calibration.** The weights and thresholds were tested on a sample of programme candidates, including a ±10-point weight sensitivity check. A comparison with a blind ranking made without the rubric scores is still outstanding, so the thresholds are provisional. Weights are never retuned silently: any change gets a new version and a changelog entry.

## 9. Crosswalk to other scoring scales

Bayanat Labs maps this rubric onto the other scoring scales it uses in planning, so every candidate is ranked on one basis. Search demand is never weighted; it only breaks ties between equal scores.

## 10. Legal notes

Five legal points shape the rules above:

- (a) laws, gazettes, judgments and official documents are outside copyright under the Saudi Copyright Law; decrees, laws and decisions may be published as text from the official gazette after the personal-data audit, notices about private persons are kept to metadata, and judgments are anonymised;
- (b) no record with personal data of KSA or UAE residents goes to a foreign-hosted platform before the PII audit passes; consent for identifiable people must cover transfer abroad; identity, consent and payment records stay in Saudi Arabia;
- (c) the PDPL Art. 27 research exception is never relied on;
- (d) Bayanat Labs relies on no Saudi text-and-data-mining exception; an exception for AI development reported in 2026 is unverified and is not relied on;
- (e) where a source labels media only "CC BY", each item keeps the CC BY version its page shows at collection, recorded in `licence_shown_at_collection`, and our transcripts and labels are CC BY 4.0.

Each source's own terms are read and filed at scoping, before anything is collected.

## 11. Versioning

| Version | Meaning |
|---|---|
| v1.0.1 (this version, 15 Oct 2026) | First public version. Adopted. Reviewed by counsel, October 2026. English and Arabic editions. The Arabic text has not yet been reviewed by a native Arabic writer; the English governs |
| v1.x | Re-read at each programme version, whenever a source's terms change, and at least quarterly |

Every change goes in `CHANGELOG.md`. Each dataset card's Licensing section links the policy version it was released under.
## 12. Contact

Questions, corrections and takedown requests: **hello@bayanatlabs.com** (30-day removal SLA; 24 hours for platform requests).

Others may adopt the licence matrix under CC BY 4.0 with the attribution "Policy by Bayanat Labs".
