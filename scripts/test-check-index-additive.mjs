#!/usr/bin/env node
/**
 * test-check-index-additive.mjs
 *
 * Fixture-driven proof that scripts/check-index-additive.mjs can actually
 * fail. Follows the repo's convention for checker tests
 * (test-check-skill-files.mjs, test-check-backlinks.mjs): drive the real
 * script via spawnSync against doctored inputs and assert the exit code and
 * message.
 *
 * The checker shipped without one, which is how a checker quietly becomes
 * decorative: every one of its four assertions was verified by hand once and
 * nothing would notice if a future edit turned one into a no-op.
 *
 * Fixtures are generated from the live index.json and README.md into a temp
 * directory, so they cannot go stale against a re-pin. No network access
 * needed: the checker only reads files and runs git.
 *
 * Usage: node scripts/test-check-index-additive.mjs
 */

import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, '..');
const script = join(__dirname, 'check-index-additive.mjs');
const realIndexPath = join(repoRoot, 'index.json');
const realReadmePath = join(repoRoot, 'README.md');

const realIndexText = readFileSync(realIndexPath, 'utf8');
const realReadmeText = readFileSync(realReadmePath, 'utf8');

const scratch = mkdtempSync(join(tmpdir(), 'test-check-index-'));
process.on('exit', () => rmSync(scratch, { recursive: true, force: true }));

function writeFixture(name, text) {
  const path = join(scratch, name);
  writeFileSync(path, text);
  return path;
}

/** index.json with `mutate` applied to the parsed object. */
function indexFixture(name, mutate) {
  const idx = JSON.parse(realIndexText);
  mutate(idx);
  return writeFixture(name, JSON.stringify(idx, null, 2) + '\n');
}

function run(indexPath, readmePath) {
  const res = spawnSync('node', [script, '--index', indexPath, '--readme', readmePath], {
    encoding: 'utf8', cwd: repoRoot, timeout: 120_000,
  });
  return { code: res.status, out: (res.stdout || '') + (res.stderr || '') };
}

const firstSlug = Object.keys(JSON.parse(realIndexText))[0];

