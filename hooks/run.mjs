#!/usr/bin/env node
// Hook runtime launcher only; setup never makes verification decisions.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const home = process.env.CODEX_HOME || path.join(os.homedir(), '.codex');
let python = 'python3';
try {
  const binding = JSON.parse(fs.readFileSync(path.join(home, 'claim-verifier/runtime.json'), 'utf8'));
  if (binding.schema_version !== 1 || typeof binding.python !== 'string' || !path.isAbsolute(binding.python) || /[\x00-\x1f]/.test(binding.python)) {
    throw new Error('Invalid runtime binding');
  }
  python = binding.python;
} catch (error) {
  if (error.code !== 'ENOENT') {
    console.log(JSON.stringify({systemMessage: 'Claim Verifier runtime configuration is invalid. Run claim-verifier doctor --verbose.'}));
    process.exit(0);
  }
}
const result = spawnSync(python, ['-B', path.join(root, 'hooks/claim_verifier.py'), process.argv[2] || ''],
  {shell: false, stdio: 'inherit'});
if (result.error || result.status !== 0) console.log(JSON.stringify({systemMessage: 'Claim Verifier runtime failed. Run claim-verifier doctor --verbose.'}));
