#!/usr/bin/env node
/**
 * check-backlinks.mjs
 *
 * Offline (no network) validation that every SKILL.md body contains exactly one
 * backlink to its own Skills & Agents catalog page:
 *   https://skillsandagents.co/skills/<slug>/
 *
 * Walks the same skill folders as build-index.mjs:
 *   top-level   <slug>/SKILL.md
 *   nested      <slug>/skills/<name>/SKILL.md   (financial-pulse / ads-copilot layout)
 *
 * Two rules are enforced. A skill's body must carry exactly one link to its own
 * slug (missing or duplicated both fail). Any other catalog link in the body must
 * name a slug some skill folder in this repo owns — a link to a slug nothing owns
 * still fails, naming the slug and the file. A link to a real sibling slug is
 * allowed: it reads as an intentional cross-reference (e.g. a platform-specific
 * skill pointing at its platform-agnostic sibling), and this check has no way to
 * tell that apart from a mistaken link — it only rules out slugs that don't exist
 * at all. Prints "all N backlinks OK" on success.
 *
 * Usage:
 *   node scripts/check-backlinks.mjs [--fixtures <dir>]
 *
 * --fixtures points the whole walk at an alternate root, for this script's own
 * tests (scripts/test-fixtures/check-backlinks/*). Omit it for the real run.
 */

import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, '..');

const BASE = 'https://skillsandagents.co/skills/';

function walkSkillFolders(root, ignoreAtTopLevel) {
  const entries = [];
  for (const name of readdirSync(root)) {
    const full = join(root, name);
    if (!statSync(full).isDirectory()) continue;
    if (ignoreAtTopLevel.has(name)) continue;
    if (name.startsWith('.')) continue;

    // top-level SKILL.md
    const topSkill = join(full, 'SKILL.md');
    if (existsSync(topSkill)) {
      entries.push({ slug: name, file: topSkill });
    }

    // nested: <skill>/skills/<name>/SKILL.md
    const nestedSkillsDir = join(full, 'skills');
    if (existsSync(nestedSkillsDir) && statSync(nestedSkillsDir).isDirectory()) {
      for (const sub of readdirSync(nestedSkillsDir)) {
        const subSkill = join(nestedSkillsDir, sub, 'SKILL.md');
        if (existsSync(subSkill)) {
          entries.push({ slug: sub, file: subSkill });
        }
      }
    }
  }
  return entries;
}

function main() {
  const args = process.argv.slice(2);
  const fixturesIdx = args.indexOf('--fixtures');
  const walkRoot = fixturesIdx !== -1 ? args[fixturesIdx + 1] : repoRoot;
  const ignoreSet = fixturesIdx !== -1 ? new Set() : new Set(['scripts', 'node_modules']);

  const entries = walkSkillFolders(walkRoot, ignoreSet);
  if (entries.length === 0) {
    console.error('No SKILL.md files found. Did the folder layout change?');
    process.exit(2);
  }

  const failures = [];
  // Any catalog backlink, regardless of slug, so we can check both rules against it.
  const anyBacklink = /https:\/\/skillsandagents\.co\/skills\/([A-Za-z0-9_-]+)\//g;
  const knownSlugs = new Set(entries.map((e) => e.slug));

  for (const { slug, file } of entries) {
    const raw = readFileSync(file, 'utf8');
    const matches = [...raw.matchAll(anyBacklink)];
    const expected = `${BASE}${slug}/`;
    const correct = matches.filter((m) => m[0] === expected);

    if (correct.length === 0) {
      failures.push(`${file}: missing backlink to ${expected}`);
    } else if (correct.length > 1) {
      failures.push(`${file}: found ${correct.length} backlinks to ${expected} (expected exactly 1)`);
    }

    // Flag any catalog link to a slug that no skill folder in this repo owns.
    // A skill's own slug is always in knownSlugs (it's built from these same
    // entries), so this can never fire on a skill's own correct backlink.
    for (const m of matches) {
      if (!knownSlugs.has(m[1])) {
        failures.push(`${file}: found backlink to unknown slug "${m[1]}" (no skill folder owns it)`);
      }
    }
  }

  if (failures.length > 0) {
    console.error('Backlink check FAILED:');
    for (const f of failures) console.error('  - ' + f);
    process.exit(1);
  }

  console.log(`all ${entries.length} backlinks OK`);
}

main();
