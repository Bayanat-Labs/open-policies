# Changelog: Bayanat Labs open-programme policy

> **Version 1.0.1 · Reviewed by counsel, October 2026.**
> Documentation, not legal advice.

All changes to the policy files are recorded here, newest first. Versions follow `MAJOR.MINOR.PATCH` plus a date.

## [Unreleased]

- A blind top-10 ranking made without the rubric scores. Until it is compared with the rubric scores, the priority thresholds are adopted for v1.0 and provisional.

## [1.0.1] - 2026-10-15

First public version. Adopted. Reviewed by counsel, October 2026.

### Contents
- `POLICY.md` in English and `POLICY.ar.md` in Arabic: operating principles, release tiers, licence matrix, index-only and stop rules, the gating rule, claims rules, selection rubric and legal notes. The Arabic text has not yet been reviewed by a native Arabic writer; the English governs.
- Machine-readable files `rubric.yaml`, `tiers.yaml`, `licence-matrix.yaml`, `principles.yaml` and `index-only-rules.yaml`, each with a JSON Schema in `schemas/`. `policy_version` takes the form `MAJOR.MINOR.PATCH`.
- Release tiers and licence routes are described by licence class (`POLICY.md` sections 3 and 4).
- Selection rubric: five criteria weighted 30/20/20/20/10. Legal cleanliness is a gate: the more restrictive of `legal_tier` and the `legal_cleanliness` score applies, and the red anchor reads "Red legal tier: not built". Priority thresholds are adopted for v1.0, provisional; the coordinator decides each case. `tools/bl-score` ships this rubric and reports `policy_version` 1.0.1.
- No release is gated: safety sets ship only as hidden test sets evaluated by submission (`gating-exception.md`).
- `scripts/validate_policy.py` and its tests check the schemas, the semantic rules, the wording in `fidelity/checklist.yaml`, the banners (version, review line, not-legal-advice notice, no draft marker), one policy version across all files, the same numbered sections in `POLICY.md` and `POLICY.ar.md`, and that every YAML file in the folder is one the validator knows.
- Contact and takedown address: hello@bayanatlabs.com.
