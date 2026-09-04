#!/usr/bin/env node
/**
 * test-install-negative.mjs
 *
 * Fixture-driven proof that scripts/test-install.sh can actually fail. Follows
 * the same convention as test-check-skill-files.mjs and test-check-backlinks.mjs:
 * spawn the real script against doctored index.json fixtures and assert it
 * exits non-zero with a matching message.
 *
 * Without this, nothing proves the manifest check in test-install.sh still
 * bites after a future edit — the exact regression this task exists to
 * prevent (see the Spec: "the exact regression this task exists to catch
 * passes silently if a skill's files array is emptied rather than made
 * wrong").
 *
 * Every fixture is a full copy of the real index.json with exactly one
 * entry (resume-tailor) doctored, so test-install.sh's real network fetch
 * (one pinned tarball) and its ref-extraction logic run unmodified — only
 * the manifest for one entry is wrong.
 *
 * Needs network access (test-install.sh downloads the real tarball once).
 *
 * Usage: node scripts/test-install-negative.mjs
 */

import { spawnSync } from 'node:child_process';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const script = join(__dirname, 'test-install.sh');
const fixturesRoot = join(__dirname, 'test-fixtures', 'test-install');

function run(fixtureFile) {
  const res = spawnSync('bash', [script, fixtureFile], { encoding: 'utf8', timeout: 180_000 });
  return { code: res.status, out: (res.stdout || '') + (res.stderr || '') };
}

const cases = [
  {
    file: 'file-not-in-tarball.json',
    label: 'a files entry naming a file the tarball does not hold',
    match: 'missing or empty file: scripts/does-not-exist.py',
  },
  {
    file: 'empty-files-array.json',
    label: 'an empty files array',
    match: 'files array is empty',
  },
  {
    file: 'absent-files-key.json',
    label: 'an absent files key',
    match: 'index.json entry has no files key',
  },
  {
    file: 'bad-install-folder.json',
    label: 'an installFolder that does not exist',
    match: 'tar extraction failed',
  },
  {
    file: 'skillfilepath-no-frontmatter.json',
    label: 'a skillFilePath whose destination has no frontmatter',
    match: 'skillFilePath destination missing or has no frontmatter',
  },
];

let failures = 0;

for (const c of cases) {
  const { code, out } = run(join(fixturesRoot, c.file));
  const codeOk = code !== 0;
  const matchOk = out.includes(c.match);
  const pass = codeOk && matchOk;
  console.log(`  [${pass ? 'PASS' : 'FAIL'}] ${c.file} (${c.label}) — got exit ${code}, wanted non-zero`);
  if (!pass) {
    failures++;
    console.log('        ' + out.trim().split('\n').join('\n        '));
  }
}

console.log('');
if (failures > 0) {
  console.error(`TEST FAILURES: ${failures}`);
  process.exit(1);
}
console.log(`All ${cases.length} negative cases correctly failed test-install.sh.`);
process.exit(0);
