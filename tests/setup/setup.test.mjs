import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import crypto from 'node:crypto';
import { main, parse } from '../../cli/index.mjs';
import { setup, validateSource, ensureCodex, registerPersonal, stageBundled, onboarding } from '../../cli/setup.mjs';
import { ROOT, run, identity } from '../../cli/system.mjs';
import { downloadVerified, ensurePython } from '../../cli/python.mjs';

const python = spawnSync('python3', ['-c', 'import sys;print(sys.executable)'], {encoding: 'utf8'}).stdout.trim();
function fixture(t, options = {}) {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), 'claim-setup-'));
  t.after(() => fs.rmSync(base, {recursive: true, force: true}));
  const userHome = path.join(base, 'user');
  const codexHome = path.join(base, 'custom-codex');
  const bin = path.join(base, 'bin');
  fs.mkdirSync(bin, {recursive: true}); fs.mkdirSync(userHome);
  for (const name of ['codex', 'npm', 'npx']) {
    if (options.missingCodex && name === 'codex' || options.missingNpm && name === 'npm') continue;
    fs.writeFileSync(path.join(bin, name), '#!/bin/sh\nexit 0\n', {mode: 0o700});
  }
  const calls = [], output = [];
  const env = {...process.env, HOME: userHome, CODEX_HOME: codexHome, PATH: bin, PYTHONDONTWRITEBYTECODE: '1'};
  delete env.PLUGIN_DATA; delete env.PLUGIN_ROOT;
  let records = [];
  const ctx = {home: codexHome, userHome, env, platform: 'darwin', arch: 'arm64', nodeVersion: '22.0.0',
    tty: false, verbose: false, output: line => output.push(line)};
  ctx.run = (command, args, extra = {}) => {
    calls.push([command, ...args]);
    if (path.basename(command) === 'npm') {
      if (args[0] === 'prefix') return {status: 0, stdout: path.join(base, 'prefix') + '\n', stderr: ''};
      if (options.npmFailure) return {status: 1, stdout: '', stderr: 'permission denied'};
      if (!options.pathMissing) fs.writeFileSync(path.join(bin, 'codex'), '#!/bin/sh\n', {mode: 0o700});
      return {status: 0, stdout: '', stderr: ''};
    }
    if (path.basename(command) === 'codex') {
      if (!args.length) return {status: 0, stdout: '', stderr: ''};
      if (args[0] === '--version') return {status: 0, stdout: 'codex-cli fixture\n', stderr: ''};
      if (args[1] === 'list') return {status: 0, stdout: options.badListing ? '{}' : JSON.stringify({installed: records}), stderr: ''};
      if (args[1] === 'marketplace') return {status: 0, stdout: JSON.stringify({name: 'dev-market'}), stderr: ''};
      if (args[1] === 'add') {
        if (options.pluginFailure) return {status: 1, stdout: '', stderr: 'plugin failed'};
        const catalog = JSON.parse(fs.readFileSync(path.join(userHome, '.agents/plugins/marketplace.json')));
        const entry = catalog.plugins.find(item => item.name === 'claim-verifier');
        const source = path.resolve(userHome, entry.source.path);
        const manifest = JSON.parse(fs.readFileSync(path.join(source, '.codex-plugin/plugin.json')));
        const market = args[2].split('@')[1];
        const cached = path.join(codexHome, 'plugins/cache', market, 'claim-verifier', manifest.version);
        fs.cpSync(source, cached, {recursive: true});
        records = [{pluginId: args[2], marketplaceName: market, version: manifest.version, installed: true, enabled: true}];
        return {status: 0, stdout: '{}', stderr: ''};
      }
      throw new Error(`Unexpected Codex command: ${args}`);
    }
    if (args.includes('-I')) return {status: 0, stdout: python + '\n', stderr: ''};
    return run(command, args, {...extra, env});
  };
  return {ctx, base, output, calls, plugin: () => records[0], setDisabled: () => records[0].enabled = false};
}
function snapshot(root) {
  const value = [];
  if (!fs.existsSync(root)) return value;
  function visit(directory) {
    for (const item of fs.readdirSync(directory, {withFileTypes: true})) {
      const file = path.join(directory, item.name);
      const stat = fs.statSync(file);
      value.push([path.relative(root, file), stat.mode, item.isFile() ? fs.readFileSync(file).toString('hex') : null]);
      if (item.isDirectory()) visit(file);
    }
  }
  visit(root); return value;
}

