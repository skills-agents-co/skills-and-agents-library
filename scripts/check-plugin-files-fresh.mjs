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
 * argument that isn't blank and doesn't look like another flag — passing it
 * with a missing operand is an error, not a silent fallback to the real repo.
 * Any other unrecognized argument is also an error.
 *
 * A manifest that parses as a valid, empty array (`[]`) is also an error: an
 * empty manifest checks nothing and silently disables the guard, which is
 * almost certainly not what was intended.
 */

import { readFileSync, existsSync } from 'node:fs';
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

  let rawManifest;
  try {
    rawManifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  } catch (err) {
    fail(`could not parse ${manifestPath}: ${err.message}`);
  }

  const manifest = validateManifest(rawManifest, root, manifestPath, fail);

  const failures = [];
  let checked = 0;

  for (const entry of manifest) {
    if (!existsSync(entry.sourcePath)) {
      failures.push(`${entry.source}: manifest names this as a source but the file does not exist (manifest is stale)`);
      continue;
    }
    const sourceBytes = readFileSync(entry.sourcePath);

    for (const g of entry.generated) {
      const generatedDir = dirname(g.resolvedPath);

      if (!existsSync(generatedDir)) {
        failures.push(`${g.path}: parent directory does not exist (run node scripts/generate-plugin-files.mjs to create it)`);
        continue;
      }

      if (!existsSync(g.resolvedPath)) {
        failures.push(driftMessage(g.path, entry.source, 'is missing — it has not been generated from'));
        continue;
      }

      checked++;

      const generatedBytes = readFileSync(g.resolvedPath);
      if (!generatedBytes.equals(sourceBytes)) {
        failures.push(driftMessage(g.path, entry.source, 'differs from'));
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
