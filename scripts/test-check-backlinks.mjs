#!/usr/bin/env node
/**
 * test-check-backlinks.mjs
 *
 * Fixture-driven tests for check-backlinks.mjs. Not wired into CI as the primary
 * gate (the CI lint step runs check-backlinks.mjs directly against the real repo);
 * this is a dev-time regression guard so a later change to the checker cannot
 * silently loosen it — see check-backlinks.mjs's own header for the two rules
 * this pins down.
 *
 * Fixtures live in scripts/test-fixtures/check-backlinks/<case>/ — outside every
 * real skill folder, and the main walk ignores the whole top-level `scripts/`
 * folder explicitly (see check-backlinks.mjs), so these never look like real
 * skills to the checker's normal run.
 *
 * Usage: node scripts/test-check-backlinks.mjs
 */

import { spawnSync } from 'node:child_process';
import { readdirSync, statSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, '..');
const checker = join(__dirname, 'check-backlinks.mjs');
const fixturesRoot = join(__dirname, 'test-fixtures', 'check-backlinks');

function run(fixtureDir) {
  const res = spawnSync('node', [checker, '--fixtures', fixtureDir], { encoding: 'utf8' });
  return { code: res.status, out: (res.stdout || '') + (res.stderr || '') };
}

const cases = [
  // a link to a slug no folder owns -> must fail
  { dir: 'unknown-slug-fail', expect: 'fail', match: 'unknown slug "totally-fake-slug"' },
  // a skill missing its own backlink -> must fail
  { dir: 'missing-own-fail', expect: 'fail', match: 'missing backlink' },
  // a skill with two copies of its own backlink -> must fail
  { dir: 'duplicate-own-fail', expect: 'fail', match: 'found 2 backlinks' },
  // a skill with its own backlink plus a link to a real sibling slug -> must pass
  { dir: 'sibling-link-pass', expect: 'pass' },
  // a skill whose only catalog link names a different real slug -> must fail,
  // with the "missing backlink" message (not a wrong-slug message — this is the
  // case the relaxation was accused of breaking; the own-slug rule still bites).
  { dir: 'wrong-slug-only-fail', expect: 'fail', match: 'missing backlink' },
];

let failures = 0;

for (const c of cases) {
  const { code, out } = run(join(fixturesRoot, c.dir));
  const codeOk = c.expect === 'pass' ? code === 0 : code !== 0;
  const matchOk = !c.match || out.includes(c.match);
  const pass = codeOk && matchOk;
  console.log(`  [${pass ? 'PASS' : 'FAIL'}] ${c.dir} — got exit ${code}, wanted ${c.expect}`);
  if (!pass) {
    failures++;
    console.log('        ' + out.trim().split('\n').join('\n        '));
  }
}

// Count assertion against disk, not a hardcoded number: whatever the checker's
// own walk finds against the real repo must equal the actual SKILL.md count,
// counted the same way the checker's own walkSkillFolders() does (top-level
// <slug>/SKILL.md and nested <slug>/skills/<name>/SKILL.md), by a second,
// separately-written walk here.
function countSkillMdOnDisk(root) {
  const ignore = new Set(['scripts', 'node_modules']);
  let count = 0;
  for (const name of readdirSync(root)) {
    const full = join(root, name);
    if (name.startsWith('.') || ignore.has(name)) continue;
    if (!statSync(full).isDirectory()) continue;

    if (existsSync(join(full, 'SKILL.md'))) count++;

    const nestedSkillsDir = join(full, 'skills');
    if (existsSync(nestedSkillsDir) && statSync(nestedSkillsDir).isDirectory()) {
      for (const sub of readdirSync(nestedSkillsDir)) {
        if (existsSync(join(nestedSkillsDir, sub, 'SKILL.md'))) count++;
      }
    }
  }
  return count;
}

const diskCount = countSkillMdOnDisk(repoRoot);
const real = spawnSync('node', [checker], { encoding: 'utf8', cwd: repoRoot });
const realOut = (real.stdout || '') + (real.stderr || '');
const reportedMatch = realOut.match(/all (\d+) backlinks OK/);
const reportedCount = reportedMatch ? Number(reportedMatch[1]) : -1;
const countOk = real.status === 0 && reportedCount === diskCount;
console.log(`  [${countOk ? 'PASS' : 'FAIL'}] disk-count — checker reported ${reportedCount}, disk has ${diskCount}`);
if (!countOk) {
  failures++;
  console.log('        ' + realOut.trim().split('\n').join('\n        '));
}

console.log('');
if (failures > 0) {
  console.error(`TEST FAILURES: ${failures}`);
  process.exit(1);
}
console.log(`All ${cases.length + 1} test cases passed.`);
process.exit(0);
