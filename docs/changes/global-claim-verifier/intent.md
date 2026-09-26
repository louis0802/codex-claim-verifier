# Global claim verifier: intent

## Problem
Codex can describe tests, edits, commits, pushes, or reviews as completed without execution evidence. A user working across many repositories needs one reusable guardrail that compares final claims with machine-observed actions.

## Outcome
Install a personal Codex plugin whose hooks record supported tool outcomes and inspect the proposed final answer. Unsupported execution claims receive an audit finding. At stronger settings, the hook asks Codex to complete work the user required before finishing. The verifier never runs the missing action itself.

## Success measures
- A false test-success claim without a test run produces an unsupported finding.
- A required but unrun test produces a repair request at `complete`.
- A test result becomes stale after a later file change.
- An unrequested push is never initiated by the verifier.
- The plugin works in multiple local repositories after one personal installation, subject to Codex hook trust and tool coverage.

## Constraints and exclusions
- Use documented Codex plugin hooks and local plugin data storage. Preserve Codex permissions for repairs.
- `Stop` provides a continuation request, not an absolute final-message veto; some hosted/specialized tools do not emit `PostToolUse`. The ledger must mark missing evidence as unknown rather than proof of nonexecution.
- The Claude Code `@sudhanshu1402/receipts` package is an MIT-licensed design reference; implementation is original and does not parse Claude transcripts.
- Deployment and complex semantic compatibility proofs are beyond the initial implementation.
