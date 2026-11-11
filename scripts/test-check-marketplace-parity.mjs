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

function run(dir, rawArgs) {
  const args = rawArgs || ['--fixtures', join(fixturesRoot, dir)];
  const res = spawnSync('node', [checker, ...args], { encoding: 'utf8' });
  return { code: res.status, out: (res.stdout || '') + (res.stderr || '') };
}

const cases = [
  // both sides list the same slug
  { dir: 'clean-pass', expect: 'pass', match: ['index-only (0)', 'plugin-only (0)', 'broken plugins (0)', '1 slugs on both sides'] },
  // beta is in the index and no plugin installs it
  { dir: 'index-only-fail', expect: 'fail', match: ['index-only (1)', '  beta', 'plugin-only (0)'] },
  // gamma is installed by a plugin and the index does not list it
  { dir: 'plugin-only-fail', expect: 'fail', match: ['plugin-only (1)', '  gamma', 'index-only (0)'] },
  // agents inside a top-level plugin dir are covered, and a slug covered by two
  // plugins counts once; nothing is flagged
  { dir: 'financial-pulse-shape-pass', expect: 'pass', match: ['2 slugs on both sides'] },
  // bad sources are listed under the third heading, exit 1, and cover nothing:
  // alpha stays index-only because the nameless plugin pointing at it is skipped
  {
    dir: 'bad-sources',
    expect: 'fail',
    match: [
      'broken plugins (6)', 'dotdot (source ../x)', 'absolute (source /etc)', 'dot (source .)',
      'objsrc (source {"type":"github"})', '(no name) (source ./alpha)', 'empty (source ./empty-src)',
      'index-only (1)', '  alpha', 'plugin-only (0)',
    ],
  },
  // unusable manifests exit 2, not 1, so they cannot pass for drift
  { dir: 'malformed-json', expect: 'exit2', match: ['Could not parse', 'marketplace.json'] },
  { dir: 'malformed-shape', expect: 'exit2', match: ['plugins[0] is not an object', 'marketplace.json'] },
  // a missing manifest also exits 2
  { dir: 'no-manifest', expect: 'exit2', match: ['No .claude-plugin/marketplace.json'], args: ['--fixtures', join(fixturesRoot, 'does-not-exist')] },
  // --fixtures needs a value
  { dir: 'bare-flag', expect: 'exit2', match: ['Usage:'], args: ['--fixtures'] },
  { dir: 'flag-then-flag', expect: 'exit2', match: ['Usage:'], args: ['--fixtures', '--other'] },
];

let failures = 0;
for (const c of cases) {
  const { code, out } = run(c.dir, c.args);
  const codeOk = c.expect === 'pass' ? code === 0 : c.expect === 'exit2' ? code === 2 : code === 1;
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