test('fresh setup installs through Codex, preserves trust, and non-TTY never launches', async t => {
  const f = fixture(t, {missingCodex: true});
  fs.mkdirSync(f.ctx.home, {recursive: true});
  const trust = path.join(f.ctx.home, 'hook-trust.json'); fs.writeFileSync(trust, 'human-owned');
  assert.equal(await setup(f.ctx, {yes: true}), 0);
  assert.equal(fs.readFileSync(trust, 'utf8'), 'human-owned');
  assert.equal(f.calls.filter(call => call.includes('install')).length, 1);
  assert.equal(f.calls.filter(call => call[1] === 'plugin' && call[2] === 'add').length, 1);
  assert.ok(f.output.join('\n').includes('WAITING FOR HOOK REVIEW'));
  assert.equal(f.calls.filter(call => path.basename(call[0]) === 'codex' && call.length === 1).length, 0);
  assert.ok(!f.calls.flat().some(arg => /bypass|trusted|\/hooks/.test(arg)));
  const state = JSON.parse(fs.readFileSync(path.join(f.ctx.home, 'claim-verifier-installation.json')));
  assert.equal(state.ready, false); assert.equal(state.hook_trust, 'UNKNOWN');
  assert.equal(fs.statSync(path.join(f.ctx.home, 'plugin-data/claim-verifier')).mode & 0o777, 0o700);
});

test('second setup preserves exact custom config, state timestamp, source, and install', async t => {
  const f = fixture(t);
  await setup(f.ctx, {});
  const config = path.join(f.ctx.home, 'claim-verifier.toml');
  const custom = '# my comments\n[claim_verifier]\nlevel = "complete"\nenforcement = "report"\n';
  fs.writeFileSync(config, custom);
  const stamp = fs.statSync(config).mtimeMs;
  const statePath = path.join(f.ctx.home, 'claim-verifier-installation.json');
  const state = fs.readFileSync(statePath, 'utf8'), stateStamp = fs.statSync(statePath).mtimeMs;
  const catalog = fs.readFileSync(path.join(f.ctx.userHome, '.agents/plugins/marketplace.json'), 'utf8');
  f.calls.length = 0;
  await setup(f.ctx, {});
  assert.equal(fs.readFileSync(config, 'utf8'), custom); assert.equal(fs.statSync(config).mtimeMs, stamp);
  assert.equal(fs.readFileSync(statePath, 'utf8'), state); assert.equal(fs.statSync(statePath).mtimeMs, stateStamp);
  assert.equal(fs.readFileSync(path.join(f.ctx.userHome, '.agents/plugins/marketplace.json'), 'utf8'), catalog);
  assert.ok(!f.calls.some(call => call.includes('add') || call.includes('install')));
});

test('existing Codex is preserved and no npm reinstall occurs', async t => {
  const f = fixture(t, {missingNpm: true});
  await setup(f.ctx, {});
  assert.ok(!f.calls.some(call => path.basename(call[0]) === 'npm'));
});

test('missing npm produces actionable failure', async t => {
  const f = fixture(t, {missingCodex: true, missingNpm: true});
  await assert.rejects(setup(f.ctx, {}), /npm is missing/);
  assert.ok(!fs.existsSync(path.join(f.ctx.home, 'claim-verifier-setup.lock')));
});

test('npm install failure stops before plugin/config and never reports success', async t => {
  const f = fixture(t, {missingCodex: true, npmFailure: true});
  await assert.rejects(setup(f.ctx, {}), /Command failed: npm install/);
  assert.ok(!fs.existsSync(path.join(f.ctx.home, 'claim-verifier.toml')));
  assert.ok(!f.output.join('\n').includes('READY'));
});

