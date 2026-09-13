#!/usr/bin/env node
/**
 * check-plugin-files-fresh.mjs
 *
 * CI-only freshness check for scripts/generate-plugin-files.mjs. It does not
 * regenerate anything on disk — it reads scripts/plugin-file-map.json, computes
 * in memory what each `generated` path's bytes *should* be (the current bytes
 * of its `source`), and compares that against what is actually committed. A
 * committed plugin-nested copy that has drifted from its canonical source fails
 * the build, naming the drifted file, rather than silently going stale again.
 *
 * Usage:
 *   node scripts/check-plugin-files-fresh.mjs [--fixtures <dir>]
 *
 * --fixtures points the whole check at an alternate root with its own
 * scripts/plugin-file-map.json-shaped manifest at `<dir>/plugin-file-map.json`
 * and `source`/`generated` paths resolved relative to `<dir>`, for this
 * script's own tests (scripts/test-fixtures/check-plugin-files-fresh/*). Omit
 * it for the real run against this repo. `--fixtures` requires a directory
 * argument — passing it with a missing or blank operand is an error, not a
 * silent fallback to the real repo.
 *
 * A manifest that parses as a valid, empty array (`[]`) is also an error: an
 * empty manifest checks nothing and silently disables the guard, which is
 * almost certainly not what was intended.
 */

import { readFileSync, existsSync } from 'node:fs';
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

/** One drift-failure message, distinguishing missing from differing. */
function driftMessage(generated, source, reason) {
  return `${generated}: ${reason} its source ${source} (run node scripts/generate-plugin-files.mjs)`;
}

function main() {
  const { root, manifest: manifestPath } = parseArgs(process.argv.slice(2));

  if (!existsSync(manifestPath)) {
    console.error(`FAIL: manifest not found at ${manifestPath}`);
    process.exit(1);
  }

  let manifest;
  try {
    manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  } catch (err) {
    fail(`could not parse ${manifestPath}: ${err.message}`);
  }

  validateManifest(manifest, root, manifestPath);

  if (manifest.length === 0) {
    fail(`manifest ${manifestPath} is an empty array — an empty manifest checks nothing and disables this guard`);
  }

  const failures = [];
  let checked = 0;

  for (const entry of manifest) {
    const sourcePath = join(root, entry.source);

    if (!existsSync(sourcePath)) {
      failures.push(`${entry.source}: manifest names this as a source but the file does not exist (manifest is stale)`);
      continue;
    }
    const sourceBytes = readFileSync(sourcePath);

    for (const generated of entry.generated) {
      const generatedPath = join(root, generated);
      const generatedDir = dirname(generatedPath);

      if (!existsSync(generatedDir)) {
        failures.push(`${generated}: parent directory does not exist (manifest is stale)`);
        continue;
      }

      if (!existsSync(generatedPath)) {
        failures.push(driftMessage(generated, entry.source, 'is missing — it has not been generated from'));
        continue;
      }

      checked++;

      const generatedBytes = readFileSync(generatedPath);
      if (!generatedBytes.equals(sourceBytes)) {
        failures.push(driftMessage(generated, entry.source, 'differs from'));
      }
    }
  }

  if (failures.length > 0) {
    console.error('Plugin-file freshness check FAILED:');
    for (const f of failures) console.error('  - ' + f);
    process.exit(1);
  }

  console.log(`checked ${checked} generated file(s), all match their source`);
}

main();
