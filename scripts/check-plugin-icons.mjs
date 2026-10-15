#!/usr/bin/env node
/**
 * check-plugin-icons.mjs
 *
 * Offline check that every plugin listed in .claude-plugin/marketplace.json ships
 * a valid icon at <source>/.claude-plugin/icon.png. The developer portal locks the
 * icon in the first time a plugin is saved, so a missing or bad icon must fail
 * here, before the plugin ever reaches the portal.
 *
 * Rules: the file exists, has a PNG signature, is square, is 512 to 2048 px per
 * side (read from the IHDR chunk, no dependencies), and is under 2 MB.
 * A .jpg/.jpeg icon named in plugin.json gets only the existence and size checks.
 *
 * Usage:
 *   node scripts/check-plugin-icons.mjs [--fixtures <dir>]
 *
 * --fixtures points the check at an alternate repo root (it must hold its own
 * .claude-plugin/marketplace.json), for scripts/test-check-plugin-icons.mjs.
 */

import { readFileSync, statSync, existsSync, openSync, readSync, closeSync } from 'node:fs';
import { join, dirname, resolve, relative, extname, isAbsolute, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

const MIN_PX = 512;
const MAX_PX = 2048;
// Conservative reading of "2 MB": 2,000,000 bytes (not 2 MiB), so a file the
// portal counts in decimal MB is never let through here.
const MAX_BYTES = 2_000_000;
const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const DEFAULT_ICON = '.claude-plugin/icon.png';

const USAGE = 'Usage: node scripts/check-plugin-icons.mjs [--fixtures <dir>]';

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

const manifest = JSON.parse(readFileSync(join(root, '.claude-plugin', 'marketplace.json'), 'utf8'));
const plugins = manifest.plugins || [];
if (plugins.length === 0) {
  console.error('No plugins found in .claude-plugin/marketplace.json');
  process.exit(2);
}

// Returns the icon path (relative to the plugin folder) or a { problem } object.
function iconRelPath(pluginDir) {
  const manifestPath = join(pluginDir, '.claude-plugin', 'plugin.json');
  if (!existsSync(manifestPath)) return { rel: DEFAULT_ICON };
  const pluginJson = JSON.parse(readFileSync(manifestPath, 'utf8'));
  if (pluginJson.icon === undefined) return { rel: DEFAULT_ICON };
  if (typeof pluginJson.icon !== 'string' || pluginJson.icon === '') {
    return { problem: 'plugin.json icon is not a path' };
  }
  const full = resolve(pluginDir, pluginJson.icon);
  const rel = relative(pluginDir, full);
  if (isAbsolute(pluginJson.icon) || rel === '' || rel === '..' || rel.startsWith('..' + sep) || isAbsolute(rel)) {
    return { problem: `plugin.json icon is outside the plugin folder (${pluginJson.icon})` };
  }
  const ext = extname(full).toLowerCase();
  if (ext !== '.png' && ext !== '.jpg' && ext !== '.jpeg') {
    return { problem: `plugin.json icon must be .png, .jpg or .jpeg (${pluginJson.icon})` };
  }
  return { rel: rel.split(sep).join('/') };
}

function problemWith(pluginDir) {
  const found = iconRelPath(pluginDir);
  if (found.problem) return found.problem;
  const { rel } = found;
  const iconPath = join(pluginDir, rel);
  if (!existsSync(iconPath)) return `missing ${rel}`;
  const st = statSync(iconPath);
  if (!st.isFile()) return 'icon.png is not a file';
  // Check size from stat before reading anything.
  if (st.size >= MAX_BYTES) return 'icon is 2 MB or larger';
  // JPEG: only existence and size are checked here. Parsing JPEG dimensions needs
  // a marker walk, which is not worth carrying for an uncommon format.
  const ext = extname(iconPath).toLowerCase();
  if (ext === '.jpg' || ext === '.jpeg') return null;
  // Read only the 24 header bytes (signature + IHDR length/type + width + height).
  const buf = Buffer.alloc(24);
  const fd = openSync(iconPath, 'r');
  let n;
  try {
    n = readSync(fd, buf, 0, 24, 0);
  } finally {
    closeSync(fd);
  }
  if (n < 24 || !buf.subarray(0, 8).equals(PNG_SIGNATURE) || buf.toString('latin1', 12, 16) !== 'IHDR') {
    return 'icon.png is not a PNG';
  }
  const width = buf.readUInt32BE(16);
  const height = buf.readUInt32BE(20);
  if (width !== height) return `icon is not square (${width}x${height})`;
  if (width < MIN_PX) return `icon is too small (${width}x${height}, minimum ${MIN_PX})`;
  if (width > MAX_PX) return `icon is too large (${width}x${height}, maximum ${MAX_PX})`;
  return null;
}

let failed = 0;
plugins.forEach((plugin, index) => {
  const source = plugin && typeof plugin.source === 'string' ? plugin.source : null;
  const name = (plugin && plugin.name) || source || `entry ${index}`;
  try {
    if (source === null) {
      console.error(`FAIL ${name}: source is not a local path`);
      failed++;
      return;
    }
    const problem = problemWith(join(root, source));
    if (problem) {
      console.error(`FAIL ${name}: ${problem}`);
      failed++;
    }
  } catch (err) {
    console.error(`FAIL ${name}: ${err.message}`);
    failed++;
  }
});

if (failed > 0) process.exit(1);
console.log(`checked ${plugins.length} plugins, all have a valid icon`);