test('successful npm install with PATH missing is diagnosed once', async t => {
  const f = fixture(t, {missingCodex: true, pathMissing: true});
  await assert.rejects(setup(f.ctx, {}), /not on PATH[\s\S]*npm global prefix:[\s\S]*PATH:/);
  assert.equal(f.calls.filter(call => call.includes('install')).length, 1);
});

test('an npm-prefix Codex absent from PATH is not reinstalled', t => {
  const f = fixture(t, {missingCodex: true});
  fs.mkdirSync(path.join(f.base, 'prefix/bin'), {recursive: true});
  fs.writeFileSync(path.join(f.base, 'prefix/bin/codex'), 'existing');
  assert.throws(() => ensureCodex(f.ctx), /not on PATH/);
  assert.equal(f.calls.filter(call => call.includes('install')).length, 0);
});

test('dry run has no filesystem mutations, Codex commands, install, or launch', async t => {
  const f = fixture(t, {missingCodex: true});
  const before = snapshot(f.base);
  await setup(f.ctx, {dryRun: true, yes: true});
  assert.deepEqual(snapshot(f.base), before);
  assert.ok(f.output.join('\n').includes('Would install Codex CLI'));
  assert.ok(!f.calls.some(call => ['codex', 'npm'].includes(path.basename(call[0]))));
});

test('upgrade refreshes plugin, preserves config, and prints review boundary', async t => {
  const f = fixture(t); await setup(f.ctx, {});
  const config = path.join(f.ctx.home, 'claim-verifier.toml');
  const content = fs.readFileSync(config, 'utf8'); f.calls.length = 0;
  await setup(f.ctx, {upgrade: true});
  assert.equal(fs.readFileSync(config, 'utf8'), content);
  assert.equal(f.calls.filter(call => call[2] === 'add').length, 1);
  assert.ok(f.output.join('\n').includes('may require a new review'));
});

test('catalog update preserves other entries, metadata, order and backup', t => {
  const f = fixture(t);
  const catalogPath = path.join(f.ctx.userHome, '.agents/plugins/marketplace.json');
  fs.mkdirSync(path.dirname(catalogPath), {recursive: true});
  const original = {name: 'personal', interface: {displayName: 'Mine'}, plugins: [{name: 'other', source: {source: 'local', path: './other'}, policy: {installation: 'AVAILABLE', authentication: 'ON_USE'}, category: 'Productivity'}]};
  fs.writeFileSync(catalogPath, JSON.stringify(original));
  registerPersonal(f.ctx, stageBundled(f.ctx));
  const after = JSON.parse(fs.readFileSync(catalogPath));
  assert.deepEqual(after.plugins[0], original.plugins[0]); assert.deepEqual(after.interface, original.interface);
  assert.equal(after.plugins[1].name, 'claim-verifier');
  const backup = fs.readdirSync(path.dirname(catalogPath)).find(name => name.startsWith('marketplace.json.backup-'));
  assert.equal(fs.readFileSync(path.join(path.dirname(catalogPath), backup), 'utf8'), JSON.stringify(original));
});

test('installed plugin payload retains project license and third-party notices', t => {
  const f = fixture(t);
  const staged = stageBundled(f.ctx);
  for (const name of ['LICENSE', 'THIRD_PARTY.md']) {
    assert.equal(fs.readFileSync(path.join(staged.root, name), 'utf8'),
      fs.readFileSync(path.join(ROOT, name), 'utf8'));
  }
});

test('plugin installation failure and malformed listing stop setup', async t => {
  for (const options of [{pluginFailure: true}, {badListing: true}]) {
    const f = fixture(t, options);
    await assert.rejects(setup(f.ctx, {}), options.pluginFailure ? /Command failed: codex plugin add/ : /listing format/);
    assert.ok(!f.output.join('\n').includes('READY'));
  }
});

test('existing disabled plugin stays disabled and reports attention', async t => {
  const f = fixture(t); await setup(f.ctx, {}); f.setDisabled(); f.output.length = 0; f.calls.length = 0;
  assert.equal(await setup(f.ctx, {}), 1);
  assert.ok(f.output.join('\n').includes('disabled in Codex'));
  assert.ok(!f.output.join('\n').includes('ACTION REQUIRED'));
  assert.ok(!f.calls.some(call => call.includes('add')));
});

