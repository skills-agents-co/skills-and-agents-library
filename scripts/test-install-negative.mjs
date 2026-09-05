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
 * prevent ("the exact regression this task exists to catch passes silently if
 * a skill's files array is emptied rather than made wrong").
 *
 * Fixtures are GENERATED here, not committed. They used to be five ~930-line
 * verbatim copies of index.json differing by one line each: 4,600 lines of
 * duplicated data with nothing forcing regeneration when index.json changed,
 * and each one froze the pinned ref, so after a re-pin they would keep
 * passing against a stale tarball. Each fixture below is instead built from
 * the live index.json, trimmed to two entries, with one documented mutation
 * applied. The second entry is an untouched control: every case asserts it
 * still reports OK, so a regression that fails *everything* cannot pass as a
 * successful negative test.
 *
 * Trimming to two entries also bounds CI cost. Ten cases over 45 entries with
 * a download each would be ~450 extractions and 10 codeload fetches per PR;
 * this is 20 extractions and, via TEST_INSTALL_TARBALL, one fetch.
 *
 * Needs network access (one pinned tarball, downloaded once and shared).
 *
 * Usage: node scripts/test-install-negative.mjs
 */

import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { refFromIndex } from './lib/index-ref.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const script = join(__dirname, 'test-install.sh');
const realIndexPath = join(__dirname, '..', 'index.json');

const SUBJECT = 'resume-tailor';   // the entry each case doctors
const CONTROL = 'ads-copilot';     // left alone, must still report OK

const realIndexText = readFileSync(realIndexPath, 'utf8');
const realIndex = JSON.parse(realIndexText);
const ref = refFromIndex(realIndexText);

for (const slug of [SUBJECT, CONTROL]) {
  if (!realIndex[slug]) {
    console.error(`index.json has no "${slug}" entry; this test needs it as its ${slug === SUBJECT ? 'subject' : 'control'}.`);
    process.exit(1);
  }
}

const scratch = mkdtempSync(join(tmpdir(), 'test-install-neg-'));
process.on('exit', () => rmSync(scratch, { recursive: true, force: true }));

/** A two-entry index.json with `mutate` applied to the subject entry. */
function fixture(name, mutate) {
  const idx = JSON.parse(JSON.stringify({
    [CONTROL]: realIndex[CONTROL],
    [SUBJECT]: realIndex[SUBJECT],
  }));
  mutate(idx[SUBJECT], idx);
  const path = join(scratch, `${name}.json`);
  writeFileSync(path, JSON.stringify(idx, null, 2) + '\n');
  return path;
}

// --- One shared tarball for the whole suite ---------------------------------

const tarball = join(scratch, 'repo.tgz');
const url = `https://codeload.github.com/skills-agents-co/skills-and-agents-library/tar.gz/${ref}`;
const dl = spawnSync('curl', ['-fsSL', '--connect-timeout', '10', '--max-time', '120', '-o', tarball, url], {
  encoding: 'utf8', timeout: 180_000,
});
if (dl.status !== 0) {
  console.error(`Could not download the pinned tarball for ${ref}: ${url}`);
  process.exit(1);
}

function run(fixturePath) {
  const res = spawnSync('bash', [script, fixturePath], {
    encoding: 'utf8',
    timeout: 180_000,
    env: { ...process.env, TEST_INSTALL_TARBALL: tarball },
  });
  return { code: res.status, out: (res.stdout || '') + (res.stderr || '') };
}

// --- Cases -------------------------------------------------------------------
//
// `match` is the message the run must contain. `summary` cases also assert the
// run counted exactly one failure out of two entries and that the untouched
// control entry still reported OK, so a break that fails every entry cannot
// masquerade as a passing negative test.

const cases = [
  {
    name: 'file-not-in-tarball',
    label: 'a files entry naming a file the tarball does not hold',
    mutate: (e) => { e.files.push('scripts/does-not-exist.py'); },
    match: 'missing or empty file: scripts/does-not-exist.py',
  },
  {
    name: 'empty-files-array',
    label: 'an empty files array',
    mutate: (e) => { e.files = []; },
    match: 'files array is empty',
  },
  {
    name: 'absent-files-key',
    label: 'an absent files key',
    mutate: (e) => { delete e.files; },
    match: 'index.json entry has no files key',
  },
  {
    name: 'files-not-an-array',
    label: 'a files value that is not an array',
    mutate: (e) => { e.files = 'SKILL.md'; },
    match: 'files is not an array',
  },
  {
    name: 'bad-install-folder',
    label: 'an installFolder that does not exist in the tarball',
    mutate: (e) => { e.installFolder = 'no-such-folder'; },
    match: 'tar extraction failed',
  },
  {
    name: 'missing-install-folder',
    label: 'a missing installFolder key',
    mutate: (e) => { delete e.installFolder; },
    match: 'missing installFolder',
  },
  {
    name: 'missing-skill-file-path',
    label: 'a missing skillFilePath key',
    mutate: (e) => { delete e.skillFilePath; },
    match: 'missing skillFilePath',
  },
  {
    name: 'path-traversal',
    label: 'a files entry that escapes the install folder',
    mutate: (e) => { e.files.push('../../etc/passwd'); },
    match: 'path traversal in manifest: ../../etc/passwd',
  },
  {
    name: 'skillfilepath-no-frontmatter',
    label: 'a skillFilePath pointing at a file with no frontmatter',
    mutate: (e) => {
      const plain = e.files.find((f) => f.endsWith('requirements.txt')) || e.files.find((f) => !f.endsWith('.md'));
      e.skillFilePath = plain;
      e.path = `${e.installFolder}/${plain}`;
    },
    match: 'skillFilePath destination missing or has no frontmatter',
  },
  {
    name: 'unsafe-ref',
    label: 'a skillFileUrl whose ref contains ".."',
    mutate: (e, idx) => {
      for (const entry of Object.values(idx)) {
        entry.skillFileUrl = entry.skillFileUrl.replace(
          /library\/[^/]+\//,
          'library/..%2f../'
        );
      }
    },
    match: 'Refusing to use unsafe ref extracted from index.json',
    wantCode: 2,
    // Aborts before the per-entry loop, so there is no summary line to check.
    noSummary: true,
  },
];

let failures = 0;

for (const c of cases) {
  const path = fixture(c.name, c.mutate);
  const { code, out } = run(path);

  const problems = [];
  if (c.wantCode !== undefined) {
    if (code !== c.wantCode) problems.push(`exit ${code}, wanted ${c.wantCode}`);
  } else if (code === 0) {
    problems.push('exit 0, wanted non-zero');
  }
  if (!out.includes(c.match)) problems.push(`output did not contain ${JSON.stringify(c.match)}`);
  if (!c.noSummary) {
    if (!out.includes('Total: 2, Failures: 1')) {
      problems.push('summary was not "Total: 2, Failures: 1" (the break should hit exactly the doctored entry)');
    }
    if (!new RegExp(`^OK\\s+${CONTROL}$`, 'm').test(out)) {
      problems.push(`the untouched control entry "${CONTROL}" did not still report OK`);
    }
  }

  const pass = problems.length === 0;
  console.log(`  [${pass ? 'PASS' : 'FAIL'}] ${c.name} (${c.label})`);
  if (!pass) {
    failures++;
    for (const p of problems) console.log('        - ' + p);
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
