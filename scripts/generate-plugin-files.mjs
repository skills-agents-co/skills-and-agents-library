#!/usr/bin/env node
/**
 * generate-plugin-files.mjs
 *
 * A skill that ships both as a standalone top-level skill and bundled inside a
 * Claude Code plugin can end up with the same file committed twice — e.g.
 * local-lead-prospector/scripts/requirements.txt and its duplicate
 * plugins/eta-searcher/scripts/requirements.txt. This script keeps exactly one
 * of those copies human-edited: it reads scripts/plugin-file-map.json, and for
 * every { source, generated } pair overwrites each `generated` path with the
 * exact bytes of `source`.
 *
 * This is a human-run, human-committed step, the same convention this repo
 * already uses for scripts/build-index.mjs: run it locally after editing a
 * canonical source, then commit the regenerated copy. CI does not run this
 * script; it runs scripts/check-plugin-files-fresh.mjs to verify nothing was
 * forgotten.
 *
 * Usage:
 *   node scripts/generate-plugin-files.mjs [--fixtures <dir>]
 *
 * --fixtures points the whole run at an alternate root with its own
 * <dir>/plugin-file-map.json and `source`/`generated` paths resolved relative
 * to `<dir>`. This script's own tests (test-generate-plugin-files.mjs) don't
 * use static fixture directories the way check-plugin-files-fresh.mjs's tests
 * do — since this script writes files, each test case builds a fresh scratch
 * root with mkdtempSync and points --fixtures at it. Omit --fixtures for the
 * real run against this repo. `--fixtures` requires a directory argument that
 * isn't blank and doesn't look like another flag — passing it with a missing
 * operand is an error, not a silent fallback to the real repo. Any other
 * unrecognized argument is also an error.
 *
 * Before writing anything, the whole manifest is validated and a pre-flight
 * pass checks that every `source` path exists and every `generated` path's
 * parent directory either already exists or can be created. If any check
 * fails, every problem found is reported and the script exits 1 without
 * writing a single file — a stale or half-set-up manifest should never result
 * in a partial write followed by a crash.
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync, statSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { validateManifest } from './lib/plugin-file-map.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, '..');

function fail(message) {
  console.error(`FAIL: ${message}`);
  process.exit(1);
}

function parseArgs(argv) {
  const args = { root: repoRoot, manifest: join(__dirname, 'plugin-file-map.json') };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--fixtures') {
      const operand = argv[i + 1];
      if (!operand || !operand.trim() || operand.startsWith('--')) {
        fail('--fixtures requires a directory argument');
      }
      args.root = operand;
      args.manifest = join(args.root, 'plugin-file-map.json');
      i++;
    } else {
      fail(`unrecognized argument "${argv[i]}"`);
    }
  }
  return args;
}

/**
 * The nearest existing ancestor of `dir` that would block `mkdirSync(dir,
 * { recursive: true })` — i.e. an existing path segment that is a regular
 * file rather than a directory — or null if nothing blocks it.
 */
function findBlockingAncestor(dir) {
  let cur = dir;
  for (;;) {
    if (existsSync(cur)) {
      return statSync(cur).isDirectory() ? null : cur;
    }
    const parent = dirname(cur);
    if (parent === cur) return null;
    cur = parent;
  }
}

function main() {
  const { root, manifest: manifestPath } = parseArgs(process.argv.slice(2));

  if (!existsSync(manifestPath)) {
    fail(`manifest not found at ${manifestPath}`);
  }

  let rawManifest;
  try {
    rawManifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  } catch (err) {
    fail(`could not parse ${manifestPath}: ${err.message}`);
  }

  const manifest = validateManifest(rawManifest, root, manifestPath, fail);

  // Pre-flight: check everything that could go wrong on either side of a
  // write — a missing source, or a generated path whose parent directory is
  // blocked by an existing file — before a single byte is written anywhere.
  const problems = [];

  for (const entry of manifest) {
    if (!existsSync(entry.sourcePath)) {
      problems.push(`${entry.source}: manifest names this as a source but the file does not exist`);
    }
    for (const g of entry.generated) {
      const blocker = findBlockingAncestor(dirname(g.resolvedPath));
      if (blocker) {
        problems.push(`${g.path}: cannot create its parent directory — "${blocker}" already exists and is not a directory`);
      }
    }
  }

  if (problems.length > 0) {
    console.error('FAIL: manifest cannot be generated — nothing was written:');
    for (const p of problems) console.error('  - ' + p);
    process.exit(1);
  }

  let written = 0;
  try {
    for (const entry of manifest) {
      const sourceBytes = readFileSync(entry.sourcePath);
      for (const g of entry.generated) {
        mkdirSync(dirname(g.resolvedPath), { recursive: true });
        writeFileSync(g.resolvedPath, sourceBytes);
        console.log(`wrote ${g.path} from ${entry.source}`);
        written++;
      }
    }
  } catch (err) {
    fail(`unexpected error while writing plugin files: ${err.message}`);
  }

  console.log(`generated ${written} file(s) from ${manifest.length} canonical source(s)`);
}

main();
