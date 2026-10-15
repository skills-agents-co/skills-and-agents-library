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
  { dir: 'pass', expect: 'pass', match: 'checked 1 plugins, all have a valid icon' },
  { dir: 'missing-fail', expect: 'fail', match: 'FAIL demo: missing' },
  { dir: 'non-square-fail', expect: 'fail', match: 'FAIL demo: icon is not square' },
  { dir: 'too-small-fail', expect: 'fail', match: 'FAIL demo: icon is too small' },
  { dir: 'too-large-fail', expect: 'fail', match: 'FAIL demo: icon is too large (4096x4096, maximum 2048)' },
  { dir: 'not-png-fail', expect: 'fail', match: 'FAIL demo: icon.png is not a PNG' },
  // An object source must produce a FAIL line, not a crash, and the next plugin is still checked.
  { dir: 'object-source-fail', expect: 'fail', match: 'FAIL remote: source is not a local path', notMatch: ['FAIL demo', 'TypeError', 'at '] },
  { dir: 'icon-dir-fail', expect: 'fail', match: 'FAIL demo: icon.png is not a file' },
  { dir: 'json-icon-fail', expect: 'fail', match: 'FAIL demo: missing assets/missing.png' },
  { dir: 'json-icon-escape-fail', expect: 'fail', match: 'FAIL demo: plugin.json icon is outside the plugin folder (../other/icon.png)' },
  { dir: 'json-icon-absolute-fail', expect: 'fail', match: 'FAIL demo: plugin.json icon is outside the plugin folder (/tmp/icon.png)' },
  { dir: 'json-icon-ext-fail', expect: 'fail', match: 'FAIL demo: icon must be a PNG (./icon.jpg)' },
  { dir: 'json-icon-type-fail', expect: 'fail', match: 'FAIL demo: plugin.json icon is not a path' },
];

// Argument handling: --fixtures needs a value.
const argCases = [
  { name: '--fixtures with no value', args: ['--fixtures'], match: 'Usage:' },
  { name: '--fixtures followed by a flag', args: ['--fixtures', '--other'], match: 'Usage:' },
];

let failures = 0;

for (const c of cases) {
  const res = spawnSync('node', [checker, '--fixtures', join(fixturesRoot, c.dir)], { encoding: 'utf8' });
  const out = (res.stdout || '') + (res.stderr || '');
  const codeOk = c.expect === 'pass' ? res.status === 0 : res.status === 1;
  const matchOk = (!c.match || out.includes(c.match)) && !(c.notMatch || []).some((m) => out.includes(m));
  const pass = codeOk && matchOk;
  console.log(`  [${pass ? 'PASS' : 'FAIL'}] ${c.dir}: got exit ${res.status}, wanted ${c.expect}`);
  if (!pass) {
    failures++;
    console.log('        ' + out.trim().split('\n').join('\n        '));
  }
}

for (const c of argCases) {
  const res = spawnSync('node', [checker, ...c.args], { encoding: 'utf8' });
  const out = (res.stdout || '') + (res.stderr || '');
  const pass = res.status === 2 && out.includes(c.match);
  console.log(`  [${pass ? 'PASS' : 'FAIL'}] ${c.name}: got exit ${res.status}, wanted 2`);
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
console.log(`all ${cases.length + argCases.length} cases passed`);
