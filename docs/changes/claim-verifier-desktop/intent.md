# Desktop hook observability

## Problem

The installed Claim Verifier has no simple way to tell whether a fresh Codex task started in the ChatGPT desktop app executed its local hooks. A plugin listing and a stored receipt do not establish hook execution or receipt visibility in that surface.

## Outcome

Give the user a local, low-sensitivity diagnostic trail and commands that identify observed hook stages and recent audits. Run fresh CLI and desktop smoke tasks before classifying desktop support. Preserve the verifier's evidence and receipt trust boundaries.

## Success

- A tagged smoke task can be located without opening hashed ledger files.
- The three hook invocations and Stop audit creation are independently visible.
- A user can inspect the latest audit and distinguish installed, trusted, executed, and visible states.
- Desktop support claims are based on a known desktop task and its recorded events, not plugin presence or the marker alone.

## Constraints and exclusions

Do not store full prompts or tool output in diagnostics; the existing evidence ledger remains authoritative. Do not change claim decisions or have the audited agent write a receipt. Desktop UI integration is outside this change until runtime evidence supports it.
