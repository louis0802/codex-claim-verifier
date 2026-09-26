import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { Readable, Transform } from 'node:stream';
import { pipeline } from 'node:stream/promises';
import { ROOT, privateDir, checked, which, atomic } from './system.mjs';

const pins = JSON.parse(fs.readFileSync(path.join(ROOT, 'cli/python-downloads.json'), 'utf8'));
export function probePython(executable, ctx) {
  if (!executable) return false;
  const result = ctx.run(executable, ['-I', '-B', '-c', 'import sys,tomllib; assert sys.version_info >= (3,11); print(sys.executable)'], {timeout: 10_000});
  return result.status === 0 && path.isAbsolute(result.stdout.trim()) ? result.stdout.trim() : false;
}
export function findPython(ctx) {
  let saved;
  try { saved = JSON.parse(fs.readFileSync(path.join(ctx.home, 'claim-verifier/runtime.json'), 'utf8')).python; } catch (error) {
    if (error.code !== 'ENOENT') throw new Error('Invalid runtime binding. Inspect claim-verifier/runtime.json before rerunning setup.');
  }
  for (const executable of [saved, which('python3', ctx.env), '/opt/homebrew/bin/python3', '/usr/local/bin/python3',
    path.join(ctx.home, 'claim-verifier/python/python/bin/python3')]) {
    const usable = probePython(executable, ctx);
    if (usable) return usable;
  }
  return null;
}
export async function downloadVerified(pin, target, fetcher = fetch) {
  if (!/^https:\/\/github.com\/astral-sh\/python-build-standalone\/releases\/download\//.test(pin.url) || !/^[a-f0-9]{64}$/.test(pin.sha256)) {
    throw new Error('Invalid pinned Python download.');
  }
  const response = await fetcher(pin.url, {signal: AbortSignal.timeout(120_000)});
  if (!response.ok || !response.body) throw new Error(`Python download failed (HTTP ${response.status}). Retry setup with working network access.`);
  if (response.url && new URL(response.url).protocol !== 'https:') throw new Error('Python download redirected outside HTTPS.');
  const hash = crypto.createHash('sha256');
  let size = 0;
  const meter = new Transform({transform(chunk, encoding, callback) {
    size += chunk.length;
    if (size > 150_000_000) return callback(new Error('Python archive is unexpectedly large.'));
    hash.update(chunk); callback(null, chunk);
  }});
  try {
    await pipeline(Readable.fromWeb(response.body), meter, fs.createWriteStream(target, {mode: 0o600, flags: 'wx'}));
    if (hash.digest('hex') !== pin.sha256) throw new Error('Python archive checksum mismatch. No executable was installed.');
  } catch (error) { fs.rmSync(target, {force: true}); throw error; }
}
export async function ensurePython(ctx) {
  let executable = findPython(ctx);
  const runtimeRoot = path.join(ctx.home, 'claim-verifier');
  if (!executable) {
    const pin = pins[ctx.arch];
    if (!pin) throw new Error(`Unsupported macOS architecture: ${ctx.arch}`);
    ctx.output('Preparing verified Python runtime…');
    privateDir(runtimeRoot);
    const stage = fs.mkdtempSync(path.join(runtimeRoot, '.python-'));
    const archive = path.join(stage, 'python.tar.gz');
    try {
      await (ctx.download || downloadVerified)(pin, archive);
      const members = checked('/usr/bin/tar', ['-tzf', archive], ctx).stdout.split('\n').filter(Boolean);
      if (!members.length || members.some(name => !name.startsWith('python/') || name.split('/').includes('..') || /[\x00-\x1f]/.test(name))) {
        throw new Error('Unsafe Python archive paths.');
      }
      checked('/usr/bin/tar', ['-xzf', archive, '-C', stage], ctx);
      fs.rmSync(archive);
      executable = probePython(path.join(stage, 'python/bin/python3'), ctx);
      if (!executable) throw new Error('Downloaded Python failed its runtime check.');
      const destination = path.join(runtimeRoot, 'python');
      if (fs.existsSync(destination)) throw new Error('Existing managed Python is unusable. Inspect or remove it before rerunning setup.');
      fs.renameSync(stage, destination);
      executable = probePython(path.join(destination, 'python/bin/python3'), ctx);
      if (!executable) throw new Error('Managed Python could not start after installation.');
    } finally { fs.rmSync(stage, {recursive: true, force: true}); }
  }
  privateDir(runtimeRoot);
  const binding = path.join(runtimeRoot, 'runtime.json');
  const content = JSON.stringify({schema_version: 1, python: executable}) + '\n';
  if (!fs.existsSync(binding) || fs.readFileSync(binding, 'utf8') !== content) atomic(binding, content);
  return executable;
}
