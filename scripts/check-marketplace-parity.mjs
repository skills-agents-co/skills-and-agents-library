#!/usr/bin/env node
/**
 * check-marketplace-parity.mjs
 *
 * Offline (no network) check that the skills the repo's folder layout would
 * publish and the skills the marketplace plugins install are the same set.
 *
 *   folder side:  the slugs build-index.mjs would publish from the folder
 *                 layout at HEAD, found by the same walk
 *                 (scripts/lib/skill-walk.mjs), run in memory
 *   plugin side:  the union of slugs found by walking every plugin's `source`
 *                 dir in .claude-plugin/marketplace.json at HEAD with that
 *                 same walk
 *
 * This does NOT read the committed index.json. That file is pinned to the last
 * release and regenerated at release time (its `plugins` field reflects that
 * release's marketplace), so between releases it and this check can differ.
 *
 * Files are listed with `git ls-files -z`, the way build-index.mjs lists them,
 * so untracked files never count. A plain filesystem walk is the fallback only
 * when the root is not inside a git work tree.
 *
 * A slug counts once however many plugins cover it (financial-pulse's agents
 * live inside the top-level financial-pulse plugin dir, and several slugs are
 * covered by more than one plugin).
 *
 * Prints three headed lists: index-only (a folder entry no plugin installs),
 * plugin-only (a plugin installs it, no folder entry), and broken plugins (a
 * marketplace entry that cannot install anything: bad name or source, or a
 * source dir with no skills). Exits 1 if any list is non-empty, 0 otherwise.
 * Exits 2 when marketplace.json is missing, unparseable, or has the wrong shape.
 *
 * Usage:
 *   node scripts/check-marketplace-parity.mjs [--fixtures <dir>]
 *
 * --fixtures points the whole check at an alternate repo root (it must hold its
 * own .claude-plugin/marketplace.json), for scripts/test-check-marketplace-parity.mjs.
 * Omit it for the real run.
 */

import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { walkSkillFolders, pluginsBySlug, brokenPlugins, marketplaceShapeError } from './lib/skill-walk.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const USAGE = 'Usage: node scripts/check-marketplace-parity.mjs [--fixtures <dir>]';
const GIT_MAX_BUFFER = 256 * 1024 * 1024;

/** True when `root` is inside a git work tree. */
function insideGitWorkTree(root) {
  try {
    return execFileSync('git', ['-C', root, 'rev-parse', '--is-inside-work-tree'], {
      encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'],
    }).trim() === 'true';
  } catch {
    return false;
  }
}

/** Fallback for non-git roots: one array, no dot-dirs, no node_modules. */
function walkFiles(root) {
  const out = [];
  const stack = [''];
  while (stack.length) {
    const rel = stack.pop();
    for (const d of readdirSync(join(root, rel), { withFileTypes: true })) {
      if (d.name.startsWith('.') && d.isDirectory()) continue;
      if (d.name === 'node_modules') continue;
      const p = rel ? `${rel}/${d.name}` : d.name;
      if (d.isDirectory()) stack.push(p);
      else if (d.isFile()) out.push(p);
    }
  }
  return out;
}

/** Sorted, forward-slash, root-relative file list. */
function listFiles(root) {
  if (insideGitWorkTree(root)) {
    const out = execFileSync('git', ['ls-files', '-z', '--'], {
      cwd: root, encoding: 'utf8', maxBuffer: GIT_MAX_BUFFER,
    });
    return out.split('\0').filter(Boolean).sort();
  }
  return walkFiles(root).sort();
}

function main() {
  const args = process.argv.slice(2);
  const fixturesIdx = args.indexOf('--fixtures');
  let root = join(__dirname, '..');
  if (fixturesIdx !== -1) {
    const value = args[fixturesIdx + 1];
    if (!value || value.startsWith('-')) {
      console.error(USAGE);
      process.exit(2);
    }
    root = value;
  }

  const manifestPath = join(root, '.claude-plugin', 'marketplace.json');
  if (!existsSync(manifestPath)) {
    console.error(`No .claude-plugin/marketplace.json under ${root}.`);
    process.exit(2);
  }
  let marketplace;
  try {
    marketplace = JSON.parse(readFileSync(manifestPath, 'utf8'));
  } catch (err) {
    console.error(`Could not parse ${manifestPath}: ${err.message}`);
    process.exit(2);
  }
  const shapeErr = marketplaceShapeError(marketplace);
  if (shapeErr) {
    console.error(`Could not use ${manifestPath}: ${shapeErr}.`);
    process.exit(2);
  }
  const files = listFiles(root);

  const folderSlugs = new Set(walkSkillFolders(files).map((e) => e.slug));
  const pluginSlugs = new Set(pluginsBySlug(marketplace, files).keys());
  const broken = brokenPlugins(marketplace, files);

  const indexOnly = [...folderSlugs].filter((s) => !pluginSlugs.has(s)).sort();
  const pluginOnly = [...pluginSlugs].filter((s) => !folderSlugs.has(s)).sort();

  console.log(`index-only (${indexOnly.length}): a folder entry no plugin installs`);
  for (const s of indexOnly) console.log(`  ${s}`);
  console.log(`plugin-only (${pluginOnly.length}): a plugin installs it, no folder entry lists it`);
  for (const s of pluginOnly) console.log(`  ${s}`);
  console.log(`broken plugins (${broken.length}): a marketplace entry that installs nothing`);
  for (const b of broken) console.log(`  ${b.name} (source ${b.source}): ${b.reason}`);

  if (indexOnly.length || pluginOnly.length || broken.length) {
    console.error('Marketplace parity check failed.');
    process.exit(1);
  }
  console.log(`marketplace parity OK: ${folderSlugs.size} slugs on both sides`);
}

main();
