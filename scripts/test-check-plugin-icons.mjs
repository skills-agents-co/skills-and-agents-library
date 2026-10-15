#!/usr/bin/env node
/**
 * test-check-plugin-icons.mjs
 *
 * Fixture-driven tests for check-plugin-icons.mjs, so a later change to the
 * checker cannot silently loosen it. Fixtures live in
 * scripts/test-fixtures/plugin-icons/<case>/, each a tiny repo root with its own
 * .claude-plugin/marketplace.json and one plugin named "demo".
 *
 * Usage: node scripts/test-check-plugin-icons.mjs
 */

import { spawnSync } from 'node:child_process';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const checker = join(__dirname, 'check-plugin-icons.mjs');
const fixturesRoot = join(__dirname, 'test-fixtures', 'plugin-icons');

const cases = [
  { dir: 'pass', expect: 'pass' },
  { dir: 'missing-fail', expect: 'fail', match: 'FAIL demo: missing' },
  { dir: 'non-square-fail', expect: 'fail', match: 'FAIL demo: icon is not square' },
  { dir: 'too-small-fail', expect: 'fail', match: 'FAIL demo: icon is too small' },
];

let failures = 0;

for (const c of cases) {
  const res = spawnSync('node', [checker, '--fixtures', join(fixturesRoot, c.dir)], { encoding: 'utf8' });
  const out = (res.stdout || '') + (res.stderr || '');
  const codeOk = c.expect === 'pass' ? res.status === 0 : res.status === 1;
  const matchOk = !c.match || out.includes(c.match);
  const pass = codeOk && matchOk;
  console.log(`  [${pass ? 'PASS' : 'FAIL'}] ${c.dir}: got exit ${res.status}, wanted ${c.expect}`);
  if (!pass) {
    failures++;
    console.log('        ' + out.trim().split('\n').join('\n        '));
  }
}

console.log('');
if (failures > 0) {
  console.error(`${failures} case(s) failed`);
  process.exit(1);
}
console.log(`all ${cases.length} cases passed`);
