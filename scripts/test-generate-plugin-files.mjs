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
import { readFileSync, writeFileSync, mkdirSync, mkdtempSync, rmSync, existsSync, symlinkSync } from 'node:fs';
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

/** Build a scratch root with an arbitrary manifest and no source/generated scaffolding. */
function makeRawRoot(name, manifest) {
  const root = join(scratch, name);
  mkdirSync(root, { recursive: true });
  writeFileSync(join(root, 'plugin-file-map.json'), JSON.stringify(manifest, null, 2) + '\n');
  return root;
}

function run(root) {
  const res = spawnSync('node', [generator, '--fixtures', root], { encoding: 'utf8' });
  return { code: res.status, out: (res.stdout || '') + (res.stderr || ''), error: res.error };
}

function runArgs(args) {
  const res = spawnSync('node', [generator, ...args], { encoding: 'utf8' });
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

// (arg parsing) --fixtures with a missing/flag-shaped operand, and an
// unrecognized flag, are both clean argument errors, not a silent fallback
// to the real repo.
{
  const missingOperand = runArgs(['--fixtures']);
  check('--fixtures with no operand: exits non-zero', missingOperand.code !== 0, missingOperand.out);
  check('--fixtures with no operand: reports the argument error', missingOperand.out.includes('--fixtures requires a directory argument'), missingOperand.out);

  const flagShapedOperand = runArgs(['--fixtures', '--verbose']);
  check('--fixtures with a flag-shaped operand: exits non-zero', flagShapedOperand.code !== 0, flagShapedOperand.out);
  check('--fixtures with a flag-shaped operand: reports the argument error, not "manifest not found at --verbose/..."', flagShapedOperand.out.includes('--fixtures requires a directory argument'), flagShapedOperand.out);

  const unrecognized = runArgs(['--fixture', join(scratch, 'nonexistent')]);
  check('unrecognized flag: exits non-zero', unrecognized.code !== 0, unrecognized.out);
  check('unrecognized flag: reports the unrecognized argument', unrecognized.out.includes('unrecognized argument'), unrecognized.out);
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
  check(
    'already-correct manifest: summary output reports what it did',
    /wrote plugin[\\/]requirements\.txt from src[\\/]requirements\.txt/.test(out) && /generated 1 file\(s\) from 1 canonical source\(s\)/.test(out),
    out,
  );
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

// (c) manifest names a missing source: exits non-zero and writes nothing —
// including leaving alone entries that *would* have succeeded on their own.
// A one-entry manifest can't distinguish "nothing was written" from "there
// was nothing to write"; a two-entry manifest where entry 1 is a valid,
// already-correct pair and entry 2's source is missing actually exercises
// all-or-nothing, by asserting entry 1's generated target is untouched.
{
  const root = join(scratch, 'missing-source');
  mkdirSync(root, { recursive: true });
  writeFileSync(join(root, 'plugin-file-map.json'), JSON.stringify([
    { source: 'src1/requirements.txt', generated: ['plugin1/requirements.txt'] },
    { source: 'src2/requirements.txt', generated: ['plugin2/requirements.txt'] },
  ], null, 2) + '\n');
  mkdirSync(join(root, 'src1'), { recursive: true });
  writeFileSync(join(root, 'src1', 'requirements.txt'), 'a==1.0\n');
  mkdirSync(join(root, 'plugin1'), { recursive: true });
  writeFileSync(join(root, 'plugin1', 'requirements.txt'), 'a==1.0\n');
  // src2/requirements.txt is deliberately never created.

  const before = readFileSync(join(root, 'plugin1', 'requirements.txt'), 'utf8');
  const { code, out, error } = run(root);
  const ranOk = !error && code !== null;
  const entry1After = existsSync(join(root, 'plugin1', 'requirements.txt'))
    ? readFileSync(join(root, 'plugin1', 'requirements.txt'), 'utf8')
    : null;
  const entry2Created = existsSync(join(root, 'plugin2', 'requirements.txt'));

  check('missing source (2nd entry): exits non-zero', ranOk && code !== 0, out);
  check('missing source (2nd entry): reports the missing source', out.includes('src2/requirements.txt'), out);
  check(
    "missing source (2nd entry): entry 1's already-correct generated target was NOT modified",
    entry1After === before,
    `before=${JSON.stringify(before)} after=${JSON.stringify(entry1After)}`,
  );
  check("missing source (2nd entry): entry 2's generated target was NOT created", !entry2Created, 'plugin2/requirements.txt was created');
}

// (d) empty-array manifest: rejected, same as the checker.
{
  const root = makeRawRoot('empty-manifest', []);
  const { code, out, error } = run(root);
  const ranOk = !error && code !== null;
  check('empty manifest: exits non-zero', ranOk && code !== 0, out);
  check('empty manifest: reports the empty-array problem', out.includes('empty array'), out);
}

// (d2) validateManifest shape rules, shared with the checker via
// scripts/lib/plugin-file-map.mjs — one representative case each.
{
  const shapeCases = [
    { name: 'non-array manifest', manifest: {}, match: 'must be a JSON array' },
    { name: 'non-object entry', manifest: [1], match: 'must be an object' },
    { name: 'missing source', manifest: [{ generated: ['x'] }], match: 'non-empty string "source"' },
    { name: 'blank source', manifest: [{ source: '   ', generated: ['x'] }], match: 'non-empty string "source"' },
    { name: 'missing/empty generated', manifest: [{ source: 'a', generated: [] }], match: 'non-empty array "generated"' },
    { name: 'generated[j] non-string', manifest: [{ source: 'a', generated: [1] }], match: 'must be a non-empty string' },
    {
      name: 'duplicate generated path across manifest',
      manifest: [
        { source: 'a', generated: ['x'] },
        { source: 'b', generated: ['x'] },
      ],
      match: 'listed as a "generated" path more than once',
    },
    {
      name: 'path listed as both source and generated',
      manifest: [{ source: 'a', generated: ['a'] }],
      match: 'listed as both a "source" and a "generated" path',
    },
    { name: 'absolute path', manifest: [{ source: '/etc/passwd', generated: ['x'] }], match: 'must be a relative path, not absolute' },
    { name: '../ root escape', manifest: [{ source: '../../etc/passwd', generated: ['x'] }], match: 'path escapes the root' },
  ];

  for (const c of shapeCases) {
    const root = makeRawRoot(`shape-${c.name.replace(/[^a-z0-9]+/gi, '-')}`, c.manifest);
    const { code, out, error } = run(root);
    const ranOk = !error && code !== null;
    check(`validateManifest rule: ${c.name}`, ranOk && code !== 0 && out.includes(c.match), out);
  }
}

// (d3) source that is a directory: clean validation-time failure, not a raw
// EISDIR stack trace.
{
  const root = join(scratch, 'source-is-directory');
  mkdirSync(join(root, 'src'), { recursive: true });
  writeFileSync(
    join(root, 'plugin-file-map.json'),
    JSON.stringify([{ source: 'src', generated: ['plugin/requirements.txt'] }], null, 2) + '\n',
  );
  const { code, out, error } = run(root);
  const ranOk = !error && code !== null;
  check(
    'source is a directory: exits non-zero with a clean FAIL message, not a raw EISDIR stack trace',
    ranOk && code !== 0 && out.includes('FAIL:') && !out.includes('EISDIR') && !out.includes('at Object.'),
    out,
  );
}

// (e) all-or-nothing when the SECOND item's generated parent is blocked by an
// existing file (not just when its source is missing) — the pre-flight must
// catch this before any write happens, not fail mid-loop after entry 1 wrote.
{
  const root = join(scratch, 'blocked-parent');
  mkdirSync(root, { recursive: true });
  writeFileSync(join(root, 'plugin-file-map.json'), JSON.stringify([
    { source: 'src1/requirements.txt', generated: ['plugin1/requirements.txt'] },
    { source: 'src2/requirements.txt', generated: ['blocker/nested/requirements.txt'] },
  ], null, 2) + '\n');
  mkdirSync(join(root, 'src1'), { recursive: true });
  writeFileSync(join(root, 'src1', 'requirements.txt'), 'a==1.0\n');
  mkdirSync(join(root, 'src2'), { recursive: true });
  writeFileSync(join(root, 'src2', 'requirements.txt'), 'b==2.0\n');
  // "blocker" exists as a plain FILE, not a directory, so mkdirSync(recursive)
  // for "blocker/nested" cannot succeed.
  writeFileSync(join(root, 'blocker'), 'i am a file, not a directory');

  const { code, out, error } = run(root);
  const ranOk = !error && code !== null;
  const entry1Written = existsSync(join(root, 'plugin1', 'requirements.txt'));

  check('blocked generated parent: exits non-zero', ranOk && code !== 0, out);
  check('blocked generated parent: reports the blocked path', out.includes('blocker/nested/requirements.txt'), out);
  check('blocked generated parent: entry 1 was NOT written (all-or-nothing)', !entry1Written, 'plugin1/requirements.txt was created');
}

// (f) symlink escape defense: a manifest entry resolving through a symlink
// that points outside the scratch root must be rejected, not silently
// followed or crashed on.
{
  const root = join(scratch, 'symlink-escape');
  const outside = join(scratch, 'symlink-escape-outside');
  mkdirSync(root, { recursive: true });
  mkdirSync(outside, { recursive: true });
  writeFileSync(join(outside, 'secret.txt'), 'should never be touched');
  symlinkSync(outside, join(root, 'link'));
  mkdirSync(join(root, 'src'), { recursive: true });
  writeFileSync(join(root, 'src', 'requirements.txt'), 'a==1.0\n');
  writeFileSync(join(root, 'plugin-file-map.json'), JSON.stringify([
    { source: 'src/requirements.txt', generated: ['link/secret.txt'] },
  ], null, 2) + '\n');

  const before = readFileSync(join(outside, 'secret.txt'), 'utf8');
  const { code, out, error } = run(root);
  const ranOk = !error && code !== null;
  const after = readFileSync(join(outside, 'secret.txt'), 'utf8');

  check('symlink escape: exits non-zero', ranOk && code !== 0, out);
  check('symlink escape: reports the escape, not a raw crash', out.includes('symlinks on disk are resolved'), out);
  check('symlink escape: file outside root was never written', after === before, `before=${JSON.stringify(before)} after=${JSON.stringify(after)}`);
}

console.log('');
if (failures > 0) {
  console.error(`TEST FAILURES: ${failures}`);
  process.exit(1);
}
console.log('All test cases passed.');
process.exit(0);
