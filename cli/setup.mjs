import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { createInterface } from 'node:readline/promises';
import { ROOT, safePath, privateDir, regular, atomic, which, checked, manifest, runtimeFiles, identity,
  installed, listing, bridge, parseJSON, renderDoctor } from './system.mjs';
import { ensurePython, findPython } from './python.mjs';

export function validateSource(source, version) {
  if (version && (!/^[A-Za-z0-9][A-Za-z0-9.+_/-]{0,127}$/.test(version) || version.includes('..') || version.includes('//'))) {
    throw new Error('Invalid plugin version/ref.');
  }
  if (!source) {
    if (version) throw new Error('--plugin-version requires --source. Pin bundled releases with a versioned GitHub release tarball.');
    return null;
  }
  if (typeof source !== 'string' || /[\x00-\x20\x7f]/.test(source) && !path.isAbsolute(source)) throw new Error('Invalid marketplace source.');
  if (/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(source) && !source.split('/').some(part => part.startsWith('.'))) return {source, remote: true};
  if (source.startsWith('https://')) {
    const url = new URL(source);
    if (url.username || url.password || url.search || url.hash || !url.hostname || !url.pathname || url.pathname === '/') {
      throw new Error('Use an HTTPS Git marketplace URL without credentials, query or fragment.');
    }
    return {source: url.href, remote: true};
  }
  if (/^[a-z][a-z0-9+.-]*:/i.test(source) || source.startsWith('-')) throw new Error('Unsupported marketplace source. Use HTTPS Git, owner/repo, or a local root.');
  const root = safePath(source);
  const catalog = JSON.parse(fs.readFileSync(path.join(root, '.agents/plugins/marketplace.json'), 'utf8'));
  validateCatalog(catalog);
  const entry = catalog.plugins.find(item => item.name === 'claim-verifier');
  if (!entry) throw new Error('Marketplace does not contain Claim Verifier.');
  if (version) {
    if (entry.source?.source !== 'local') throw new Error('Use --plugin-version with a Git marketplace source to pin its ref.');
    const sourceRoot = path.resolve(root, entry.source.path);
    if (manifest(sourceRoot).version !== version) throw new Error('Local plugin version does not match --plugin-version.');
  }
  return {source: root, remote: false, name: catalog.name};
}
function validateCatalog(value) {
  if (!value || typeof value !== 'object' || !/^[A-Za-z0-9_-]+$/.test(value.name || '') || !Array.isArray(value.plugins)) {
    throw new Error('Invalid marketplace manifest.');
  }
}
export function selectedPlugin(ctx) {
  try {
    const value = JSON.parse(fs.readFileSync(path.join(ctx.home, 'claim-verifier-installation.json'), 'utf8'));
    if (value.selector && /^claim-verifier@[A-Za-z0-9_-]+$/.test(value.selector)) return value.selector;
  } catch (error) { if (error.code !== 'ENOENT') throw new Error('Installation state is unreadable. Run doctor --verbose.'); }
  return 'claim-verifier@personal';
}
export function ensureCodex(ctx) {
  let executable = which('codex', ctx.env);
  if (!executable) {
    const npm = which('npm', ctx.env);
    if (!npm) throw new Error('npm is missing. Install Node.js with npm, then rerun the GitHub release setup command.');
    const existingPrefix = ctx.run(npm, ['prefix', '-g'], {timeout: 10_000});
    const prefixPath = existingPrefix.stdout.trim();
    if (existingPrefix.status === 0 && path.isAbsolute(prefixPath) && fs.existsSync(path.join(prefixPath, 'bin/codex'))) {
      throw new Error(`Codex is installed in the npm global prefix but is not on PATH.\nnpm global prefix: ${prefixPath}\nPATH: ${ctx.env.PATH || '(empty)'}\nAdd ${path.join(prefixPath, 'bin')} to PATH, then rerun setup.`);
    }
    ctx.output('Installing Codex CLI…');
    checked(npm, ['install', '-g', '@openai/codex@latest'], ctx, {timeout: 300_000});
    executable = which('codex', ctx.env);
    if (!executable) {
      const prefix = ctx.run(npm, ['prefix', '-g'], {timeout: 10_000});
      throw new Error(`Codex was installed, but the executable is not on PATH.\nnpm global prefix: ${prefix.stdout.trim() || 'unavailable'}\nPATH: ${ctx.env.PATH || '(empty)'}\nAdd the npm prefix bin directory to PATH, then rerun setup. Codex will not be reinstalled in this run.`);
    }
  }
  const version = checked(executable, ['--version'], ctx, {timeout: 10_000}).stdout.trim();
  ctx.output(`✓ ${version || 'Codex CLI found'}`);
  return executable;
}
export function stageBundled(ctx) {
  const info = manifest(ROOT);
  // Codex local marketplace entries cannot escape their marketplace root (the user's home).
  const relativeHome = path.relative(ctx.userHome, ctx.home);
  const sourceHome = relativeHome.startsWith('..') || path.isAbsolute(relativeHome)
    ? path.join(ctx.userHome, '.agents/plugins/claim-verifier') : path.join(ctx.home, 'claim-verifier');
  const destination = path.join(sourceHome, 'releases', identity(ROOT));
  privateDir(path.dirname(destination));
  if (!fs.existsSync(destination)) {
    const stage = fs.mkdtempSync(path.join(path.dirname(destination), '.plugin-'));
    try {
      for (const relative of runtimeFiles(ROOT)) {
        privateDir(path.dirname(path.join(stage, relative)));
        fs.copyFileSync(path.join(ROOT, relative), path.join(stage, relative));
      }
      fs.renameSync(stage, destination);
    } finally { fs.rmSync(stage, {recursive: true, force: true}); }
  }
  if (identity(destination) !== identity(ROOT)) throw new Error('Staged plugin payload failed validation.');
  manifest(destination);
  return {root: destination, version: info.version};
}
export function registerPersonal(ctx, staged) {
  const catalogPath = path.join(ctx.userHome, '.agents/plugins/marketplace.json');
  privateDir(path.dirname(catalogPath));
  regular(catalogPath);
  const previous = fs.existsSync(catalogPath) ? fs.readFileSync(catalogPath, 'utf8') : null;
  const catalog = previous ? JSON.parse(previous) : {name: 'personal', interface: {displayName: 'Personal'}, plugins: []};
  validateCatalog(catalog);
  const sourcePath = './' + path.relative(ctx.userHome, staged.root).split(path.sep).join('/');
  const entry = {name: 'claim-verifier', source: {source: 'local', path: sourcePath},
    policy: {installation: 'AVAILABLE', authentication: 'ON_INSTALL'}, category: 'Productivity'};
  const index = catalog.plugins.findIndex(item => item.name === 'claim-verifier');
  if (index === -1) catalog.plugins.push(entry);
  else catalog.plugins[index] = {...catalog.plugins[index], ...entry};
  const content = JSON.stringify(catalog, null, 2) + '\n';
  if (previous !== content) {
    if (previous !== null) atomic(`${catalogPath}.backup-${crypto.randomUUID()}`, previous);
    atomic(catalogPath, content);
  }
  // The personal marketplace is implicitly discovered by Codex, including when its name differs.
  return `claim-verifier@${catalog.name}`;
}
export function installPlugin(ctx, flags, existing, source) {
  if (existing.installed && !flags.upgrade) {
    ctx.output('✓ Claim Verifier already installed');
    return existing;
  }
  let selector;
  if (source) {
    const args = ['plugin', 'marketplace', 'add', source.source, '--json'];
    if (source.remote && flags.pluginVersion) args.push('--ref', flags.pluginVersion);
    const value = parseJSON(checked(ctx.codex, args, ctx).stdout, 'Codex marketplace add');
    const name = source.name || value.marketplaceName || value.name || value.marketplace?.name;
    if (!/^[A-Za-z0-9_-]+$/.test(name || '')) throw new Error('Codex did not return a valid marketplace name. Run codex plugin marketplace list.');
    selector = `claim-verifier@${name}`;
  } else selector = registerPersonal(ctx, stageBundled(ctx));
  checked(ctx.codex, ['plugin', 'add', selector, '--json'], ctx);
  const result = installed(ctx, listing(ctx), selector);
  if (!result.installed) throw new Error('Plugin installation was not confirmed by Codex. Run claim-verifier doctor --verbose.');
  manifest(result.root);
  if (!source && identity(result.root) !== identity(ROOT)) {
    throw new Error('Codex cached a different payload for this plugin version. Release a new plugin version/cachebuster, then rerun setup --upgrade.');
  }
  ctx.output('✓ Claim Verifier plugin installed');
  return result;
}
export function configAndStorage(ctx) {
  const config = path.join(ctx.home, 'claim-verifier.toml');
  privateDir(ctx.home);
  regular(config);
  let created = false;
  try {
    fs.writeFileSync(config, fs.readFileSync(path.join(ROOT, 'claim-verifier.toml.example')), {flag: 'wx', mode: 0o600});
    created = true;
  } catch (error) { if (error.code !== 'EEXIST') throw error; }
  ctx.output(created ? '✓ Global configuration ready' : '✓ Existing configuration preserved');
  const data = safePath(ctx.env.PLUGIN_DATA || path.join(ctx.home, 'plugin-data/claim-verifier'));
  privateDir(data);
  ctx.output('✓ Audit storage ready');
  return data;
}
export async function onboarding(ctx, flags, status) {
  if (status.status === 'READY') return;
  if (status.status === 'WAITING FOR AUDIT') {
    ctx.output('Current hooks were observed. Start a new Codex task to produce a saved audit.');
    return;
  }
  if (status.status !== 'WAITING FOR HOOK REVIEW') return;
  ctx.output('\nACTION REQUIRED\n\nClaim Verifier is installed.\nCodex requires a one-time review before plugin hooks can execute.\n\nInside Codex enter:\n\n  /hooks\n\nReview and trust: Claim Verifier\nThen start a new Codex task. Activation is detected automatically.');
  if (flags.upgrade) ctx.output('Updated hook definitions may require a new review.');
  if (flags.noLaunch || !ctx.tty) { ctx.output('\nOpen Codex with: codex'); return; }
  if (!flags.yes) {
    if (ctx.waitEnter) await ctx.waitEnter();
    else {
      const reader = createInterface({input: process.stdin, output: process.stdout});
      try { await reader.question('\nPress Enter to open Codex…'); } finally { reader.close(); }
    }
  }
  ctx.output('Opening Codex…');
  const result = ctx.run(ctx.codex, [], {stdio: 'inherit', timeout: undefined});
  if (result.status !== 0) throw new Error('Codex exited unsuccessfully. Run codex manually, then /hooks.');
}
export async function setup(ctx, flags) {
  ctx.output('Claim Verifier Setup\n');
  if (ctx.platform !== 'darwin' || !['arm64', 'x64'].includes(ctx.arch)) throw new Error('Setup currently supports macOS arm64 and x64 only.');
  if (Number(ctx.nodeVersion.split('.')[0]) < 20) throw new Error('Node.js 20 or newer is required.');
  safePath(ctx.home);
  const source = validateSource(flags.source, flags.pluginVersion);
  ctx.output('✓ Node.js available');
  if (flags.verbose) ctx.output(`Platform: ${ctx.platform} ${ctx.arch}\nCodex home: ${ctx.home}\nnpm: ${which('npm', ctx.env) || 'missing'}\nnpx: ${which('npx', ctx.env) || 'missing'}`);
  if (flags.dryRun) {
    const codex = which('codex', ctx.env);
    const config = path.join(ctx.home, 'claim-verifier.toml');
    // Codex commands can refresh caches, so dry-run uses filesystem observations only.
    ctx.output(codex ? 'Would preserve existing Codex CLI' : 'Would install Codex CLI');
    ctx.output(findPython(ctx) ? 'Would use existing Python runtime' : 'Would install a verified private Python runtime');
    ctx.output(flags.upgrade ? 'Would upgrade Claim Verifier through Codex' : 'Would preserve an installed Claim Verifier, or install it if absent');
    ctx.output(fs.existsSync(config) ? 'Would preserve existing configuration' : `Would create ${config}`);
    ctx.output('Would prepare private audit storage and diagnostics');
    ctx.output('Would require hook review unless current hooks and audit are already observed');
    return 0;
  }
  privateDir(ctx.home);
  const lock = path.join(ctx.home, 'claim-verifier-setup.lock');
  try { fs.writeFileSync(lock, String(process.pid), {flag: 'wx', mode: 0o600}); }
  catch (error) {
    if (error.code === 'EEXIST') throw new Error(`Another setup is running, or an interrupted setup left ${lock}. Inspect the recorded process before removing the lock.`);
    throw error;
  }
  let status;
  try {
    ctx.codex = ensureCodex(ctx);
    ctx.python = await ensurePython(ctx);
    ctx.output('✓ Python runtime ready');
    const existing = installed(ctx, listing(ctx), selectedPlugin(ctx));
    const plugin = installPlugin(ctx, flags, existing, source);
    const data = configAndStorage(ctx);
    bridge(ctx, 'initialize', plugin, ['--data-root', data]);
    status = bridge(ctx, 'doctor', plugin);
    renderDoctor(status, ctx.output, flags.verbose);
    if (status.exit_code === 2) throw new Error('Required installation validation failed. Run claim-verifier doctor --verbose.');
    ctx.output('✓ Diagnostics available\n✓ Audit commands available: claim-verifier audit latest / audit list');
  } finally { fs.rmSync(lock, {force: true}); }
  await onboarding(ctx, flags, status);
  // Setup succeeded when only human review remains; doctor retains its attention exit code.
  return status.status === 'ATTENTION REQUIRED' ? 1 : 0;
}
