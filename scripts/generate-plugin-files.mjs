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
 * to `<dir>`, for this script's own tests
 * (scripts/test-fixtures/generate-plugin-files/* or a scratch directory). Omit
 * it for the real run against this repo.
 *
 * Before writing anything, every `source` path named in the manifest is
 * checked to exist. If any is missing, all of the missing sources are
 * reported and the script exits 1 without writing a single file — a manifest
 * that names a stale source should never result in a partial write followed
 * by a crash.
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { join, dirname, resolve, isAbsolute, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, '..');

function parseArgs(argv) {
  const args = { root: repoRoot, manifest: join(__dirname, 'plugin-file-map.json') };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--fixtures') {
      const operand = argv[i + 1];
      if (!operand || !operand.trim()) {
        console.error('FAIL: --fixtures requires a directory argument');
        process.exit(1);
      }
      args.root = operand;
      args.manifest = join(args.root, 'plugin-file-map.json');
      i++;
    }
  }
  return args;
}

function fail(message) {
  console.error(`FAIL: ${message}`);
  process.exit(1);
}

/** Resolve `relPath` against `root` and abort if it would escape `root`. */
function resolveInRoot(root, relPath, label) {
  const rootResolved = resolve(root);
  if (isAbsolute(relPath)) {
    fail(`${label} "${relPath}" must be a relative path, not absolute`);
  }
  const resolved = resolve(root, relPath);
  if (resolved !== rootResolved && !resolved.startsWith(rootResolved + sep)) {
    fail(`${label} "${relPath}" resolves outside of ${root} (path escapes the root)`);
  }
  return resolved;
}

/**
 * Validate the shape of a parsed plugin-file-map.json manifest and every path
 * it names, aborting the process with a clear message on the first problem
 * found. Returns nothing on success.
 */
function validateManifest(manifest, root, manifestPath) {
  if (!Array.isArray(manifest)) {
    fail(`manifest ${manifestPath} must be a JSON array, got ${typeof manifest}`);
  }

  const allSources = [];
  const allGenerated = [];

  manifest.forEach((entry, i) => {
    if (typeof entry !== 'object' || entry === null || Array.isArray(entry)) {
      fail(`manifest ${manifestPath}: entry ${i} must be an object, got ${JSON.stringify(entry)}`);
    }
    if (typeof entry.source !== 'string' || entry.source.trim() === '') {
      fail(`manifest ${manifestPath}: entry ${i} must have a non-empty string "source", got ${JSON.stringify(entry.source)}`);
    }
    if (!Array.isArray(entry.generated) || entry.generated.length === 0) {
      fail(`manifest ${manifestPath}: entry ${i} (source "${entry.source}") must have a non-empty array "generated"`);
    }
    entry.generated.forEach((g, j) => {
      if (typeof g !== 'string' || g.trim() === '') {
        fail(`manifest ${manifestPath}: entry ${i} (source "${entry.source}") generated[${j}] must be a non-empty string, got ${JSON.stringify(g)}`);
      }
    });

    resolveInRoot(root, entry.source, `manifest ${manifestPath}: entry ${i} source`);
    entry.generated.forEach((g) => resolveInRoot(root, g, `manifest ${manifestPath}: entry ${i} (source "${entry.source}") generated`));

    allSources.push(entry.source);
    allGenerated.push(...entry.generated);
  });

  const generatedSeen = new Set();
  for (const g of allGenerated) {
    if (generatedSeen.has(g)) {
      fail(`manifest ${manifestPath}: "${g}" is listed as a "generated" path more than once`);
    }
    generatedSeen.add(g);
  }

  const sourceSet = new Set(allSources);
  for (const g of allGenerated) {
    if (sourceSet.has(g)) {
      fail(`manifest ${manifestPath}: "${g}" is listed as both a "source" and a "generated" path`);
    }
  }
}

function main() {
  const { root, manifest: manifestPath } = parseArgs(process.argv.slice(2));

  let manifest;
  try {
    manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  } catch (err) {
    fail(`could not parse ${manifestPath}: ${err.message}`);
  }

  validateManifest(manifest, root, manifestPath);

  const missingSources = manifest
    .map((entry) => entry.source)
    .filter((source) => !existsSync(join(root, source)));

  if (missingSources.length > 0) {
    console.error('FAIL: manifest names source(s) that do not exist — nothing was written:');
    for (const s of missingSources) console.error('  - ' + s);
    process.exit(1);
  }

  let written = 0;
  for (const entry of manifest) {
    const sourcePath = join(root, entry.source);
    const sourceBytes = readFileSync(sourcePath);

    for (const generated of entry.generated) {
      const generatedPath = join(root, generated);
      mkdirSync(dirname(generatedPath), { recursive: true });
      writeFileSync(generatedPath, sourceBytes);
      console.log(`wrote ${generated} from ${entry.source}`);
      written++;
    }
  }

  console.log(`generated ${written} file(s) from ${manifest.length} canonical source(s)`);
}

main();
