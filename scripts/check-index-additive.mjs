#!/usr/bin/env node
/**
 * check-index-additive.mjs
 *
 * Four committed assertions about index.json, the one file this repo publishes
 * as an interface to the catalog site. They used to be hand-run at review time
 * and left no artifact behind (CTO check 7, "verification adequacy", found that
 * twice):
 *
 *   1. Regenerating index.json **at the ref it already pins** produces the
 *      exact same file. Note "at the ref", not "from the working tree": that
 *      distinction is the whole point. index.json describes a release, and
 *      scripts/test-install.sh verifies its `files` manifest against that
 *      release's tarball, so both checks now look at the same snapshot. A PR
 *      that adds a file inside a skill folder therefore does not need to
 *      regenerate index.json, and could not have satisfied both checks if it
 *      did. The cost is real and worth stating precisely: a companion-file
 *      mistake (a deleted or renamed file inside a skill folder) is not caught
 *      in the PR that makes it, and not at "the next release" either — it is
 *      caught by the tag-push build, which runs *after* the tag is already
 *      public. Recovery is a follow-up tag, not an amended one.
 *   2. Every key previously published at the pinned ref is still present, with
 *      the same JSON type, in the committed index.json. This is the actual
 *      additivity check: check 1 compares the file to a regeneration of
 *      itself and so cannot see a key that was removed or reshaped in both.
 *   3. Structural invariants on the new manifest keys: installFolder +
 *      skillFilePath reconstructs path, files is non-empty, contains
 *      skillFilePath, and holds no path escaping the install folder.
 *   4. README.md's documented install ref (the `ref="..."` line in its fenced
 *      codeload block) equals the ref index.json's entries are pinned to. A
 *      Spec criterion with no assertion behind it is how the two drifted apart
 *      before (README pinned v1.23.0, index.json pinned v1.27.0). When you cut
 *      a release you must bump that line in the same commit as the regenerated
 *      index.json; this check is what makes forgetting it a red build.
 *
 * Nothing here writes to the tracked index.json: the regeneration goes to a
 * temp file. A "check" that mutates the tree it is checking leaves a dirty
 * working copy behind on every failure path.
 *
 * Usage: node scripts/check-index-additive.mjs [--index <path>] [--readme <path>]
 * The two overrides exist for scripts/test-check-index-additive.mjs.
 */

import { readFileSync, mkdtempSync, rmSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join, dirname } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { refFromIndex, refFromReadme, isSafeRef, isSafeManifestPath } from './lib/index-ref.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, '..');

function parseArgs(argv) {
  const args = { index: join(repoRoot, 'index.json'), readme: join(repoRoot, 'README.md') };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--index' && argv[i + 1]) { args.index = argv[++i]; }
    else if (argv[i] === '--readme' && argv[i + 1]) { args.readme = argv[++i]; }
  }
  return args;
}

const { index: indexPath, readme: readmePath } = parseArgs(process.argv.slice(2));

let failures = 0;
function fail(msg) {
  console.error('FAIL: ' + msg);
  failures++;
}

const before = readFileSync(indexPath, 'utf8');
const indexRef = refFromIndex(before);

if (!indexRef) {
  fail(
    'could not read a single pinned ref from index.json: either an entry has no parseable ' +
      'skillFileUrl, or the entries do not all pin the same ref (a half-regenerated index)'
  );
} else if (!isSafeRef(indexRef)) {
  fail(`index.json pins a ref that is not git-ref-safe: '${indexRef}'`);
} else {
  console.log(`index.json pins ref: ${indexRef}`);
}

// --- Check 4: README's documented ref matches index.json's ref -------------

const readmeRef = refFromReadme(readFileSync(readmePath, 'utf8'));

if (!readmeRef) {
  fail('could not find a ref="..." line in README.md\'s fenced codeload install block');
} else {
  console.log(`README.md pins ref: ${readmeRef}`);
}

if (indexRef && readmeRef && indexRef !== readmeRef) {
  fail(
    `README.md's install ref (${readmeRef}) does not match index.json's pinned ref (${indexRef}). ` +
      'Cutting a release means bumping both in the same commit.'
  );
} else if (indexRef && readmeRef) {
  console.log('OK: README.md and index.json agree on the pinned ref.');
}

// --- Check 3: structural invariants on the manifest keys -------------------

let parsed = null;
try {
  parsed = JSON.parse(before);
} catch (err) {
  fail(`index.json is not valid JSON: ${err.message}`);
}