test('invalid config is preserved and validation fails', async t => {
  const f = fixture(t); fs.mkdirSync(f.ctx.home, {recursive: true});
  const config = path.join(f.ctx.home, 'claim-verifier.toml'); fs.writeFileSync(config, '[claim_verifier]\nlevel = "wrong"\n');
  await assert.rejects(setup(f.ctx, {}), /validation failed/);
  assert.equal(fs.readFileSync(config, 'utf8'), '[claim_verifier]\nlevel = "wrong"\n');
});

test('TTY launch waits for Enter; --yes skips Enter; --no-launch never launches', async t => {
  for (const flags of [{}, {yes: true}, {noLaunch: true}]) {
    const f = fixture(t); f.ctx.tty = true; f.ctx.codex = path.join(f.base, 'bin/codex');
    let enters = 0; f.ctx.waitEnter = async () => enters++;
    await onboarding(f.ctx, flags, {status: 'WAITING FOR HOOK REVIEW'});
    assert.equal(enters, !flags.yes && !flags.noLaunch ? 1 : 0);
    assert.equal(f.calls.length, flags.noLaunch ? 0 : 1);
    if (f.calls.length) assert.deepEqual(f.calls[0], [f.ctx.codex]);
  }
});

test('READY resumption does not show review or launch', async t => {
  const f = fixture(t);
  await onboarding(f.ctx, {}, {status: 'READY'});
  assert.equal(f.output.length, 0); assert.equal(f.calls.length, 0);
});

test('source/version validation prevents unsafe selectors and shell interpolation', () => {
  for (const source of ['--evil', 'http://example.com/repo', 'https://user:pass@example.com/repo', 'https://example.com/repo?x=1', 'file:///tmp/repo', 'ssh://host/repo']) {
    assert.throws(() => validateSource(source), /source|HTTPS|Unsupported/);
  }
  for (const version of ['--evil', 'a;touch', '../main', 'a..b', '$(whoami)']) assert.throws(() => validateSource('owner/repo', version), /version/);
  assert.deepEqual(validateSource('owner/repo', 'v0.2.0'), {source: 'owner/repo', remote: true});
  assert.throws(() => validateSource(null, 'v0.2.0'), /requires --source/);
});

test('symlinked config and storage are rejected without target mutation', async t => {
  const f = fixture(t); fs.mkdirSync(f.ctx.home, {recursive: true});
  const target = path.join(f.base, 'target'); fs.writeFileSync(target, 'keep');
  fs.symlinkSync(target, path.join(f.ctx.home, 'claim-verifier.toml'));
  await assert.rejects(setup(f.ctx, {}), /regular file/);
  assert.equal(fs.readFileSync(target, 'utf8'), 'keep');
});

test('concurrent setup lock fails without deleting another process lock', async t => {
  const f = fixture(t); fs.mkdirSync(f.ctx.home, {recursive: true});
  const lock = path.join(f.ctx.home, 'claim-verifier-setup.lock'); fs.writeFileSync(lock, '999');
  await assert.rejects(setup(f.ctx, {}), /Another setup/); assert.equal(fs.readFileSync(lock, 'utf8'), '999');
});

test('Python downloads reject checksums before executable extraction', async t => {
  const f = fixture(t); const target = path.join(f.base, 'archive');
  const body = Buffer.from('archive data');
  const pin = {url: 'https://github.com/astral-sh/python-build-standalone/releases/download/test/python.tar.gz', sha256: '0'.repeat(64)};
  await assert.rejects(downloadVerified(pin, target, async () => new Response(body)), /checksum mismatch/);
  assert.ok(!fs.existsSync(target));
  const good = {...pin, sha256: crypto.createHash('sha256').update(body).digest('hex')};
  await downloadVerified(good, target, async () => new Response(body));
  assert.deepEqual(fs.readFileSync(target), body);
});

