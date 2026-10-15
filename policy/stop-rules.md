# Stop rules

> **Version 1.0.1 · Reviewed by counsel, October 2026.**
> Documentation, not legal advice.

Policy version 1.0.1 · Source: Bayanat Labs practice, adopted as policy · Licence: CC BY 4.0

## Source text

> **Stop rules:** a release that cannot pass the legal gate is converted to Tier 2 or dropped, never delayed indefinitely; a benchmark whose test set leaks is rotated within 30 days; any partner audio whose permission is withdrawn is removed within the SLA and the counter corrected publicly.

## Rules

| ID | Situation | What happens | Deadline | Related |
|---|---|---|---|---|
| SR-1 | A release cannot pass the legal gate | It is converted to Tier 2 or dropped, never delayed indefinitely | At the gate decision | rubric.yaml legal gate |
| SR-2 | A benchmark's test set leaks | The test set is rotated and a new version is published | Within 30 days | Maintenance rules |
| SR-3 | A partner withdraws permission for its audio | The audio is removed within the SLA and the public counter is corrected | Within the SLA (30 days) | tiers.yaml Tier 3 |

## Notes

- "Never delayed indefinitely" means a blocked release does not wait in the queue. The scoping memo records the decision (Tier 2 or drop) and work moves to an independently cleared source.
- A rotated test set keeps its canary GUID policy.
- A corrected counter is a public correction, logged in the release's `CHANGELOG.md`.
