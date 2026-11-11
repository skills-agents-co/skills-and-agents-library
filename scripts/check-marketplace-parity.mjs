#!/usr/bin/env node
/**
 * check-marketplace-parity.mjs
 *
 * Offline (no network) check that the skills index and the plugin marketplace
 * list the same slugs.
 *
 *   index side:   the slugs build-index.mjs would publish, found by the same
 *                 folder walk (scripts/lib/skill-walk.mjs), run in memory
 *   plugin side:  the union of slugs found by walking every plugin's `source`
 *                 dir in .claude-plugin/marketplace.json with that same walk
 *
 * A slug counts once however many plugins cover it (financial-pulse's agents
 * live inside the top-level financial-pulse plugin dir, and several slugs are
 * covered by more than one plugin).
 *
 * Prints two headed lists, index-only (no plugin installs it) and plugin-only
 * (a plugin installs it, the index does not list it). Exits 1 if either is
 * non-empty, 0 otherwise.
 *
 * Usage:
 *   node scripts/check-marketplace-parity.mjs [--root <dir>]
 *
 * --root points the whole check at an alternate repo root, for this script's
 * own tests (scripts/test-fixtures/check-marketplace-parity/*). Omit it for
 * the real run.
 */

import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { walkSkillFolders, pluginsBySlug } from './lib/skill-walk.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));

/** Sorted, forward-slash, root-relative listing of every file, skipping .git and node_modules. */
function listFiles(root, rel = '') {
  const out = [];
  for (const d of readdirSync(join(root, rel), { withFileTypes: true })) {
    if (d.name === '.git' || d.name === 'node_modules') continue;
    const p = rel ? `${rel}/${d.name}` : d.name;
    if (d.isDirectory()) out.push(...listFiles(root, p));
    else if (d.isFile()) out.push(p);
  }
  return out.sort();
}

function main() {
  const args = process.argv.slice(2);
  const rootIdx = args.indexOf('--root');
  const root = rootIdx !== -1 ? args[rootIdx + 1] : join(__dirname, '..');

  const manifestPath = join(root, '.claude-plugin', 'marketplace.json');
  if (!existsSync(manifestPath)) {
    console.error(`No .claude-plugin/marketplace.json under ${root}.`);
    process.exit(2);
  }
  const marketplace = JSON.parse(readFileSync(manifestPath, 'utf8'));
  const files = listFiles(root);

  const indexSlugs = new Set(walkSkillFolders(files).map((e) => e.slug));
  const pluginSlugs = new Set(pluginsBySlug(marketplace, files).keys());

  const indexOnly = [...indexSlugs].filter((s) => !pluginSlugs.has(s)).sort();
  const pluginOnly = [...pluginSlugs].filter((s) => !indexSlugs.has(s)).sort();

  console.log(`index-only (${indexOnly.length}): in the index, no plugin installs it`);
  for (const s of indexOnly) console.log(`  ${s}`);
  console.log(`plugin-only (${pluginOnly.length}): a plugin installs it, the index does not list it`);
  for (const s of pluginOnly) console.log(`  ${s}`);

  if (indexOnly.length || pluginOnly.length) {
    console.error('Marketplace parity check failed.');
    process.exit(1);
  }
  console.log(`marketplace parity OK: ${indexSlugs.size} slugs on both sides`);
}

main();
