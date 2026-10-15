# Bayanat Labs open policies

The rules Bayanat Labs follows when it chooses, licenses and publishes open Arabic data, and the gated process every Bayanat Labs open dataset goes through. In English and Arabic.

> **Documentation, not legal advice.** These files state Bayanat Labs' own rules. They summarise statutes and platform terms only to explain those rules. They are not a legal opinion and not advice to anyone else.

| | Version | Status |
|---|---|---|
| Open-programme policy (`policy/`) | 1.0.1 | Adopted. Reviewed by counsel, October 2026 |
| Operating manual (`manual/`) | 1.0.1 | Approved by the founder on 15 Oct 2026 |
| `bl-score` scoring tool (`tools/bl-score/`) | 0.1.0 | Apache-2.0 |

Read them on the web: [Open-data policy](https://www.bayanatlabs.com/open/policy) and [How we build open datasets](https://www.bayanatlabs.com/open/how-we-build).

## What Bayanat Labs publishes

Bayanat Labs publishes open Arabic data only where it can license it. Every release says what it contains and on what terms before anyone downloads it. Each release sits in one of 3 tiers (`policy/tiers.yaml`):

- **Tier 1: open content.** Full text or audio plus our annotations. It covers content under an open licence (CC0, CC BY, CC BY-SA, ODC-By, ODbL) or in the public domain, and content from consented contributors.
- **Tier 2: manifests plus our annotations.** IDs, URLs, timestamps, dialect/city labels, speaker turns, quality scores, topics, entity tags, alignment anchors, and a one-command rebuild script. No verbatim content. It covers content that is not redistributed (standard-licence, all-rights-reserved or unclear-licence content), referenced by identifier.
- **Tier 3: partner-licensed.** Content released under a written permission (CC BY or a custom open licence). It covers content licensed from a partner under a written agreement (no partner is named before an agreement exists).

No release is gated, and every record carries its own `source_license`; the licence matrix is in `policy/licence-matrix.yaml`. Every candidate is scored against a 5-criterion rubric (`policy/rubric.yaml`). Legal cleanliness is also a gate: a candidate with a red legal tier is not built, whatever its total.

## How we build

The operating manual (`manual/PUBLIC.md`, Arabic `manual/PUBLIC.ar.md`) sets out 13 stages, from a stage-0 scoping memo to maintenance. Each stage ends in a blocking gate. `manual/stages.yaml` holds 114 machine-checkable gate checks, `manual/dod.yaml` the 12-item definition of done, and `manual/tooling.lock.yaml` 57 pinned tools and models with their licences.

## What is in this repository

| Folder | What it holds | Licence |
|---|---|---|
| `policy/` | The open-programme policy: `POLICY.md` and `POLICY.ar.md`, the selection rubric, release tiers, licence matrix, principles, index-only, stop, gating and claims rules, JSON Schemas, a validator and its tests | Text, YAML and schemas CC BY 4.0; `scripts/` and `tests/` Apache-2.0 |
| `tools/bl-score/` | `bl-score`, the command-line tool that applies the rubric to a scoping memo | Apache-2.0 (its copy of `rubric.yaml` stays CC BY 4.0) |
| `manual/` | The operating manual in English and Arabic, `stages.yaml`, gate crosswalk, scoping-memo template and schemas, definition of done, crawler etiquette, stop rules, tooling lock, stage diagram, budget estimator and its tests | Text and YAML CC BY 4.0; JSON Schemas, `budget.py` and `tests/` Apache-2.0 |
| `coordinator/` | Ledger procedure, launch-bundle checklist, maintenance calendar, metrics-row schema | Text CC BY 4.0; schema Apache-2.0 |
| `scripts/` | Stage validator, report-schema generator, `bl-score` pin check, public leak check, and their tests | Apache-2.0 |
| `templates/` | Provenance ledger schema | Apache-2.0 |

`LICENSE.md` gives the exact split.

## Run the checks

Python 3.11 or newer. From the repository root:

```bash
python -m venv .venv && . .venv/bin/activate
pip install pyyaml jsonschema pytest
pip install ./tools/bl-score

# Policy
python policy/scripts/validate_policy.py --policy-dir policy
python -m pytest policy/tests

# bl-score
python -m pytest tools/bl-score/tests
bl-score tools/bl-score/examples/green_p0.yaml

# Operating manual
python scripts/validate_stages.py manual/stages.yaml --dod manual/dod.yaml --tooling manual/tooling.lock.yaml
python scripts/gen_report_schemas.py --check
python scripts/pin_bl_score.py tools/bl-score --check manual/bl-score.pin.json
python -m pytest manual/tests scripts/tests

# Public leak check (no local paths, archive IDs, budgets or personal data)
python scripts/public_leak_check.py
```

Every command exits 0 when the files are consistent.

## Cite

`CITATION.cff` holds the citation. GitHub shows it under "Cite this repository".

> Bayanat Labs (2026). *Bayanat Labs open policies* (version 1.0.1). https://github.com/Bayanat-Labs/open-policies

To reuse the policy text, attribute it as "Policy by Bayanat Labs"; for the manual, "Operating manual by Bayanat Labs".

## Licences

- Text, documentation and data files: [Creative Commons Attribution 4.0 International](LICENSES/CC-BY-4.0.txt) (CC BY 4.0).
- Code, tests and the JSON Schemas outside `policy/`: [Apache License 2.0](LICENSES/Apache-2.0.txt).

See `LICENSE.md` for the folder-by-folder split.

## Contact, corrections and takedowns

Questions, corrections and takedown requests: **hello@bayanatlabs.com** (30-day removal SLA; 24 hours for platform requests). Issues are welcome; `CONTRIBUTING.md` explains how changes are made.

## ملخص بالعربية

The Arabic text has not yet been reviewed by a native Arabic writer; the English governs.

لا تنشر بيانات لابز (Bayanat Labs) بيانات عربية مفتوحة إلا حيث تستطيع ترخيصها. ويضم هذا المستودع قواعد برنامج البيانات المفتوحة ودليل بناء مجموعات البيانات، بالعربية والإنجليزية. وهو توثيق، وليس استشارة قانونية.

- **السياسة** (`policy/POLICY.ar.md`): معايير الاختيار، ومستويات النشر، ومصفوفة التراخيص. مراجعة المستشار القانوني: أكتوبر 2026.
- **دليل التشغيل** (`manual/PUBLIC.ar.md`): تمر كل مجموعة بيانات مفتوحة تصدرها بيانات لابز بالعملية نفسها. تبدأ بمذكرة تحديد نطاق من صفحة واحدة، ثم تمر بـ12 مرحلة أخرى. وتنتهي كل مرحلة ببوابة، وكل بوابة مانعة.
- **أداة التقييم** `tools/bl-score` (رخصة Apache-2.0).

ترخيص النصوص: رخصة CC BY 4.0. وترخيص الشيفرة البرمجية: رخصة Apache-2.0. وعند اختلاف النصين يُعتمد النص الإنجليزي.

للأسئلة والتصحيحات وطلبات الإزالة: **hello@bayanatlabs.com** (مهلة الإزالة 30 يومًا، و24 ساعة لطلبات المنصات).