if (parsed) {
  let structural = 0;
  for (const [slug, v] of Object.entries(parsed)) {
    const bad = (msg) => { fail(`${slug}: ${msg}`); structural++; };
    if (typeof v.installFolder !== 'string' || !v.installFolder) { bad('missing installFolder'); continue; }
    if (typeof v.skillFilePath !== 'string' || !v.skillFilePath) { bad('missing skillFilePath'); continue; }
    if (!Array.isArray(v.files) || v.files.length === 0) { bad('files is missing, not an array, or empty'); continue; }
    if (`${v.installFolder}/${v.skillFilePath}` !== v.path) {
      bad(`installFolder + skillFilePath ("${v.installFolder}/${v.skillFilePath}") does not reconstruct path ("${v.path}")`);
      continue;
    }
    if (!v.files.includes(v.skillFilePath)) { bad(`files does not list its own skillFilePath (${v.skillFilePath})`); continue; }
    const escaping = [slug, v.installFolder, v.skillFilePath, ...v.files].find((p) => !isSafeManifestPath(p));
    if (escaping !== undefined) { bad(`manifest path escapes the install folder: ${escaping}`); continue; }
  }
  if (structural === 0) {
    console.log(`OK: all ${Object.keys(parsed).length} entries satisfy the manifest invariants.`);
  }
}

// --- Check 2: nothing previously published was removed or reshaped ---------

if (indexRef && isSafeRef(indexRef) && parsed) {
  let publishedRaw = null;
  try {
    publishedRaw = execFileSync('git', ['show', `${indexRef}:index.json`], {
      cwd: repoRoot, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024,
    });
  } catch (err) {
    // Not a skip. This is the one check that can catch a key being removed or
    // reshaped, so a clone that cannot reach the pinned ref cannot run it —
    // and a check that silently goes dark is worse than no check, because the
    // build stays green and nobody learns the difference.
    fail(
      `${indexRef}:index.json is not available in this clone, so the published-shape check ` +
        `could not run. Run \`git fetch --tags\` (or \`git fetch --unshallow\`) and try again. ` +
        `(${err.message.trim().split('\n')[0]})`
    );
  }
  let published = null;
  if (publishedRaw) {
    try {
      published = JSON.parse(publishedRaw);
    } catch (err) {
      fail(`index.json published at ${indexRef} is not valid JSON: ${err.message}`);
    }
  }
  if (published) {
    let removed = 0;
    for (const [slug, oldEntry] of Object.entries(published)) {
      const nowEntry = parsed[slug];
      if (!nowEntry) { fail(`entry "${slug}" was published at ${indexRef} and is gone from index.json`); removed++; continue; }
      for (const key of Object.keys(oldEntry)) {
        if (!(key in nowEntry)) {
          fail(`entry "${slug}" lost the published key "${key}"`);
          removed++;
        } else if (Array.isArray(oldEntry[key]) !== Array.isArray(nowEntry[key]) || typeof oldEntry[key] !== typeof nowEntry[key]) {
          fail(`entry "${slug}" key "${key}" changed JSON type since ${indexRef}`);
          removed++;
        }
      }
    }
    if (removed === 0) {
      console.log(`OK: every key published at ${indexRef} is still present with the same type.`);
    }
  }
}

// --- Check 1: regenerating at the pinned ref is byte-identical -------------

if (indexRef && isSafeRef(indexRef)) {
  const scratch = mkdtempSync(join(tmpdir(), 'check-index-'));
  try {
    const regenerated = join(scratch, 'index.json');
    // build-index.mjs exits non-zero on its own hard failures (an unresolvable
    // ref, a traversal path in a manifest). Letting execFileSync throw would
    // surface those as a raw stack trace from this script instead of as one of
    // its own FAIL: lines, so they are routed through fail() like everything
    // else here.
    let regenerated_ok = true;
    try {
      execFileSync('node', [join(__dirname, 'build-index.mjs'), '--tag', indexRef, '--out', regenerated], {
        cwd: repoRoot,
        stdio: 'inherit',
      });
    } catch (err) {
      regenerated_ok = false;
      fail(
        `build-index.mjs failed while regenerating index.json at ${indexRef} ` +
          `(exit ${err.status ?? 'unknown'}). Its own output is above.`
      );
    }
    if (regenerated_ok && readFileSync(regenerated, 'utf8') !== before) {
      fail(
        `regenerating index.json at its pinned ref (${indexRef}) does not reproduce the committed file. ` +
          `Run \`node scripts/build-index.mjs --tag ${indexRef}\` and commit the result if the change is intentional.`
      );
    } else if (regenerated_ok) {
      console.log(`OK: index.json is byte-identical to a fresh regeneration at ${indexRef}.`);
    }
  } finally {
    rmSync(scratch, { recursive: true, force: true });
  }
}

if (failures > 0) {
  console.error(`\n${failures} check(s) failed.`);
  process.exit(1);
}
console.log('\nAll checks passed.');
process.exit(0);
