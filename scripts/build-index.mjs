#!/usr/bin/env node
/**
 * build-index.mjs
 *
 * Walks every <skill>/SKILL.md and <skill>/agents/*.md, parses YAML frontmatter,
 * and writes index.json keyed by slug with pinned skillFileUrl + githubUrl.
 *
 * Usage:
 *   node scripts/build-index.mjs --tag v1.0.0
 *   node scripts/build-index.mjs --tag main
 */

import { readFileSync, readdirSync, writeFileSync, statSync, existsSync } from 'node:fs';
import { join, relative, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, '..');

function parseArgs(argv) {
  const args = { tag: null };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--tag' && argv[i + 1]) {
      args.tag = argv[i + 1];
      i++;
    }
  }
  return args;
}

function parseFrontmatter(raw) {
  if (!raw.startsWith('---\n')) return null;
  const end = raw.indexOf('\n---', 4);
  if (end === -1) return null;
  const block = raw.slice(4, end);
  const out = {};
  let currentKey = null;
  let currentList = null;
  for (const rawLine of block.split('\n')) {
    const line = rawLine.replace(/\r$/, '');
    if (!line.trim()) continue;
    // list item
    const listMatch = line.match(/^\s+-\s+(.*)$/);
    if (listMatch && currentList) {
      currentList.push(stripQuotes(listMatch[1].trim()));
      continue;
    }
    const kv = line.match(/^([A-Za-z0-9_]+):\s*(.*)$/);
    if (kv) {
      currentKey = kv[1];
      const value = kv[2].trim();
      if (value === '') {
        // could be a list or nested obj — start list bucket
        currentList = [];
        out[currentKey] = currentList;
      } else {
        currentList = null;
        out[currentKey] = stripQuotes(value);
      }
    }
  }
  return out;
}

function stripQuotes(v) {
  if (v.startsWith('"') && v.endsWith('"')) return v.slice(1, -1);
  if (v.startsWith("'") && v.endsWith("'")) return v.slice(1, -1);
  return v;
}

function walkSkillFolders() {
  const entries = [];
  for (const name of readdirSync(repoRoot)) {
    const full = join(repoRoot, name);
    if (!statSync(full).isDirectory()) continue;
    if (name.startsWith('.') || name === 'scripts' || name === 'node_modules') continue;

    // top-level SKILL.md
    const topSkill = join(full, 'SKILL.md');
    if (existsSync(topSkill)) {
      entries.push({ slug: name, file: topSkill, kind: 'skill', nested: false });
    }

    // nested: <skill>/skills/<name>/SKILL.md (financial-pulse layout)
    const nestedSkillsDir = join(full, 'skills');
    if (existsSync(nestedSkillsDir) && statSync(nestedSkillsDir).isDirectory()) {
      for (const sub of readdirSync(nestedSkillsDir)) {
        const subSkill = join(nestedSkillsDir, sub, 'SKILL.md');
        if (existsSync(subSkill)) {
          entries.push({ slug: sub, file: subSkill, kind: 'skill', nested: true, parent: name });
        }
      }
    }

    // agents
    const agentsDir = join(full, 'agents');
    if (existsSync(agentsDir) && statSync(agentsDir).isDirectory()) {
      for (const f of readdirSync(agentsDir)) {
        if (!f.endsWith('.md')) continue;
        entries.push({ slug: f.replace(/\.md$/, ''), file: join(agentsDir, f), kind: 'agent', nested: true, parent: name });
      }
    }
  }
  return entries;
}

function main() {
  const { tag } = parseArgs(process.argv.slice(2));
  if (!tag) {
    console.error('Usage: build-index.mjs --tag <tag-or-branch>');
    process.exit(2);
  }

  const entries = walkSkillFolders();
  const index = {};

  for (const entry of entries) {
    const raw = readFileSync(entry.file, 'utf8');
    const fm = parseFrontmatter(raw);
    if (!fm) {
      console.error(`! No frontmatter in ${entry.file}`);
      continue;
    }
    const relPath = relative(repoRoot, entry.file);
    const dirRel = relative(repoRoot, dirname(entry.file));
    const skillFileUrl = `https://raw.githubusercontent.com/uristocrat/skills/${tag}/${relPath}`;
    const githubUrl = `https://github.com/uristocrat/skills/tree/${tag}/${dirRel}`;
    index[entry.slug] = {
      slug: entry.slug,
      kind: entry.kind,
      name: fm.name || entry.slug,
      description: fm.description || '',
      category: fm.category || '',
      tags: Array.isArray(fm.tags) ? fm.tags : [],
      version: fm.version || '',
      author: fm.author || 'uristocrat',
      skillFileUrl,
      githubUrl,
      path: relPath,
    };
  }

  const outPath = join(repoRoot, 'index.json');
  writeFileSync(outPath, JSON.stringify(index, null, 2) + '\n');
  console.log(`Wrote ${Object.keys(index).length} entries to ${outPath} (tag=${tag})`);
}

main();
