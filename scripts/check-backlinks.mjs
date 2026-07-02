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
 * Exits non-zero and prints the offending file(s) if any backlink is missing,
 * duplicated, or pointing at the wrong slug. Prints "all N backlinks OK" on success.
 *
 * Usage:
 *   node scripts/check-backlinks.mjs
 */

import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, '..');

const BASE = 'https://skillsandagents.co/skills/';

function walkSkillFolders() {
  const entries = [];
  for (const name of readdirSync(repoRoot)) {
    const full = join(repoRoot, name);
    if (!statSync(full).isDirectory()) continue;
    if (name.startsWith('.') || name === 'scripts' || name === 'node_modules') continue;

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
  const entries = walkSkillFolders();
  if (entries.length === 0) {
    console.error('No SKILL.md files found. Did the folder layout change?');
    process.exit(2);
  }

  const failures = [];
  // Any catalog backlink, regardless of slug, so we can flag wrong-slug links too.
  const anyBacklink = /https:\/\/skillsandagents\.co\/skills\/([A-Za-z0-9_-]+)\//g;

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

    // Flag any catalog link whose slug does not match this skill.
    for (const m of matches) {
      if (m[1] !== slug) {
        failures.push(`${file}: found backlink to wrong slug "${m[1]}" (expected "${slug}")`);
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