test('public command parsing, version, doctor exit, and audit availability', async t => {
  const f = fixture(t); await setup(f.ctx, {});
  assert.equal(await main(['doctor'], f.ctx), 1);
  assert.equal(await main(['version'], f.ctx), 0);
  assert.equal(await main(['audit', 'latest'], f.ctx), 0);
  assert.equal(await main(['audit', 'list'], f.ctx), 0);
  assert.ok(f.output.join('\n').includes('No audit found.'));
  assert.ok(f.output.join('\n').includes('Config schema: 1'));
  assert.throws(() => parse(['setup', '--unknown']), /Unknown option/);
  assert.throws(() => parse(['doctor', '--yes']), /only valid for setup/);
});

test('unsupported platforms fail before setup mutation', async t => {
  const f = fixture(t); f.ctx.platform = 'linux'; const before = snapshot(f.base);
  await assert.rejects(setup(f.ctx, {}), /macOS/); assert.deepEqual(snapshot(f.base), before);
});

test('real hook launcher processes activate installed package, doctor reaches READY, and setup resumes quietly', async t => {
  const f = fixture(t); await setup(f.ctx, {});
  const root = path.join(f.ctx.home, 'plugins/cache/personal/claim-verifier', f.plugin().version);
  const data = path.join(f.base, 'actual-runtime-data');
  const env = {...f.ctx.env, PLUGIN_ROOT: root, PLUGIN_DATA: data};
  for (const event of ['prompt', 'tool', 'stop']) {
    const payload = {session_id: 'launcher-smoke', cwd: f.base, prompt: 'Read README.', tool_name: 'Read',
      tool_input: {path: 'README.md'}, tool_response: {content: 'hello'}, last_assistant_message: 'Hello.'};
    const result = spawnSync(process.execPath, [path.join(root, 'hooks/run.mjs'), event],
      {env, encoding: 'utf8', input: JSON.stringify(payload)});
    assert.equal(result.status, 0, result.stderr);
    assert.ok(!result.stdout.includes('could not complete'));
  }
  assert.equal(await main(['doctor'], f.ctx), 0);
  assert.equal(await main(['audit', 'latest'], f.ctx), 0);
  f.output.length = 0;
  await setup(f.ctx, {});
  assert.ok(f.output.join('\n').includes('READY'));
  assert.ok(!f.output.join('\n').includes('ACTION REQUIRED'));
});

test('an older installation is preserved and needs explicit upgrade', async t => {
  const f = fixture(t); await setup(f.ctx, {});
  const root = path.join(f.ctx.home, 'plugins/cache/personal/claim-verifier', f.plugin().version);
  fs.unlinkSync(path.join(root, 'claim_verifier/install_state.py'));
  f.calls.length = 0; f.output.length = 0;
  assert.equal(await setup(f.ctx, {}), 1);
  assert.ok(f.output.join('\n').includes('predates automatic setup detection'));
  assert.ok(!f.calls.some(call => call.includes('add')));
});

test('custom PLUGIN_DATA storage is private and setup/doctor agree', async t => {
  const f = fixture(t); f.ctx.env.PLUGIN_DATA = path.join(f.base, 'custom-data');
  await setup(f.ctx, {});
  assert.equal(fs.statSync(f.ctx.env.PLUGIN_DATA).mode & 0o777, 0o700);
  assert.equal(JSON.parse(fs.readFileSync(path.join(f.ctx.home, 'claim-verifier-installation.json'))).data_root, fs.realpathSync(f.ctx.env.PLUGIN_DATA));
  assert.equal(await main(['doctor'], f.ctx), 1);
});

test('CLI doctor distinguishes absent Codex as broken', async t => {
  const f = fixture(t, {missingCodex: true});
  assert.equal(await main(['doctor'], f.ctx), 2);
  assert.ok(f.output.join('\n').includes('missing from PATH'));
});

test('npm bin symlink executes the CLI entry point', t => {
  const f = fixture(t);
  const bin = path.join(f.base, 'claim-verifier');
  fs.symlinkSync(path.join(ROOT, 'cli/index.mjs'), bin);
  const result = spawnSync(process.execPath, [bin, '--help'], {encoding: 'utf8'});
  assert.equal(result.status, 0, result.stderr);
  assert.ok(result.stdout.includes('Commands: setup, doctor'));
});
