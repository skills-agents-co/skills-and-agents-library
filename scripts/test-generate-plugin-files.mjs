#!/usr/bin/env node
/**
 * test-generate-plugin-files.mjs
 *
 * Fixture-driven tests for generate-plugin-files.mjs. Follows the same
 * spawn-and-assert pattern as test-check-plugin-files-fresh.mjs, but since the
 * generator writes files it needs a scratch directory rather than static
 * fixtures — built with mkdtempSync the way test-check-index-additive.mjs
 * already does, and cleaned up on exit.
 *
 * Wired into CI via .github/workflows/lint.yml, next to
 * test-check-plugin-files-fresh.mjs.
 *
 * Usage: node scripts/test-generate-plugin-files.mjs
 */

import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync, mkdtempSync, rmSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const generator = join(__dirname, 'generate-plugin-files.mjs');

const scratch = mkdtempSync(join(tmpdir(), 'test-generate-plugin-files-'));
process.on('exit', () => rmSync(scratch, { recursive: true, force: true }));

/** Build a fresh scratch root under `scratch/<name>/` and return its path. */
function makeRoot(name, { source, generated, manifest }) {
  const root = join(scratch, name);
  mkdirSync(root, { recursive: true });
  if (source !== undefined) {
    const sourcePath = join(root, 'src', 'requirements.txt');
    mkdirSync(dirname(sourcePath), { recursive: true });
    writeFileSync(sourcePath, source);
  }
  if (generated !== undefined) {
    const generatedPath = join(root, 'plugin', 'requirements.txt');
    mkdirSync(dirname(generatedPath), { recursive: true });
    writeFileSync(generatedPath, generated);
  }
  writeFileSync(
    join(root, 'plugin-file-map.json'),
    JSON.stringify(manifest ?? [{ source: 'src/requirements.txt', generated: ['plugin/requirements.txt'] }], null, 2) + '\n',
  );
  return root;
}

function run(root) {
  const res = spawnSync('node', [generator, '--fixtures', root], { encoding: 'utf8' });
  return { code: res.status, out: (res.stdout || '') + (res.stderr || ''), error: res.error };
}

let failures = 0;

function check(name, condition, detail) {
  console.log(`  [${condition ? 'PASS' : 'FAIL'}] ${name}`);
  if (!condition) {
    failures++;
    if (detail) console.log('        ' + detail);
  }
}

// (a) already-correct generated copy: running produces zero changes.
{
  const root = makeRoot('already-correct', { source: 'a==1.0\n', generated: 'a==1.0\n' });
  const before = readFileSync(join(root, 'plugin', 'requirements.txt'), 'utf8');
  const { code, out, error } = run(root);
  const ranOk = !error && code !== null;
  const after = existsSync(join(root, 'plugin', 'requirements.txt'))
    ? readFileSync(join(root, 'plugin', 'requirements.txt'), 'utf8')
    : null;
  check('already-correct manifest: exits 0', ranOk && code === 0, out);
  check('already-correct manifest: generated copy unchanged', after === before, `before=${JSON.stringify(before)} after=${JSON.stringify(after)}`);
}

// (b) source changed since last generation: generated copy is updated to be
// byte-identical to the new source.
{
  const root = makeRoot('source-changed', { source: 'a==2.0\n', generated: 'a==1.0\n' });
  const { code, out, error } = run(root);
  const ranOk = !error && code !== null;
  const sourceBytes = readFileSync(join(root, 'src', 'requirements.txt'));
  const generatedBytes = existsSync(join(root, 'plugin', 'requirements.txt'))
    ? readFileSync(join(root, 'plugin', 'requirements.txt'))
    : null;
  check('source changed: exits 0', ranOk && code === 0, out);
  check('source changed: generated copy now byte-identical to source', generatedBytes !== null && generatedBytes.equals(sourceBytes), out);
}

// (c) manifest names a missing source: exits non-zero and writes nothing.
{
  const root = makeRoot('missing-source', { generated: 'a==1.0\n' }); // no source file created
  const { code, out, error } = run(root);
  const ranOk = !error && code !== null;
  const generatedStillThere = existsSync(join(root, 'plugin', 'requirements.txt'));
  const generatedBytes = generatedStillThere ? readFileSync(join(root, 'plugin', 'requirements.txt'), 'utf8') : null;
  check('missing source: exits non-zero', ranOk && code !== 0, out);
  check('missing source: reports the missing source', out.includes('src/requirements.txt'), out);
  check('missing source: existing generated file left untouched (nothing written)', generatedBytes === 'a==1.0\n', `generatedBytes=${JSON.stringify(generatedBytes)}`);
}

console.log('');
if (failures > 0) {
  console.error(`TEST FAILURES: ${failures}`);
  process.exit(1);
}
console.log('All test cases passed.');
process.exit(0);
