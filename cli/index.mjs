#!/usr/bin/env node
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { PKG, home, which, run, installed, listing, bridge, renderDoctor } from './system.mjs';
import { findPython } from './python.mjs';
import { setup, selectedPlugin } from './setup.mjs';

export function parse(argv) {
  const flags = {};
  const words = [];
  const names = {'--verbose': 'verbose', '--no-launch': 'noLaunch', '--upgrade': 'upgrade', '--yes': 'yes', '--dry-run': 'dryRun'};
  for (let index = 0; index < argv.length; index++) {
    const word = argv[index];
    if (names[word]) flags[names[word]] = true;
    else if (word === '--source' || word === '--plugin-version') {
      const value = argv[++index];
      if (!value || value.startsWith('--')) throw new Error(`Missing value for ${word}.`);
      flags[word === '--source' ? 'source' : 'pluginVersion'] = value;
    } else if (word.startsWith('-')) {
      if (word === '--help' || word === '-h') flags.help = true;
      else throw new Error(`Unknown option: ${word}`);
    } else words.push(word);
  }
  const command = words[0] || 'help';
  if (!['setup', 'doctor', 'audit', 'version', 'help'].includes(command)) throw new Error(`Unknown command: ${command}`);
  if (command === 'audit' && (!['latest', 'list'].includes(words[1]) || words.length !== 2)) throw new Error('Use claim-verifier audit latest or audit list.');
  if (command !== 'audit' && words.length > 1) throw new Error('Unexpected command arguments.');
  if (command !== 'setup' && Object.keys(flags).some(key => !['verbose', 'help'].includes(key))) throw new Error('Setup options are only valid for setup.');
  return {command, subcommand: words[1], flags};
}
export async function main(argv = process.argv.slice(2), overrides = {}) {
  const {command, subcommand, flags} = parse(argv);
  const ctx = {env: process.env, home: home(), userHome: os.homedir(), platform: process.platform,
    arch: process.arch, nodeVersion: process.versions.node, tty: Boolean(process.stdin.isTTY && process.stdout.isTTY),
    run, output: console.log, verbose: Boolean(flags.verbose), ...overrides};
  if (flags.help || command === 'help') {
    ctx.output('Claim Verifier\n\nCommands: setup, doctor, audit latest, audit list, version\n\nSetup flags: --verbose --no-launch --upgrade --yes --dry-run\nSources: --source <marketplace-root|owner/repo|https-git-url> [--plugin-version <ref>]\nPublic Preview: use npx --package <GitHub release tarball URL> claim-verifier setup');
    return 0;
  }
  if (command === 'setup') return setup(ctx, flags);
  ctx.codex = which('codex', ctx.env);
  let plugin = {installed: false};
  if (ctx.codex) plugin = installed(ctx, listing(ctx), selectedPlugin(ctx));
  if (command === 'version') {
    ctx.output(`Claim Verifier CLI: ${PKG.version}\nPlugin: ${plugin.version || 'not installed'}\nConfig schema: 1`);
    return 0;
  }
  if (!ctx.codex && command === 'doctor') {
    ctx.output('BROKEN INSTALLATION\nCodex CLI is missing from PATH. Run Claim Verifier setup from the GitHub release package.');
    return 2;
  }
  ctx.python = findPython(ctx);
  if (!ctx.python) throw new Error('Python runtime is unavailable. Run Claim Verifier setup from the GitHub release package.');
  if (command === 'doctor') {
    const status = bridge(ctx, 'doctor', plugin);
    renderDoctor(status, ctx.output, flags.verbose);
    return status.exit_code;
  }
  const result = bridge(ctx, `audit-${subcommand}`);
  if (subcommand === 'latest') ctx.output(result.text);
  else {
    ctx.output('Claim Verifier — Audits');
    if (!result.audits.length) ctx.output('No audits found.');
    for (const audit of result.audits) ctx.output(`${audit.timestamp || 'unknown'}  ${audit.session}  ${audit.result || 'unknown'}`);
  }
  return 0;
}
if (process.argv[1] && fs.realpathSync(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { process.exitCode = await main(); }
  catch (error) { console.error(`✗ ${error.message}`); process.exitCode = 2; }
}
