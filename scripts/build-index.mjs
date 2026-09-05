#!/usr/bin/env node
/**
 * build-index.mjs
 *
 * Walks every <skill>/SKILL.md and <skill>/agents/*.md, parses YAML frontmatter,
 * and writes index.json keyed by slug with pinned skillFileUrl + githubUrl.
 *
 * The SKILL.md frontmatter shape is the Claude Code skill plugin format
 * (name, description, optional license). The richer catalog metadata
 * (category, tags, runbook) lives in the catalog site, not here.
 *
 * --tag names the git ref whose *content* is read, not merely a label stamped
 * into the emitted URLs. `--tag v1.2.3` reads every file as it exists at
 * v1.2.3, so the manifest describes that release's tarball rather than
 * whatever happens to be in your checkout. If the ref is not present in this
 * clone the script fails; pass --worktree to deliberately read the working
 * tree instead (the ref still labels the URLs).
 *
 * Usage:
 *   node scripts/build-index.mjs --tag v1.0.0 [--out <path>] [--worktree]
 */

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { isSafeRef, isSafeManifestPath } from './lib/index-ref.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, '..');
const GIT_MAX_BUFFER = 64 * 1024 * 1024;

function parseArgs(argv) {
  const args = { tag: null, out: null, worktree: false };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--tag' && argv[i + 1]) {
      args.tag = argv[i + 1];
      i++;
    } else if (argv[i] === '--out' && argv[i + 1]) {
      args.out = argv[i + 1];
      i++;
    } else if (argv[i] === '--worktree') {
      args.worktree = true;
    }
  }
  return args;
}

/** True when `ref` names a commit this clone actually has. */
function refResolves(ref) {
  try {
    execFileSync('git', ['rev-parse', '--verify', '--quiet', `${ref}^{commit}`], {
      cwd: repoRoot,
      stdio: 'pipe',
    });
    return true;
  } catch {
    return false;
  }
}

/**
 * Where this run reads the repo's content from.
 *
 * index.json describes a *release*, not somebody's checkout: its skillFileUrl
 * and githubUrl point at a tag, and scripts/test-install.sh verifies the
 * published `files` manifest against that tag's tarball. So when --tag names a
 * ref this clone has, read the tree at that ref. Reading the working tree
 * instead is what made the two CI checks mutually exclusive: a PR adding a
 * file under a skill folder had to regenerate index.json to satisfy the
 * additive check, and the regenerated manifest then named a file the released
 * tarball could not contain.
 *
 * --worktree forces the working-tree read, which is what you want at release
 * time for a tag that exists only on the remote, or in a shallow clone.
 *
 * When --tag names a ref this clone does NOT have, this is a hard failure, not
 * a fallback. An earlier version warned and read the working tree anyway,
 * which silently recreated the deadlock described above with no signal that it
 * had happened — and left the remediation message telling the user to run the
 * exact command that recreated it. Falling back to a different snapshot than
 * the one asked for is the failure mode, so it fails loudly instead. Reading
 * the working tree is still available, but only by asking for it.
 *
 * Either way the listing comes from git, never a filesystem walk: no untracked
 * junk (.DS_Store, __pycache__), no accidentally-published secrets, and no
 * symlink-cycle hazard, all by construction rather than by a deny-list.
 */
