# Claim Verifier footer: verification

## Automated checks
- `python3 -m unittest discover -s tests -q`: 38 passed, including the original 18 and exact-string renderer and integration cases.
- `python3 -m compileall -q claim_verifier hooks scripts tests`: passed.
- Plugin-creator `validate_plugin.py`: passed for the deliverable, personal source, and installed cache package. SHA-256 comparisons of all changed runtime/test files matched between deliverable and installed cache.

## Runtime presentation probes
- Preimplementation `receipts + warn` probe: Stop audited the answer `Tests pass.` as `CORRECT/UNVERIFIED`. Normal CLI output ended with the model answer; no warning receipt appeared. A second `--json` probe emitted `agent_message` and `turn.completed`, with no `systemMessage` event.
- Updated plugin in directory A, ordinary CLI invocation: no ledger file was created. The hooks remain untrusted and were skipped. This is a new task; installation alone did not activate them.
- Updated plugin in directory A, vetted one-off trust bypass: the stored audit contained `CORRECT/UNVERIFIED`, an adaptive detailed receipt, and `channel=systemMessage`. The CLI JSON stream showed only the model answer and no receipt.
- Updated plugin in directory B, trusted project override `delivery=system-message`, vetted one-off trust bypass: the stored audit contained `PASS`, `0 claims checked`, and `channel=systemMessage`. The CLI JSON stream again showed only the model answer.

The one-off bypass confirms hook computation and storage, not persistent trust. The official Codex hook documentation describes `systemMessage` as a UI warning, and the tested CLI did not surface it. No desktop UI receipt placement was verified. The final-answer footer goal therefore remains limited by the current hook presentation API and the user's pending `/hooks` trust review.
