#!/usr/bin/env node
/**
 * test-check-skill-files.mjs
 *
 * Fixture-driven tests for check-skill-files.mjs. Not wired into CI (the CI step
 * runs check-skill-files.mjs directly against the real repo); this is a dev-time
 * regression guard so a later change to the checker cannot silently loosen it.
 *
 * Fixtures live in scripts/test-fixtures/check-skill-files/<case>/ — outside every
 * real skill folder, and the main walk ignores the whole top-level `scripts/`
 * folder explicitly (see check-skill-files.mjs), so these never look like real
 * skills to the checker's normal run.
 *
 * Usage: node scripts/test-check-skill-files.mjs
 */

import { spawnSync } from 'node:child_process';
import { readdirSync, statSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, '..');
const checker = join(__dirname, 'check-skill-files.mjs');
const fixturesRoot = join(__dirname, 'test-fixtures', 'check-skill-files');

function run(fixtureDir) {
  const res = spawnSync('node', [checker, '--fixtures', fixtureDir], { encoding: 'utf8' });
  return { code: res.status, out: (res.stdout || '') + (res.stderr || '') };
}

const cases = [
  { dir: 'escapes-root', expect: 'fail', match: 'resolves outside its own skill folder' },
  { dir: 'missing-file', expect: 'fail', match: 'does not exist' },
  { dir: 'orphan-file', expect: 'fail', match: 'is not named by any path' },
  { dir: 'agents-pass', expect: 'pass' },
  { dir: 'indirect-reach-pass', expect: 'pass' },
  { dir: 'plugin-nested-pass', expect: 'pass' },
  { dir: 'sibling-skill-link-pass', expect: 'pass' },
  { dir: 'escaping-skill-md-link-fail', expect: 'fail', match: 'resolves outside its own skill folder' },
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
// own walk finds against the real repo must equal the actual SKILL.md count.
function countSkillMdOnDisk(dir) {
  const ignore = new Set(['.git', 'node_modules', 'examples', 'scripts', 'evals', '.github', '.claude-plugin']);
  let count = 0;
  function walk(d, depth) {
    for (const name of readdirSync(d)) {
      if (depth === 0 && ignore.has(name)) continue;
      const full = join(d, name);
      if (statSync(full).isDirectory()) walk(full, depth + 1);
      else if (name === 'SKILL.md') count++;
    }
  }
  walk(dir, 0);
  return count;
}

const diskCount = countSkillMdOnDisk(repoRoot);
const real = spawnSync('node', [checker], { encoding: 'utf8', cwd: repoRoot });
const realOut = (real.stdout || '') + (real.stderr || '');
const reportedMatch = realOut.match(/checked (\d+) skills/);
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