function makeSource({ tag, worktree }) {
  const useRef = !worktree;
  if (useRef && !refResolves(tag)) {
    console.error(
      `Ref "${tag}" does not resolve in this clone, so index.json cannot be generated at it.\n` +
        'Run `git fetch --tags` (or `git fetch --unshallow` in a shallow clone) and try again.\n' +
        'Pass --worktree if you deliberately want to generate from the working tree instead.'
    );
    process.exit(1);
  }
  let listOut;
  try {
    listOut = useRef
      ? execFileSync('git', ['ls-tree', '-r', '-z', '--name-only', tag, '--'], {
          cwd: repoRoot, encoding: 'utf8', maxBuffer: GIT_MAX_BUFFER,
        })
      : execFileSync('git', ['ls-files', '-z', '--'], {
          cwd: repoRoot, encoding: 'utf8', maxBuffer: GIT_MAX_BUFFER,
        });
  } catch (err) {
    console.error(`Could not list the repo's tracked files from git: ${err.message}`);
    process.exit(1);
  }
  const files = listOut.split('\0').filter(Boolean).sort();
  return {
    label: useRef ? `git ref ${tag}` : 'working tree',
    files,
    read: (p) =>
      useRef
        ? execFileSync('git', ['show', `${tag}:${p}`], {
            cwd: repoRoot, encoding: 'utf8', maxBuffer: GIT_MAX_BUFFER,
          })
        : readFileSync(join(repoRoot, p), 'utf8'),
  };
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

/**
 * Scan a SKILL.md body for a `## Eval Contract` section and return the semver
 * string declared in its `### Version` subsection, or null when absent/malformed.
 *
 * Tolerant by design:
 *   - no `## Eval Contract` heading            → null
 *   - no `### Version` subsection              → null
 *   - `### Version` present but no valid semver → null
 *   - duplicate `### Version` subsections      → first valid semver, else null
 * Never throws.
 */
function extractEvalContractVersion(body) {
  if (typeof body !== 'string' || !body) return null;
  const lines = body.split('\n');

  // Find the `## Eval Contract` heading (level-2, case-insensitive on the label).
  let start = -1;
  for (let i = 0; i < lines.length; i++) {
    if (/^##\s+Eval Contract\s*$/i.test(lines[i])) { start = i; break; }
  }
  if (start === -1) return null;

  // Bound the section: it ends at the next level-2 (or higher) `##`/`#` heading.
  let end = lines.length;
  for (let i = start + 1; i < lines.length; i++) {
    if (/^#{1,2}\s+\S/.test(lines[i])) { end = i; break; }
  }

  const semverRe = /^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$/;

  // Walk every `### Version` subsection inside the section; return the first
  // valid semver found on a line within that subsection.
  for (let i = start + 1; i < end; i++) {
    if (!/^###\s+Version\s*$/i.test(lines[i])) continue;
    // Scan lines under this subsection until the next `###`/`##`/`#` heading.
    for (let j = i + 1; j < end; j++) {
      if (/^#{1,3}\s+\S/.test(lines[j])) break;
      const candidate = lines[j].trim();
      if (!candidate) continue;
      if (semverRe.test(candidate)) return candidate;
    }
  }
  return null;
}

/** Strip the YAML frontmatter block from a raw SKILL.md, returning the body. */
function stripFrontmatter(raw) {
  if (!raw.startsWith('---\n')) return raw;
  const end = raw.indexOf('\n---', 4);
  if (end === -1) return raw;
  return raw.slice(end + 4);
}

/**
 * Every catalog entry, derived from the source's file listing rather than a
 * directory walk, so a ref-backed run and a working-tree run find the same
 * entries by the same rules. Three shapes, unchanged from the directory walk
 * this replaces:
 *
 *   <skill>/SKILL.md                  -> skill, slug = <skill>
 *   <skill>/skills/<name>/SKILL.md    -> skill, slug = <name>   (nested layout)
 *   <skill>/agents/<name>.md          -> agent, slug = <name>
 */
function walkSkillFolders(sourceFiles) {
  const entries = [];
  for (const path of sourceFiles) {
    const top = path.split('/')[0];
    if (!path.includes('/')) continue;
    if (top.startsWith('.') || top === 'scripts' || top === 'node_modules') continue;

    let m;
    if (path === `${top}/SKILL.md`) {
      entries.push({ slug: top, file: path, kind: 'skill' });
    } else if ((m = path.match(/^[^/]+\/skills\/([^/]+)\/SKILL\.md$/))) {
      entries.push({ slug: m[1], file: path, kind: 'skill' });
    } else if ((m = path.match(/^[^/]+\/agents\/([^/]+)\.md$/))) {
      entries.push({ slug: m[1], file: path, kind: 'agent' });
    }
  }
  return entries;
}

/**
 * Every file under `installFolder`, relative to it, sorted.
 *
 * Computed by string prefix on git's own repo-relative paths. The previous
 * version passed an absolute folder to path.relative() against repo-relative
 * git output, which Node resolves against process.cwd(): running this script
 * from anywhere but the repo root silently wrote "../../../..." traversal
 * paths into every entry's manifest and still exited 0. There is no cwd in
 * this version to get wrong.
 */
function filesUnder(sourceFiles, installFolder) {
  const prefix = installFolder + '/';
  return sourceFiles.filter((p) => p.startsWith(prefix)).map((p) => p.slice(prefix.length)).sort();
}

function main() {
  const { tag, out, worktree } = parseArgs(process.argv.slice(2));
  if (!tag) {
    console.error('Usage: build-index.mjs --tag <tag> [--out <path>] [--worktree]');
    process.exit(2);
  }
  // The tag is interpolated into every published URL and handed to git as a
  // ref, so it is validated before either happens.
  if (!isSafeRef(tag)) {
    console.error(
      `Refusing to use an unsafe ref: "${tag}". A ref must start with a letter or digit, ` +
        'contain only [A-Za-z0-9._/-], and hold no "..".'
    );
    process.exit(2);
  }

  const source = makeSource({ tag, worktree });
  const entries = walkSkillFolders(source.files);
  const index = {};

  for (const entry of entries) {
    const raw = source.read(entry.file);
    const fm = parseFrontmatter(raw) || {};
    const evalContractVersion = extractEvalContractVersion(stripFrontmatter(raw));
    const relPath = entry.file;
    const dirRel = dirname(entry.file);
    const skillFileUrl = `https://raw.githubusercontent.com/skills-agents-co/skills-and-agents-library/${tag}/${relPath}`;
    const githubUrl = `https://github.com/skills-agents-co/skills-and-agents-library/tree/${tag}/${dirRel}`;

    // installFolder is the repo top-level folder this entry ships under, e.g.
    // "ceo-todo" for the "ceo-todo-daily" agent slug. skillFilePath is relPath
    // with that leading segment removed, e.g. "agents/ceo-todo-daily.md". Both
    // are additive, new keys; installFolder replaces the README's old wrong
    // assumption that slug equals folder.
    const installFolder = relPath.split('/')[0];
    const skillFilePath = relPath.slice(installFolder.length + 1);
    const files = filesUnder(source.files, installFolder);

    // slug is checked alongside the paths: consumers interpolate it into a
    // destination directory, so a slug of "." or ".." is as dangerous there as
    // a traversal inside the manifest itself.
    for (const p of [entry.slug, installFolder, skillFilePath, ...files]) {
      if (!isSafeManifestPath(p)) {
        console.error(`Refusing to write a manifest path that escapes its install folder: "${p}" (entry ${entry.slug})`);
        process.exit(1);
      }
    }
    if (files.length === 0) {
      console.error(`Entry ${entry.slug} has an empty files manifest under "${installFolder}"`);
      process.exit(1);
    }

    index[entry.slug] = {
      slug: entry.slug,
      kind: entry.kind,
      name: fm.name || entry.slug,
      description: fm.description || '',
      category: fm.category || '',
      tags: Array.isArray(fm.tags) ? fm.tags : [],
      version: fm.version || '',
      evalContractVersion,
      author: fm.author || 'Skills and Agents Co',
      skillFileUrl,
      githubUrl,
      path: relPath,
      installFolder,
      skillFilePath,
      files,
    };
  }

  const outPath = out ? (out.startsWith('/') ? out : join(process.cwd(), out)) : join(repoRoot, 'index.json');
  mkdirSync(dirname(outPath), { recursive: true });
  const ordered = Object.keys(index).sort().reduce((o, k) => { o[k] = index[k]; return o; }, {});
  writeFileSync(outPath, JSON.stringify(ordered, null, 2) + '\n');
  console.log(`Wrote ${Object.keys(ordered).length} entries to ${outPath} (tag=${tag}, read from ${source.label})`);
}

main();
