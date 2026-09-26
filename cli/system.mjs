import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

export const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
export const PKG = JSON.parse(fs.readFileSync(path.join(ROOT, 'package.json'), 'utf8'));
export const home = (env = process.env) => path.resolve(env.CODEX_HOME || path.join(os.homedir(), '.codex'));
export function safePath(value) {
  if (typeof value !== 'string' || !value || /[\x00-\x1f\x7f]/.test(value)) throw new Error('Invalid path.');
  return path.resolve(value);
}
export function regular(file) {
  const info = fs.lstatSync(file, {throwIfNoEntry: false});
  if (info && (!info.isFile() || info.isSymbolicLink())) throw new Error(`Expected a regular file: ${file}`);
}
export function privateDir(directory) {
  safePath(directory);
  // Check ancestors before following them during setup-owned writes.
  for (let current = directory; current !== path.dirname(current); current = path.dirname(current)) {
    const info = fs.lstatSync(current, {throwIfNoEntry: false});
    // macOS exposes these root-owned system aliases for its private directories.
    if (info?.isSymbolicLink() && info.uid === 0 && ['/var', '/tmp'].includes(current) &&
        fs.realpathSync(current) === `/private${current}`) continue;
    if (info && (!info.isDirectory() || info.isSymbolicLink())) throw new Error(`Unsafe directory: ${current}`);
  }
  fs.mkdirSync(directory, {recursive: true, mode: 0o700});
  fs.chmodSync(directory, 0o700);
}
export function atomic(file, value) {
  regular(file);
  const temporary = `${file}.${crypto.randomUUID()}.tmp`;
  try {
    fs.writeFileSync(temporary, value, {mode: 0o600, flag: 'wx'});
    fs.renameSync(temporary, file);
  } finally {
    fs.rmSync(temporary, {force: true});
  }
}
export function which(name, env = process.env) {
  for (const directory of (env.PATH || '').split(path.delimiter)) {
    if (!directory) continue;
    const file = path.join(directory, name);
    try { fs.accessSync(file, fs.constants.X_OK); if (fs.statSync(file).isFile()) return file; } catch {}
  }
  return null;
}
export function run(command, args, options = {}) {
  const result = spawnSync(command, args, {encoding: 'utf8', timeout: 120_000, maxBuffer: 4 * 1024 * 1024,
    shell: false, env: process.env, ...options});
  return {status: result.status ?? 2, stdout: result.stdout || '', stderr: result.stderr || '', error: result.error};
}
export function diagnosticText(value, ctx, limit = 2000) {
  let text = String(value ?? '');
  // Redact before truncating so a boundary cannot disclose a partial secret.
  for (const [key, secret] of Object.entries(ctx.env || {})) {
    if (/token|secret|password|passwd|credential|api.?key|authorization/i.test(key) && secret) {
      text = text.split(String(secret)).join('[REDACTED]');
    }
  }
  text = text.replace(/(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]+)/g, '[REDACTED]')
    .replace(/(bearer\s+)\S+/gi, '$1[REDACTED]')
    .replace(/((?:token|password|secret|api[_-]?key)\s*[=:]\s*)[^\s,;]+/gi, '$1[REDACTED]')
    .replace(/[\x00-\x08\x0b-\x1f\x7f]/g, '');
  return text.slice(0, limit) + (text.length > limit ? '… [truncated]' : '');
}
function captured(result, command, args, ctx) {
  return `\ncommand: ${diagnosticText([path.basename(command), ...args].join(' '), ctx)}\nexit status: ${result.status}` +
    `\nstdout prefix: ${diagnosticText(result.stdout, ctx)}\nstderr prefix: ${diagnosticText(result.stderr || result.error?.message, ctx)}`;
}
function versionDetail(ctx) {
  return ctx.codexVersion ? `\nCodex version: ${diagnosticText(ctx.codexVersion, ctx, 200)}` : '';
}
export function checked(command, args, ctx, options = {}) {
  const result = ctx.run(command, args, options);
  if (result.status !== 0) {
    throw new Error(`Command failed: ${diagnosticText([path.basename(command), ...args].join(' '), ctx)}.` +
      versionDetail(ctx) + (ctx.verbose ? captured(result, command, args, ctx) : '') +
      '\nRun it manually, then rerun the GitHub release setup command.');
  }
  return result;
}
export function parseJSON(output, label) {
  try { return JSON.parse(output); } catch { throw new Error(`${label} did not return parseable JSON.`); }
}
export function codexJSON(ctx, args, label) {
  const readOnly = ['plugin list --json', 'plugin marketplace list --json'].includes(args.join(' '));
  if (!ctx.codexVersion) {
    const version = ctx.run(ctx.codex, ['--version'], {timeout: 10_000});
    ctx.codexVersion = version.status === 0 ? version.stdout.trim() : 'unavailable';
  }
  let result;
  for (let attempt = 0; attempt < (readOnly ? 2 : 1); attempt++) {
    result = checked(ctx.codex, args, ctx, {timeout: 30_000});
    try { return JSON.parse(result.stdout); } catch {}
  }
  const next = readOnly ? `Retry:\n  codex ${args.join(' ')}` :
    'The command may have changed state. Inspect codex plugin marketplace list --json and codex plugin list --json before retrying setup.';
  throw new Error(`${label} did not return parseable JSON.\n${versionDetail(ctx)}\n\n${next}` +
    '\nRun setup with --verbose to inspect captured output.' +
    (ctx.verbose ? captured(result, ctx.codex, args, ctx) : ''));
}
export function manifest(root) {
  const value = JSON.parse(fs.readFileSync(path.join(root, '.codex-plugin/plugin.json'), 'utf8'));
  if (value.name !== 'claim-verifier' || typeof value.version !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9.+_-]{0,127}$/.test(value.version)) {
    throw new Error('Invalid Claim Verifier manifest.');
  }
  for (const file of ['hooks/hooks.json', 'hooks/claim_verifier.py', 'claim_verifier/hook.py']) {
    regular(path.join(root, file));
    if (!fs.existsSync(path.join(root, file))) throw new Error(`Plugin file missing: ${file}`);
  }
  const hooks = JSON.parse(fs.readFileSync(path.join(root, 'hooks/hooks.json'), 'utf8'));
  for (const name of ['UserPromptSubmit', 'PostToolUse', 'Stop']) {
    if (!Array.isArray(hooks.hooks?.[name]) || !hooks.hooks[name].length) throw new Error(`Plugin hook missing: ${name}`);
  }
  return value;
}
export function runtimeFiles(root) {
  const files = ['.codex-plugin/plugin.json'];
  // Legacy installed payloads predate release notices; preserve their identity.
  for (const notice of ['LICENSE', 'THIRD_PARTY.md']) {
    if (fs.existsSync(path.join(root, notice))) files.push(notice);
  }
  function visit(directory) {
    for (const entry of fs.readdirSync(path.join(root, directory), {withFileTypes: true})) {
      if (entry.name === '__pycache__') continue;
      const relative = `${directory}/${entry.name}`;
      if (entry.isSymbolicLink()) throw new Error(`Plugin payload must not contain symlinks: ${relative}`);
      if (entry.isDirectory()) visit(relative);
      else if (/\.(py|json|mjs)$/.test(entry.name)) files.push(relative);
    }
  }
  for (const dir of ['claim_verifier', 'hooks', 'scripts']) visit(dir);
  return files.sort();
}
export function identity(root) {
  const digest = crypto.createHash('sha256');
  for (const file of runtimeFiles(root)) digest.update(file).update('\0').update(fs.readFileSync(path.join(root, file))).update('\0');
  return digest.digest('hex');
}
export function listing(ctx) {
  const value = codexJSON(ctx, ['plugin', 'list', '--json'], 'Codex plugin list');
  if (!value || !Array.isArray(value.installed)) throw new Error('Unsupported Codex plugin listing format. Update Codex CLI.');
  return value.installed;
}
export function installed(ctx, records, selector = 'claim-verifier@personal') {
  const record = records.find(item => item.pluginId === selector && item.installed === true);
  if (!record) return {installed: false};
  if (typeof record.version !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9.+_-]{0,127}$/.test(record.version)) throw new Error('Invalid installed plugin version.');
  const market = record.marketplaceName;
  if (typeof market !== 'string' || !/^[A-Za-z0-9_-]+$/.test(market)) throw new Error('Invalid installed marketplace name.');
  const root = path.join(ctx.home, 'plugins/cache', market, 'claim-verifier', record.version);
  return {installed: true, enabled: record.enabled, version: record.version, root, selector: record.pluginId};
}
export function bridge(ctx, command, installation = {}, extra = []) {
  const result = ctx.run(ctx.python, ['-B', path.join(ROOT, 'scripts/public_cli.py'), command,
    '--installation', JSON.stringify(installation), ...extra], {timeout: 30_000});
  if (!result.stdout || result.status !== 0) {
    let message = 'Claim Verifier diagnostics could not run. Rerun with --verbose.';
    try { message = JSON.parse(result.stdout).error || message; } catch {}
    if (ctx.verbose && result.stderr) message += `\n${diagnosticText(result.stderr, ctx)}`;
    throw new Error(message);
  }
  const value = parseJSON(result.stdout, 'Claim Verifier diagnostics');
  if (value.error) throw new Error(value.error);
  return value;
}
export function renderDoctor(status, output, verbose = false) {
  for (const [key, label] of [['installation', 'Installation'], ['configuration', 'Configuration'],
    ['audit_storage', 'Audit storage'], ['hooks_observed', 'Hooks observed'], ['audit_generation', 'Audit generation']]) {
    output(`${status[key] ? '✓' : '✗'} ${label}`);
  }
  output(`\n${status.status}`);
  for (const item of [...status.errors, ...status.attention]) output(item);
  if (verbose) {
    output('\nHooks');
    for (const hook of ['UserPromptSubmit', 'PostToolUse', 'Stop']) output(`${status.hooks_seen?.includes(hook) ? '✓' : '✗'} ${hook}`);
    output(JSON.stringify(status, null, 2));
  }
}
