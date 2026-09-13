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
 * Usage: node scripts/generate-plugin-files.mjs
 */

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, '..');
const manifestPath = join(__dirname, 'plugin-file-map.json');

function main() {
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));

  let written = 0;
  for (const entry of manifest) {
    const sourcePath = join(repoRoot, entry.source);
    const sourceBytes = readFileSync(sourcePath);

    for (const generated of entry.generated) {
      const generatedPath = join(repoRoot, generated);
      mkdirSync(dirname(generatedPath), { recursive: true });
      writeFileSync(generatedPath, sourceBytes);
      console.log(`wrote ${generated} from ${entry.source}`);
      written++;
    }
  }

  console.log(`generated ${written} file(s) from ${manifest.length} canonical source(s)`);
}

main();
