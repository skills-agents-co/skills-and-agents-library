#!/usr/bin/env node
/**
 * test-check-plugin-files-fresh.mjs
 *
 * Fixture-driven tests for check-plugin-files-fresh.mjs. Not wired into CI as
 * the source of truth for the real repo (the CI step runs
 * check-plugin-files-fresh.mjs directly against the real repo); this is a
 * dev-time regression guard so a later change to the checker cannot silently
 * loosen it.
 *
 * Fixtures live in scripts/test-fixtures/check-plugin-files-fresh/<case>/, each
 * with its own small plugin-file-map.json and matching source/generated files.
 *
 * Usage: node scripts/test-check-plugin-files-fresh.mjs
 */

import { spawnSync } from 'node:child_process';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const checker = join(__dirname, 'check-plugin-files-fresh.mjs');
const fixturesRoot = join(__dirname, 'test-fixtures', 'check-plugin-files-fresh');

function run(fixtureDir) {
  const res = spawnSync('node', [checker, '--fixtures', fixtureDir], { encoding: 'utf8' });
  return { code: res.status, out: (res.stdout || '') + (res.stderr || '') };
}

const cases = [
  { dir: 'clean', expect: 'pass', match: 'checked 1 generated file(s), all match their source' },
  { dir: 'drifted', expect: 'fail', match: 'plugin/requirements.txt: drifted from src/requirements.txt' },
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

console.log('');
if (failures > 0) {
  console.error(`TEST FAILURES: ${failures}`);
  process.exit(1);
}
console.log(`All ${cases.length} test cases passed.`);
process.exit(0);
