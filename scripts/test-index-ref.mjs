#!/usr/bin/env node
/**
 * test-index-ref.mjs
 *
 * Unit tests for scripts/lib/index-ref.mjs, the module three scripts and one
 * bash script rely on to agree about which ref this repo pins and what counts
 * as a safe ref or a safe manifest path.
 *
 * It is a pure module with no I/O, so unlike its siblings this test imports the
 * functions directly rather than spawning a script. The CLI arm is still
 * exercised through spawnSync, because scripts/test-install.sh consumes it that
 * way and a broken exit code there would be invisible to a direct import.
 *
 * Usage: node scripts/test-index-ref.mjs
 */

import { spawnSync } from 'node:child_process';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { isSafeRef, isSafeManifestPath, refFromIndex, refFromReadme } from './lib/index-ref.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const cli = join(__dirname, 'lib', 'index-ref.mjs');

let failures = 0;
function check(name, fn) {
  const problems = [];
  try {
    fn((cond, msg) => { if (!cond) problems.push(msg); });
  } catch (err) {
    problems.push(`threw: ${err.message}`);
  }
  const pass = problems.length === 0;
  console.log(`  [${pass ? 'PASS' : 'FAIL'}] ${name}`);
  if (!pass) { failures++; for (const p of problems) console.log('        - ' + p); }
}

function entry(ref) {
  return { skillFileUrl: `https://raw.githubusercontent.com/skills-agents-co/skills-and-agents-library/${ref}/x/SKILL.md` };
}

check('isSafeRef accepts real refs and rejects the dangerous shapes', (want) => {
  for (const good of ['v1.28.0', 'main', 'release/v2', 'abc123def', '1.0.0-rc.1']) {
    want(isSafeRef(good) === true, `rejected a valid ref: ${good}`);
  }
  for (const bad of ['', '-x', '--upload-pack=evil', '../etc', 'a..b', 'v1;rm -rf /', 'has space', null, undefined, 42]) {
    want(isSafeRef(bad) === false, `accepted an unsafe ref: ${JSON.stringify(bad)}`);
  }
});

check('isSafeManifestPath rejects traversal, absolute, and dot segments', (want) => {
  for (const good of ['SKILL.md', 'references/guide.md', '.gitignore', 'a/b/c.py', 'x..y/z.md']) {
    want(isSafeManifestPath(good) === true, `rejected a valid path: ${good}`);
  }
  for (const bad of ['', '.', '..', '/etc/passwd', '../x', 'a/../b', 'a/..', 'a/./b', './a', null, 7]) {
    want(isSafeManifestPath(bad) === false, `accepted an unsafe path: ${JSON.stringify(bad)}`);
  }
});

check('refFromIndex reads the pinned ref when every entry agrees', (want) => {
  const text = JSON.stringify({ a: entry('v1.28.0'), b: entry('v1.28.0'), c: entry('v1.28.0') });
  want(refFromIndex(text) === 'v1.28.0', `got ${refFromIndex(text)}`);
});

check('refFromIndex returns null when the entries disagree', (want) => {
  // A half-regenerated index.json. Reading only the first entry would return
  // v1.28.0 here and hide the fact that the file is internally inconsistent.
  const text = JSON.stringify({ a: entry('v1.28.0'), b: entry('v1.27.0') });
  want(refFromIndex(text) === null, `got ${JSON.stringify(refFromIndex(text))}, wanted null`);
});

check('refFromIndex returns null on malformed, empty, or foreign input', (want) => {
  want(refFromIndex('not json at all') === null, 'accepted invalid JSON');
  want(refFromIndex('{}') === null, 'accepted an empty index');
  want(refFromIndex(JSON.stringify({ a: { skillFileUrl: 'https://example.com/x' } })) === null, 'accepted a foreign URL');
  want(refFromIndex(JSON.stringify({ a: { name: 'no url' } })) === null, 'accepted an entry with no skillFileUrl');
});

check('refFromReadme reads the ref only from the fenced codeload block', (want) => {
  const readme = [
    '```bash', 'ref="v0.0.1"   # an unrelated earlier example', '```', '',
    '```bash', '(', '  skill="x"', '  ref="v1.28.0"',
    '  curl https://codeload.github.com/skills-agents-co/skills-and-agents-library/tar.gz/$ref', ')', '```',
  ].join('\n');
  want(refFromReadme(readme) === 'v1.28.0', `got ${JSON.stringify(refFromReadme(readme))} — it read the wrong block`);
  want(refFromReadme('no fences here') === null, 'found a ref where there is none');
});

check('the CLI arm exits the way test-install.sh depends on', (want) => {
  const run = (...args) => spawnSync('node', [cli, ...args], { encoding: 'utf8' });
  want(run('safe-ref', 'v1.28.0').status === 0, 'safe-ref rejected a valid ref');
  want(run('safe-ref', '-x').status === 1, 'safe-ref accepted an option-shaped ref');
  want(run('safe-ref', '').status === 1, 'safe-ref accepted an empty ref');
  want(run('bogus-mode', 'x').status === 2, 'an unknown mode did not exit 2');
  want(run().status === 2, 'a missing mode did not exit 2');
});

console.log('');
if (failures > 0) {
  console.error(`TEST FAILURES: ${failures}`);
  process.exit(1);
}
console.log('All index-ref cases behaved as expected.');
process.exit(0);
