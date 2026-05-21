#!/usr/bin/env node
/**
 * build-index.mjs
 *
 * Walks every <skill>/SKILL.md and <skill>/agents/*.md, parses YAML frontmatter,
 * and writes index.json keyed by slug with pinned skillFileUrl + githubUrl.
 *
 * The SKILL.md frontmatter shape is the Claude Code skill plugin format
 * (name, description, optional license). The richer catalog metadata
 * (category, tags, runbook) lives in uristocrat-skills/src/content/, not here.
 *
 * Usage:
 *   node scripts/build-index.mjs --tag v1.0.0
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

/**
 * Minimal YAML frontmatter parser that handles:
 *   key: value
 *   key: "quoted value"
 *   key: >    (folded block scalar — fold subsequent indented lines)
 *   key: |    (literal block scalar — keep newlines)
 *   key:      (list — subsequent "  - item" lines)
 */
function parseFrontmatter(raw) {
  if (!raw.startsWith('---\n')) return null;
  const end = raw.indexOf('\n---', 4);
  if (end === -1) return null;
  const block = raw.slice(4, end);
  const out = {};
  const lines = block.split('\n');
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) { i++; continue; }
    const kv = line.match(/^([A-Za-z0-9_]+):\s*(.*)$/);
    if (!kv) { i++; continue; }
    const key = kv[1];
    const rest = kv[2];

    if (rest === '>' || rest === '|') {
      // block scalar — gather subsequent indented lines
      const joiner = rest === '>' ? ' ' : '\n';
      const collected = [];
      i++;
      while (i < lines.length) {
        const next = lines[i];
        if (next.match(/^[A-Za-z0-9_]+:/)) break;
        if (!next.trim()) { i++; continue; }
        collected.push(next.replace(/^\s+/, ''));
        i++;
      }
      out[key] = collected.join(joiner).trim();
      continue;
    }

    if (rest === '') {
      // could be a list
      const list = [];
      i++;
      while (i < lines.length) {
        const next = lines[i];
        const item = next.match(/^\s+-\s+(.*)$/);
        if (!item) break;
        list.push(stripQuotes(item[1].trim()));
        i++;
      }
      out[key] = list;
      continue;
    }

    out[key] = stripQuotes(rest.trim());
    i++;
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
      entries.push({ slug: name, file: topSkill, kind: 'skill' });
    }

    // nested: <skill>/skills/<name>/SKILL.md (financial-pulse layout)
    const nestedSkillsDir = join(full, 'skills');
    if (existsSync(nestedSkillsDir) && statSync(nestedSkillsDir).isDirectory()) {
      for (const sub of readdirSync(nestedSkillsDir)) {
        const subSkill = join(nestedSkillsDir, sub, 'SKILL.md');
        if (existsSync(subSkill)) {
          entries.push({ slug: sub, file: subSkill, kind: 'skill' });
        }
      }
    }

    // agents
    const agentsDir = join(full, 'agents');
    if (existsSync(agentsDir) && statSync(agentsDir).isDirectory()) {
      for (const f of readdirSync(agentsDir)) {
        if (!f.endsWith('.md')) continue;
        entries.push({ slug: f.replace(/\.md$/, ''), file: join(agentsDir, f), kind: 'agent' });
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
    const fm = parseFrontmatter(raw) || {};
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
  const ordered = Object.keys(index).sort().reduce((o, k) => { o[k] = index[k]; return o; }, {});
  writeFileSync(outPath, JSON.stringify(ordered, null, 2) + '\n');
  console.log(`Wrote ${Object.keys(ordered).length} entries to ${outPath} (tag=${tag})`);
}

main();
