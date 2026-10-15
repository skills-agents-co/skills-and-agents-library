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
 *
 * Usage:
 *   node scripts/check-plugin-icons.mjs [--fixtures <dir>]
 *
 * --fixtures points the check at an alternate repo root (it must hold its own
 * .claude-plugin/marketplace.json), for scripts/test-check-plugin-icons.mjs.
 */

import { readFileSync, statSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

const MIN_PX = 512;
const MAX_PX = 2048;
const MAX_BYTES = 2 * 1024 * 1024;
const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

const args = process.argv.slice(2);
const fixturesIdx = args.indexOf('--fixtures');
const root = fixturesIdx !== -1 ? args[fixturesIdx + 1] : join(__dirname, '..');

const manifest = JSON.parse(readFileSync(join(root, '.claude-plugin', 'marketplace.json'), 'utf8'));
const plugins = manifest.plugins || [];
if (plugins.length === 0) {
  console.error('No plugins found in .claude-plugin/marketplace.json');
  process.exit(2);
}

function problemWith(iconPath) {
  if (!existsSync(iconPath)) return 'missing .claude-plugin/icon.png';
  const buf = readFileSync(iconPath);
  if (buf.length < 24 || !buf.subarray(0, 8).equals(PNG_SIGNATURE) || buf.toString('latin1', 12, 16) !== 'IHDR') {
    return 'icon.png is not a PNG';
  }
  const width = buf.readUInt32BE(16);
  const height = buf.readUInt32BE(20);
  if (width !== height) return `icon is not square (${width}x${height})`;
  if (width < MIN_PX) return `icon is too small (${width}x${height}, minimum ${MIN_PX})`;
  if (width > MAX_PX) return `icon is too large (${width}x${height}, maximum ${MAX_PX})`;
  if (statSync(iconPath).size >= MAX_BYTES) return 'icon is 2 MB or larger';
  return null;
}

let failed = 0;
for (const plugin of plugins) {
  const problem = problemWith(join(root, plugin.source, '.claude-plugin', 'icon.png'));
  if (problem) {
    console.error(`FAIL ${plugin.name}: ${problem}`);
    failed++;
  }
}

if (failed > 0) process.exit(1);
console.log(`checked ${plugins.length} plugins, all have a valid icon`);
