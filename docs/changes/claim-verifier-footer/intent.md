# Claim Verifier footer: intent

## Problem and outcome
Users cannot see the verifier's conclusion without opening private JSON ledgers. Add a short, deterministic receipt for each Stop audit, tied to the structured audit result. Problem receipts should be actionable; successful receipts should stay compact.

## Users and measures
The owner of the personal plugin can configure the receipt globally or in a trusted project. Success means the renderer never labels unsupported or stale work as verified, reports repair state accurately, and stores the exact receipt for later inspection. All existing verification behavior stays intact.

## Runtime constraint and scope
The installed Codex Stop hook cannot rewrite the final answer. Its `systemMessage` is documented as a UI warning. A live CLI probe on 2026-09-25 produced a `CORRECT` audit and hook completion, but showed no `systemMessage` in normal or JSON CLI output. Delivery is therefore best effort on the current runtime, not a guarantee of a visible final-answer footer. The feature includes local rendering, audit storage, and supported hook delivery; native final-answer insertion, dashboards, and remote services are excluded.
