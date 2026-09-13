#!/usr/bin/env node
/**
 * test-plugin-file-map.mjs
 *
 * Unit tests for scripts/lib/plugin-file-map.mjs, the module
 * generate-plugin-files.mjs and check-plugin-files-fresh.mjs both rely on to
 * agree about what counts as a valid plugin-file-map.json. Follows the same
 * pattern as test-index-ref.mjs: import the pure functions directly and drive
 * them with a `fail` that throws instead of exiting, rather than spawning a
 * script for every validation rule.
 *
 * The two scripts' own test files (test-generate-plugin-files.mjs and
 * test-check-plugin-files-fresh.mjs) still spawn the real scripts for
 * behavior that only shows up end-to-end (exit codes, write side effects,
 * output text) — this file only covers the shared validation rules.
 *
 * Usage: node scripts/test-plugin-file-map.mjs
 */

import { mkdtempSync, rmSync, mkdirSync, writeFileSync, symlinkSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { resolveInRoot, validateManifest } from './lib/plugin-file-map.mjs';

let failures = 0;
function check(name, fn) {
  const problems = [];
  try {
    fn((cond, msg) => { if (!cond) problems.push(msg); });
  } catch (err) {
    problems.push(`threw unexpectedly: ${err.message}`);
  }
  const pass = problems.length === 0;
  console.log(`  [${pass ? 'PASS' : 'FAIL'}] ${name}`);
  if (!pass) { failures++; for (const p of problems) console.log('        - ' + p); }
}

/** A `fail` that throws instead of exiting, so validation can be tested in-process. */
function throwingFail(message) {
  throw new Error(message);
}

/** Assert that calling `fn` triggers `fail`, and that the message contains `substr`. */
function expectFail(fn, substr) {
  try {
    fn();
  } catch (err) {
    if (substr && !err.message.includes(substr)) {
      return `failed, but message did not include "${substr}": ${err.message}`;
    }
    return null;
  }
  return `expected a failure containing "${substr}", but nothing failed`;
}

const scratch = mkdtempSync(join(tmpdir(), 'test-plugin-file-map-'));
process.on('exit', () => rmSync(scratch, { recursive: true, force: true }));

/** Build a fresh root under scratch/<name>/ with the given files, no manifest validation performed here. */
function makeRoot(name, files = {}) {
  const root = join(scratch, name);
  mkdirSync(root, { recursive: true });
  for (const [rel, contents] of Object.entries(files)) {
    const p = join(root, rel);
    mkdirSync(join(p, '..'), { recursive: true });
    writeFileSync(p, contents);
  }
  return root;
}

// --- resolveInRoot -----------------------------------------------------

check('resolveInRoot accepts a plain relative path and returns the resolved path', (want) => {
  const root = makeRoot('resolve-ok');
  const resolved = resolveInRoot(root, 'a/b.txt', 'label', throwingFail);
  want(resolved === join(root, 'a/b.txt'), `got ${resolved}`);
});

check('resolveInRoot rejects an absolute path', (want) => {
  const root = makeRoot('resolve-abs');
  const err = expectFail(() => resolveInRoot(root, '/etc/passwd', 'label', throwingFail), 'must be a relative path');
  want(err === null, err);
});

check('resolveInRoot rejects a "../" escape', (want) => {
  const root = makeRoot('resolve-escape');
  const err = expectFail(() => resolveInRoot(root, '../../etc/passwd', 'label', throwingFail), 'escapes the root');
  want(err === null, err);
});

check('resolveInRoot rejects a symlinked path segment that escapes root on disk', (want) => {
  const root = makeRoot('resolve-symlink-escape');
  const outside = makeRoot('resolve-symlink-outside');
  writeFileSync(join(outside, 'secret.txt'), 'nope');
  symlinkSync(outside, join(root, 'link'));
  // "link/secret.txt" resolves lexically inside root, but "link" is a symlink
  // pointing outside it — the disk-level check must still catch this.
  const err = expectFail(() => resolveInRoot(root, 'link/secret.txt', 'label', throwingFail), 'once symlinks on disk are resolved');
  want(err === null, err);
});

check('resolveInRoot allows a symlink that stays inside root', (want) => {
  const root = makeRoot('resolve-symlink-ok');
  mkdirSync(join(root, 'real'), { recursive: true });
  writeFileSync(join(root, 'real', 'f.txt'), 'ok');
  symlinkSync(join(root, 'real'), join(root, 'link'));
  const resolved = resolveInRoot(root, 'link/f.txt', 'label', throwingFail);
  want(resolved === join(root, 'link', 'f.txt'), `got ${resolved}`);
});

check('resolveInRoot checks the nearest existing ancestor for a not-yet-existing generated path', (want) => {
  const root = makeRoot('resolve-symlink-future');
  const outside = makeRoot('resolve-symlink-future-outside');
  symlinkSync(outside, join(root, 'link'));
  // "link/new/file.txt" doesn't exist yet, but its ancestor "link" does, and
  // it's a symlink pointing outside root.
  const err = expectFail(() => resolveInRoot(root, 'link/new/file.txt', 'label', throwingFail), 'once symlinks on disk are resolved');
  want(err === null, err);
});

// --- validateManifest ----------------------------------------------------

function validate(root, manifest) {
  return validateManifest(manifest, root, 'manifest.json', throwingFail);
}

check('validateManifest rejects a non-array manifest', (want) => {
  const root = makeRoot('v-non-array');
  const err = expectFail(() => validate(root, { not: 'an array' }), 'must be a JSON array');
  want(err === null, err);
});

check('validateManifest rejects an empty array', (want) => {
  const root = makeRoot('v-empty');
  const err = expectFail(() => validate(root, []), 'empty array');
  want(err === null, err);
});

check('validateManifest rejects a non-object entry', (want) => {
  const root = makeRoot('v-non-object-entry');
  const err = expectFail(() => validate(root, ['not-an-object']), 'must be an object');
  want(err === null, err);
});

check('validateManifest rejects a missing source', (want) => {
  const root = makeRoot('v-missing-source');
  const err = expectFail(() => validate(root, [{ generated: ['g.txt'] }]), 'non-empty string "source"');
  want(err === null, err);
});

check('validateManifest rejects a blank source', (want) => {
  const root = makeRoot('v-blank-source');
  const err = expectFail(() => validate(root, [{ source: '   ', generated: ['g.txt'] }]), 'non-empty string "source"');
  want(err === null, err);
});

check('validateManifest rejects a missing generated array', (want) => {
  const root = makeRoot('v-missing-generated');
  const err = expectFail(() => validate(root, [{ source: 's.txt' }]), 'non-empty array "generated"');
  want(err === null, err);
});

check('validateManifest rejects an empty generated array', (want) => {
  const root = makeRoot('v-empty-generated');
  const err = expectFail(() => validate(root, [{ source: 's.txt', generated: [] }]), 'non-empty array "generated"');
  want(err === null, err);
});

check('validateManifest rejects a non-string generated[j]', (want) => {
  const root = makeRoot('v-non-string-generated');
  const err = expectFail(() => validate(root, [{ source: 's.txt', generated: [42] }]), 'generated[0] must be a non-empty string');
  want(err === null, err);
});

check('validateManifest rejects a duplicate generated path across the manifest', (want) => {
  const root = makeRoot('v-dup-generated', { 's1.txt': 'a', 's2.txt': 'b' });
  const err = expectFail(
    () => validate(root, [
      { source: 's1.txt', generated: ['g.txt'] },
      { source: 's2.txt', generated: ['g.txt'] },
    ]),
    'is listed as a "generated" path more than once',
  );
  want(err === null, err);
});

check('validateManifest rejects a path listed as both source and generated', (want) => {
  const root = makeRoot('v-source-is-generated', { 's.txt': 'a' });
  const err = expectFail(
    () => validate(root, [{ source: 's.txt', generated: ['s.txt'] }]),
    'is listed as both a "source" and a "generated" path',
  );
  want(err === null, err);
});

check('validateManifest rejects an ALIASED path listed as both source and generated (different spelling, same file)', (want) => {
  // "s.txt" and "./s.txt" are the same file on disk. A collision check that
  // compares the raw manifest strings instead of resolved paths lets this
  // through, and the generator then silently overwrites a canonical source.
  const root = makeRoot('v-source-is-generated-aliased', { 's.txt': 'a' });
  const err = expectFail(
    () => validate(root, [{ source: 's.txt', generated: ['./s.txt'] }]),
    'is listed as both a "source" and a "generated" path',
  );
  want(err === null, err);
});

check('validateManifest rejects an ALIASED duplicate generated path (different spelling, same file)', (want) => {
  const root = makeRoot('v-dup-generated-aliased', { 's1.txt': 'a', 's2.txt': 'b' });
  const err = expectFail(
    () => validate(root, [
      { source: 's1.txt', generated: ['sub/g.txt'] },
      { source: 's2.txt', generated: ['./sub/g.txt'] },
    ]),
    'is listed as a "generated" path more than once',
  );
  want(err === null, err);
});

check('validateManifest rejects a generated path that already exists as a symlink', (want) => {
  // Even a symlink pointing at a real file INSIDE the root must be rejected:
  // accepting it (a plain statSync follows the link) would make the write
  // silently land on whatever the link targets, not on "generated" itself.
  const root = makeRoot('v-generated-is-symlink', { 's.txt': 'a', 'real-target.txt': 'canonical' });
  symlinkSync(join(root, 'real-target.txt'), join(root, 'alias-link'));
  const err = expectFail(
    () => validate(root, [{ source: 's.txt', generated: ['alias-link'] }]),
    'already exists as a symlink',
  );
  want(err === null, err);
});

check('validateManifest rejects an absolute path', (want) => {
  const root = makeRoot('v-absolute');
  const err = expectFail(() => validate(root, [{ source: '/etc/passwd', generated: ['g.txt'] }]), 'must be a relative path');
  want(err === null, err);
});

check('validateManifest rejects a "../" root escape', (want) => {
  const root = makeRoot('v-root-escape');
  const err = expectFail(() => validate(root, [{ source: '../../etc/passwd', generated: ['g.txt'] }]), 'escapes the root');
  want(err === null, err);
});

check('validateManifest rejects a source that is a directory, not a file', (want) => {
  const root = makeRoot('v-source-is-dir');
  mkdirSync(join(root, 'a-directory'), { recursive: true });
  const err = expectFail(() => validate(root, [{ source: 'a-directory', generated: ['g.txt'] }]), 'is not a file (is it a directory?)');
  want(err === null, err);
});

check('validateManifest rejects a generated path that is a directory, not a file', (want) => {
  const root = makeRoot('v-generated-is-dir', { 's.txt': 'hello' });
  mkdirSync(join(root, 'a-directory'), { recursive: true });
  const err = expectFail(
    () => validate(root, [{ source: 's.txt', generated: ['a-directory'] }]),
    'already exists and is not a file (is it a directory?)',
  );
  want(err === null, err);
});

check('resolveInRoot rejects a DANGLING symlink whose target does not exist', (want) => {
  const root = makeRoot('resolve-dangling-symlink');
  const outside = makeRoot('resolve-dangling-symlink-outside');
  // Target doesn't exist yet (unlike the earlier "future path" case, where
  // the symlink itself exists and points at a real directory) — this is the
  // gap nearestExistingAncestor's realpath check alone can't see, because
  // existsSync reports a dangling symlink's path as not-existing and walks
  // straight past it.
  symlinkSync(join(outside, 'does-not-exist-yet'), join(root, 'dangling'));
  const err = expectFail(
    () => resolveInRoot(root, 'dangling/file.txt', 'label', throwingFail),
    "passes through a dangling symlink whose target can't be verified",
  );
  want(err === null, err);
});

check('validateManifest accepts a well-formed manifest and returns resolved paths', (want) => {
  const root = makeRoot('v-ok', { 's.txt': 'hello' });
  const normalized = validate(root, [{ source: 's.txt', generated: ['out/g.txt'] }]);
  want(Array.isArray(normalized) && normalized.length === 1, 'did not return a normalized array');
  want(normalized[0].sourcePath === join(root, 's.txt'), `sourcePath was ${normalized[0].sourcePath}`);
  want(normalized[0].generated[0].resolvedPath === join(root, 'out/g.txt'), `resolvedPath was ${normalized[0].generated[0].resolvedPath}`);
});

console.log('');
if (failures > 0) {
  console.error(`TEST FAILURES: ${failures}`);
  process.exit(1);
}
console.log('All plugin-file-map cases behaved as expected.');
process.exit(0);