const cases = [
  {
    name: 'clean (positive control)',
    index: () => realIndexPath,
    readme: () => realReadmePath,
    wantCode: 0,
    match: 'All checks passed.',
  },
  {
    name: 'README pins a different ref than index.json',
    index: () => realIndexPath,
    readme: () => writeFixture('readme-wrong-ref.md', realReadmeText.replace(/^(\s*)ref="[^"]+"/m, '$1ref="v0.0.1"')),
    wantCode: 1,
    match: "README.md's install ref (v0.0.1) does not match",
  },
  {
    name: 'README has no ref line in its install block',
    index: () => realIndexPath,
    readme: () => writeFixture('readme-no-ref.md', realReadmeText.replace(/^(\s*)ref="[^"]+".*$/m, '')),
    wantCode: 1,
    match: 'could not find a ref="..." line',
  },
  {
    name: 'index.json was hand-edited away from what the ref regenerates',
    index: () => indexFixture('hand-edited.json', (idx) => { idx[firstSlug].description = 'hand-edited by someone'; }),
    readme: () => realReadmePath,
    wantCode: 1,
    match: 'does not reproduce the committed file',
  },
  {
    name: 'a previously published key was removed',
    index: () => indexFixture('key-removed.json', (idx) => { delete idx[firstSlug].version; }),
    readme: () => realReadmePath,
    wantCode: 1,
    match: `entry "${firstSlug}" lost the published key "version"`,
  },
  {
    name: 'a previously published key changed JSON type',
    index: () => indexFixture('key-retyped.json', (idx) => { idx[firstSlug].tags = 'not-an-array'; }),
    readme: () => realReadmePath,
    wantCode: 1,
    match: `entry "${firstSlug}" key "tags" changed JSON type`,
  },
  {
    name: 'a whole published entry disappeared',
    index: () => indexFixture('entry-removed.json', (idx) => { delete idx[firstSlug]; }),
    readme: () => realReadmePath,
    wantCode: 1,
    match: `entry "${firstSlug}" was published at`,
  },
  {
    name: 'installFolder + skillFilePath no longer reconstructs path',
    index: () => indexFixture('bad-invariant.json', (idx) => { idx[firstSlug].skillFilePath = 'elsewhere/SKILL.md'; }),
    readme: () => realReadmePath,
    wantCode: 1,
    match: 'does not reconstruct path',
  },
  {
    name: 'a manifest path escapes the install folder',
    index: () => indexFixture('traversal.json', (idx) => { idx[firstSlug].files = [...idx[firstSlug].files, '../../etc/passwd']; }),
    readme: () => realReadmePath,
    wantCode: 1,
    match: 'manifest path escapes the install folder',
  },
  {
    name: 'index.json is not valid JSON',
    index: () => writeFixture('not-json.json', '{ this is not json'),
    readme: () => realReadmePath,
    wantCode: 1,
    match: 'index.json is not valid JSON',
  },
  {
    name: 'an entry lost its installFolder',
    index: () => indexFixture('no-install-folder.json', (idx) => { delete idx[firstSlug].installFolder; }),
    readme: () => realReadmePath,
    wantCode: 1,
    match: `${firstSlug}: missing installFolder`,
  },
  {
    name: 'an entry lost its skillFilePath',
    index: () => indexFixture('no-skill-file-path.json', (idx) => { delete idx[firstSlug].skillFilePath; }),
    readme: () => realReadmePath,
    wantCode: 1,
    match: `${firstSlug}: missing skillFilePath`,
  },
  {
    name: 'an entry has an empty files array',
    index: () => indexFixture('empty-files.json', (idx) => { idx[firstSlug].files = []; }),
    readme: () => realReadmePath,
    wantCode: 1,
    match: `${firstSlug}: files is missing, not an array, or empty`,
  },
  {
    name: 'files no longer lists the entry\'s own skill file',
    index: () => indexFixture('files-without-skill-file.json', (idx) => {
      const e = idx[firstSlug];
      e.files = e.files.filter((f) => f !== e.skillFilePath);
    }),
    readme: () => realReadmePath,
    wantCode: 1,
    match: 'files does not list its own skillFilePath',
  },
  {
    name: 'entries disagree about which ref they pin (a half-regenerated index)',
    index: () => indexFixture('mixed-refs.json', (idx) => {
      const other = Object.keys(idx).find((k) => k !== firstSlug);
      idx[other].skillFileUrl = idx[other].skillFileUrl.replace(/library\/[^/]+\//, 'library/v0.0.1/');
    }),
    readme: () => realReadmePath,
    wantCode: 1,
    match: 'could not read a single pinned ref from index.json',
  },
  {
    name: 'index.json pins a ref that is not git-ref-safe',
    index: () => indexFixture('unsafe-ref.json', (idx) => {
      for (const e of Object.values(idx)) {
        e.skillFileUrl = e.skillFileUrl.replace(/library\/[^/]+\//, 'library/..%2f../');
      }
    }),
    readme: () => realReadmePath,
    wantCode: 1,
    match: 'pins a ref that is not git-ref-safe',
  },
];

let failures = 0;

for (const c of cases) {
  const { code, out } = run(c.index(), c.readme());
  const problems = [];
  if (code !== c.wantCode) problems.push(`exit ${code}, wanted ${c.wantCode}`);
  if (!out.includes(c.match)) problems.push(`output did not contain ${JSON.stringify(c.match)}`);
  const pass = problems.length === 0;
  console.log(`  [${pass ? 'PASS' : 'FAIL'}] ${c.name}`);
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
console.log(`All ${cases.length} check-index-additive cases behaved as expected.`);
process.exit(0);
