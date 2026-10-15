# Bayanat Labs open-programme policy

> **Version 1.0.1 · Reviewed by counsel, October 2026.**
> **Documentation, not legal advice.** These files state the rules Bayanat Labs follows when it chooses, licenses and publishes open Arabic data. They are not a legal opinion and not advice to anyone else.

## What is here

| File | What it holds |
|---|---|
| `POLICY.md` | The policy in English: principles, release tiers, licence matrix, index-only and stop rules, gating exception, claims rules, selection rubric and legal notes |
| `POLICY.ar.md` | The policy in Arabic. The English text governs if the two differ |
| `rubric.yaml` | The five-criteria selection rubric, weights, anchors, legal gate and priority and effort codes |
| `tiers.yaml` | The three release tiers |
| `licence-matrix.yaml` | Release licence tags, and the input allowlist and blocklist |
| `principles.yaml` | The five operating principles |
| `index-only-rules.yaml` | When a release moves from publishing content to publishing an index only |
| `stop-rules.md`, `gating-exception.md`, `claims-rules.md` | Stop rules, the gating rule (no release is gated) and the claims-ledger rules |
| `schemas/` | JSON Schemas for every YAML file |
| `fidelity/checklist.yaml` | The wording each file must keep |
| `scripts/validate_policy.py`, `tests/` | The validator and its tests |
| `CHANGELOG.md` | Every change, newest first |

## Check the files

```bash
pip install pyyaml jsonschema pytest
python scripts/validate_policy.py
python -m pytest tests
```

`validate_policy.py` exits 0 when every check passes.

## Reuse and contact

The policy text and YAML files are CC BY 4.0 (attribution: "Policy by Bayanat Labs"); the scripts and tests are Apache-2.0. Questions, corrections and takedown requests: hello@bayanatlabs.com.
