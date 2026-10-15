# Gating exception

> **Version 1.0.1 · Reviewed by counsel, October 2026.**
> Documentation, not legal advice.

Policy version 1.0.1 · Source: Bayanat Labs practice, adopted as policy · Licence: CC BY 4.0

## The rule

Every Bayanat Labs release is ungated (operating principle 2: "Never gate, use permissive licences, and ship the full launch bundle every time").

**In v1.0 there is no gating exception.** Safety evaluation sets with residual sensitivity are not gated either: they are kept as hidden test sets and evaluated by submission.

## What this means

| Question | Answer |
|---|---|
| May any release be gated? | No. Safety sets are not gated, and every other release is ungated. |
| What happens to safety sets with residual sensitivity? | They are not released as downloads, gated or otherwise. They are kept as hidden test sets, and systems are evaluated by submission. |
| Does gating make unlicensable content publishable? | No. Content Bayanat Labs cannot license stays internal, even gated or "research only" (tiers.yaml internal-only rule). |
| Can the exception come back? | Only through a new policy version, announced in `CHANGELOG.md`. |

