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
 * it for the real run against this repo.
 */

import { readFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, '..');

function parseArgs(argv) {
  const args = { root: repoRoot, manifest: join(__dirname, 'plugin-file-map.json') };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--fixtures' && argv[i + 1]) {
      args.root = argv[++i];
      args.manifest = join(args.root, 'plugin-file-map.json');
    }
  }
  return args;
}

function main() {
  const { root, manifest: manifestPath } = parseArgs(process.argv.slice(2));

  if (!existsSync(manifestPath)) {
    console.error(`FAIL: manifest not found at ${manifestPath}`);
    process.exit(1);
  }

  const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));

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

      checked++;

      if (!existsSync(generatedPath)) {
        failures.push(`${generated}: drifted from ${entry.source} (run node scripts/generate-plugin-files.mjs)`);
        continue;
      }

      const generatedBytes = readFileSync(generatedPath);
      if (!generatedBytes.equals(sourceBytes)) {
        failures.push(`${generated}: drifted from ${entry.source} (run node scripts/generate-plugin-files.mjs)`);
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
