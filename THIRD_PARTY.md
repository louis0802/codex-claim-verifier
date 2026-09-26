# Third-party notices and provenance

## Claim Verifier design reference

The MIT-licensed [`@sudhanshu1402/receipts`](https://www.npmjs.com/package/%40sudhanshu1402/receipts)
for Claude Code informed the receipt concept. The original implementation record
states that Claim Verifier was written independently; no code from that package
is included. The reference is retained as attribution. Claim Verifier's own
license is [MIT](LICENSE), copyright 2026 Louis.

## Portable Python

Setup can download CPython 3.13.15, python-build-standalone build 20260924, for macOS arm64 or x64. The package does not embed the binary archive. URLs and SHA-256 pins are in cli/python-downloads.json.

Upstream project: https://github.com/astral-sh/python-build-standalone
Metadata source read for these pins: https://raw.githubusercontent.com/astral-sh/uv/main/crates/uv-python/download-metadata.json (retrieved 2026-09-26).
Python management background: https://docs.astral.sh/uv/concepts/python-versions/

The extracted archive retains its upstream license/notice files. CPython and bundled dependencies retain their respective licenses. See the upstream release contents and https://docs.astral.sh/python-build-standalone/ for distribution details. Claim Verifier's MIT license does not replace these upstream licenses.
