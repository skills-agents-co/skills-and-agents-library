#!/usr/bin/env node
/**
 * test-check-marketplace-parity.mjs
 *
 * Fixture-driven tests for check-marketplace-parity.mjs. The CI lint step runs
 * the checker directly against the real repo (warn-only for now); this test is
 * the blocking guard that the checker itself still behaves.
 *
 * Fixtures live in scripts/test-fixtures/check-marketplace-parity/<case>/, each
 * a miniature repo root with its own .claude-plugin/marketplace.json.
 *
 * Usage: node scripts/test-check-marketplace-parity.mjs
 */

import { spawnSync } from 'node:child_process';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const checker = join(__dirname, 'check-marketplace-parity.mjs');
const fixturesRoot = join(__dirname, 'test-fixtures', 'check-marketplace-parity');

function run(dir) {
  const res = spawnSync('node', [checker, '--root', join(fixturesRoot, dir)], { encoding: 'utf8' });
  return { code: res.status, out: (res.stdout || '') + (res.stderr || '') };
}

const cases = [
  // both sides list the same slug
  { dir: 'clean-pass', expect: 'pass' },
  // beta is in the index and no plugin installs it
  { dir: 'index-only-fail', expect: 'fail', match: ['index-only (1)', '  beta', 'plugin-only (0)'] },
  // gamma is installed by a plugin and the index does not list it
  { dir: 'plugin-only-fail', expect: 'fail', match: ['plugin-only (1)', '  gamma', 'index-only (0)'] },
  // agents inside a top-level plugin dir are covered, and a slug covered by two
  // plugins counts once; nothing is flagged
  { dir: 'financial-pulse-shape-pass', expect: 'pass', match: ['2 slugs on both sides'] },
];

let failures = 0;
for (const c of cases) {
  const { code, out } = run(c.dir);
  const codeOk = c.expect === 'pass' ? code === 0 : code === 1;
  const matchOk = (c.match || []).every((m) => out.includes(m));
  const pass = codeOk && matchOk;
  console.log(`  [${pass ? 'PASS' : 'FAIL'}] ${c.dir} — got exit ${code}, wanted ${c.expect}`);
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
console.log(`All ${cases.length} test cases passed.`);
process.exit(0);
