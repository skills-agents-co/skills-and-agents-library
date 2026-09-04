#!/usr/bin/env node
/**
 * check-index-additive.mjs
 *
 * Two committed assertions that used to be hand-run at review time and left
 * no artifact behind (CTO check 7, "verification adequacy", found this twice):
 *
 *   1. Regenerating index.json at the ref it already pins produces the exact
 *      same file. If a future change to build-index.mjs reshapes an existing
 *      key (or the new files/installFolder/skillFilePath keys drift for a
 *      reason other than the repo's own tracked files changing), this fails
 *      instead of silently shipping a changed published interface.
 *   2. README.md's documented install ref (the `ref="..."` line in its fenced
 *      install block) equals the ref index.json's entries are pinned to. A
 *      Spec criterion with no assertion behind it is how the two drifted
 *      apart before (README pinned v1.23.0, index.json pinned v1.27.0).
 *
 * Usage: node scripts/check-index-additive.mjs
 */

import { readFileSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, '..');
const indexPath = join(repoRoot, 'index.json');
const readmePath = join(repoRoot, 'README.md');

let failures = 0;

function fail(msg) {
  console.error('FAIL: ' + msg);
  failures++;
}

const before = readFileSync(indexPath, 'utf8');
const idx = JSON.parse(before);
const firstEntry = Object.values(idx)[0];
const urlMatch = firstEntry && String(firstEntry.skillFileUrl || '').match(
  /^https:\/\/raw\.githubusercontent\.com\/skills-agents-co\/skills-and-agents-library\/([^/]+)\//
);
const indexRef = urlMatch ? urlMatch[1] : null;

if (!indexRef) {
  fail('could not extract a ref from index.json\'s first entry skillFileUrl');
} else {
  console.log(`index.json pins ref: ${indexRef}`);
}

// --- Check 2: README's documented ref matches index.json's ref -------------

const readme = readFileSync(readmePath, 'utf8');
const readmeMatch = readme.match(/ref="([^"]+)"/);
const readmeRef = readmeMatch ? readmeMatch[1] : null;

if (!readmeRef) {
  fail('could not find a ref="..." line in README.md\'s install block');
} else {
  console.log(`README.md pins ref: ${readmeRef}`);
}

if (indexRef && readmeRef && indexRef !== readmeRef) {
  fail(`README.md's install ref (${readmeRef}) does not match index.json's pinned ref (${indexRef})`);
} else if (indexRef && readmeRef) {
  console.log('OK: README.md and index.json agree on the pinned ref.');
}

// --- Check 1: regenerating at the same ref is byte-identical ---------------

if (indexRef) {
  execFileSync('node', [join(__dirname, 'build-index.mjs'), '--tag', indexRef], {
    cwd: repoRoot,
    stdio: 'inherit',
  });
  const after = readFileSync(indexPath, 'utf8');
  if (after !== before) {
    fail('regenerating index.json at its own pinned ref changed the file. A committed key reshaped, or the repo\'s tracked files under some skill folder changed since index.json was last generated. Run `node scripts/build-index.mjs --tag ' + indexRef + '` and commit the result if the change is intentional.');
    // Leave the regenerated file in place so the diff is visible to whoever
    // is debugging this locally; CI's checkout is discarded either way.
  } else {
    console.log('OK: index.json is byte-identical to a fresh regeneration at its own pinned ref.');
    // No functional change, but avoid leaving a spurious mtime-only rewrite.
    writeFileSync(indexPath, before);
  }
}

if (failures > 0) {
  console.error(`\n${failures} check(s) failed.`);
  process.exit(1);
}
console.log('\nAll checks passed.');
process.exit(0);
