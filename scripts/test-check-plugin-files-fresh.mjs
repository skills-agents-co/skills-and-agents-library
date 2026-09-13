#!/usr/bin/env node
/**
 * test-check-plugin-files-fresh.mjs
 *
 * Fixture-driven tests for check-plugin-files-fresh.mjs. Wired into CI via
 * .github/workflows/lint.yml, right after the real check-plugin-files-fresh.mjs
 * run against the real repo — this is the dev-time regression guard so a
 * later change to the checker cannot silently loosen it.
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

function run(args) {
  const res = spawnSync('node', [checker, ...args], { encoding: 'utf8' });
  return { code: res.status, out: (res.stdout || '') + (res.stderr || ''), error: res.error };
}

function runFixture(fixtureDir) {
  return run(['--fixtures', fixtureDir]);
}

const cases = [
  {
    name: 'clean',
    run: () => runFixture(join(fixturesRoot, 'clean')),
    expect: 'pass',
    match: 'checked 1 generated file(s), all match their source',
  },
  {
    name: 'drifted',
    run: () => runFixture(join(fixturesRoot, 'drifted')),
    expect: 'fail',
    match: 'plugin/requirements.txt: differs from its source src/requirements.txt',
  },
  {
    name: 'missing source',
    run: () => runFixture(join(fixturesRoot, 'missing-source')),
    expect: 'fail',
    match: 'src/requirements.txt: manifest names this as a source but the file does not exist',
  },
  {
    name: 'missing generated parent dir',
    run: () => runFixture(join(fixturesRoot, 'missing-gen-parent-dir')),
    expect: 'fail',
    match: 'plugin/requirements.txt: parent directory does not exist',
  },
  {
    name: 'missing generated file (parent dir exists)',
    run: () => runFixture(join(fixturesRoot, 'missing-gen-file')),
    expect: 'fail',
    match: 'plugin/requirements.txt: is missing',
  },
  {
    name: 'no manifest in fixture dir',
    run: () => runFixture(join(fixturesRoot, 'no-manifest')),
    expect: 'fail',
    match: 'manifest not found at',
  },
  {
    name: '--fixtures with missing operand',
    run: () => run(['--fixtures']),
    expect: 'fail',
    match: '--fixtures requires a directory argument',
  },
  {
    name: 'multi-entry: drift only in non-first item of each entry',
    run: () => runFixture(join(fixturesRoot, 'multi-entry')),
    expect: 'fail',
    match: 'plugin2b/requirements.txt: differs from its source src2/requirements.txt',
  },
];

let failures = 0;

for (const c of cases) {
  const { code, out, error } = c.run();
  // A subprocess that never ran (spawn error, or status null because it was
  // killed/never started) is a failure of the TEST ITSELF, not evidence the
  // checker correctly failed — never let that read as a false pass.
  const subprocessRanOk = !error && code !== null;
  const codeOk = subprocessRanOk && (c.expect === 'pass' ? code === 0 : code !== 0);
  const matchOk = !c.match || out.includes(c.match);
  const pass = codeOk && matchOk;
  console.log(`  [${pass ? 'PASS' : 'FAIL'}] ${c.name} — got exit ${code}${error ? ` (spawn error: ${error.message})` : ''}, wanted ${c.expect}`);
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
