#!/usr/bin/env node
/**
 * check-skill-files.mjs
 *
 * Offline (no network) validation that every skill in the library resolves every
 * file it names, using only files inside its own skill folder.
 *
 * "Its own skill folder" is the skill's resolution root, which depends on layout:
 *   flat            <slug>/SKILL.md                          root = <slug>/
 *   nested          <slug>/skills/<name>/SKILL.md             root = <slug>/
 *   plugin-nested   plugins/<plugin>/skills/<name>/SKILL.md   root = plugins/<plugin>/
 *
 * The walk finds SKILL.md by filename, not by a fixed folder shape, so a fourth
 * layout cannot hide from the check. It ignores the top-level `examples/`, `scripts/`,
 * and `evals/` folders (none of those hold real installable skills; `scripts/` also
 * holds this check's own test fixtures, kept out of the walk on purpose) plus VCS/CI
 * bookkeeping folders.
 *
 * For each SKILL.md, the body is scanned for paths it names (inline code spans and
 * markdown link targets). Three defect classes are reported:
 *   1. escapes-root   a named path resolves outside the skill's own root
 *   2. missing-file   a named path has no file/dir on disk
 *   3. orphan-file     a shipped file under the root is never named by any path
 *
 * Two exemptions keep the check from demanding busywork:
 *   - A file under `agents/` (directly under the skill root) is a plugin component
 *     loaded by folder convention; no SKILL.md needs to name it.
 *   - A file that sits in the same folder as a path the SKILL.md *does* name is
 *     "reached indirectly" (e.g. a `requirements.txt` next to a named `.py` script
 *     that a package manager reads, not a prose reference).
 * A bare cross-reference from one skill's SKILL.md to *another* skill's SKILL.md
 * (e.g. "see the meeting-scribe skill" as a doc link) is a navigational pointer, not
 * a file dependency, and is exempt from the escapes-root / missing-file checks.
 *
 * A short, explicit allowlist covers exactly one pre-existing, deliberately-left
 * orphan: unemployment-guide/references/states.md. That skill is mid-deprecation
 * (tracked separately) and its data file was intentionally left disconnected rather
 * than touched as a side effect of this check.
 *
 * Usage:
 *   node scripts/check-skill-files.mjs [--fixtures <dir>]
 *
 * --fixtures points the whole walk at an alternate root, for this script's own
 * tests (scripts/test-fixtures/check-skill-files/*). Omit it for the real run.
 */

import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join, dirname, basename, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, '..');

// Top-level folders the walk never descends into when scanning the real repo.
// scripts/  -> tooling + this check's own test fixtures, never real skills
// examples/ -> demo/reference material, explicitly out of scope per the spec
// evals/    -> repo-level dev fixtures (e.g. evals/ceo-todo/), not shipped skills
const TOP_LEVEL_IGNORE = new Set(['.git', 'node_modules', 'examples', 'scripts', 'evals', '.github', '.claude-plugin']);

// Files/dirs that are never required to be "named" by a SKILL.md, anywhere under a root.
const ALWAYS_EXEMPT_BASENAMES = new Set(['README.md', 'LICENSE', 'LICENSE.md', '.gitignore']);

// A single, deliberate, pre-existing exception. See file header.
const KNOWN_ORPHAN_ALLOWLIST = new Set(['unemployment-guide/references/states.md']);

function isDir(p) {
  try {
    return statSync(p).isDirectory();
  } catch {
    return false;
  }
}

/** Recursively find every SKILL.md under `root`, ignoring top-level folders in `ignore`. */
function findSkillMdFiles(root, ignoreAtTopLevel) {
  const found = [];
  function walk(dir, depth) {
    for (const name of readdirSync(dir)) {
      if (name.startsWith('.')) continue; // dotfiles/dot-dirs never hold a real SKILL.md
      const full = join(dir, name);
      if (depth === 0 && ignoreAtTopLevel.has(name)) continue;
      if (!isDir(full)) {
        if (name === 'SKILL.md') found.push(full);
        continue;
      }
      walk(full, depth + 1);
    }
  }
  walk(root, 0);
  return found;
}

/**
 * Resolution root for a SKILL.md path:
 *   .../skills/<name>/SKILL.md  -> two levels up (parent of "skills")
 *   everything else             -> the directory containing SKILL.md
 */
function resolveRootFor(skillMdPath) {
  const dir = dirname(skillMdPath);
  const parent = dirname(dir);
  if (dirname(parent) !== parent && basename(parent) === 'skills') {
    return dirname(parent);
  }
  return dir;
}

/** Every regular file under `root`, as absolute paths. */
function listFilesUnder(root) {
  const out = [];
  function walk(dir) {
    for (const name of readdirSync(dir)) {
      const full = join(dir, name);
      if (isDir(full)) walk(full);
      else out.push(full);
    }
  }
  walk(root);
  return out;
}

// --- path extraction from SKILL.md prose -----------------------------------

const CODE_SPAN_RE = /`([^`\n]+)`/g;
const MD_LINK_RE = /\[[^\]]*\]\(([^)\s]+)\)/g;
const FENCE_RE = /```[^\n]*\n([\s\S]*?)```/g;

function candidateTokensFromBody(body) {
  const tokens = new Set();

  for (const m of body.matchAll(CODE_SPAN_RE)) {
    for (const t of m[1].split(/\s+/)) tokens.add(t);
  }
  for (const m of body.matchAll(MD_LINK_RE)) {
    tokens.add(m[1]);
  }
  // Fenced blocks mix two things: real shell commands that name shipped files
  // (`node references/validate.mjs ...`) and illustrative example output (a
  // ```markdown template showing what a generated file looks like). Only scan
  // lines that look like an invocation of a known interpreter/tool, so template
  // content full of made-up example paths and filenames is not mistaken for a
  // dependency this skill must ship.
  const COMMAND_WORDS = new Set(['node', 'python', 'python3', 'pip', 'pip3', 'bash', 'sh', 'npm', 'npx']);
  for (const m of body.matchAll(FENCE_RE)) {
    for (const line of m[1].split('\n')) {
      const trimmed = line.trim();
      const firstWord = trimmed.split(/\s+/)[0];
      if (!COMMAND_WORDS.has(firstWord)) continue;
      for (const t of trimmed.split(/\s+/)) tokens.add(t);
    }
  }
  return [...tokens];
}

const KNOWN_PREFIXES = ['references/', 'scripts/', 'agents/', '../', './'];
const KNOWN_EXTENSIONS = new Set([
  'md', 'py', 'mjs', 'js', 'ts', 'json', 'csv', 'ics', 'txt', 'sh', 'yml', 'yaml', 'pdf', 'png', 'jpg', 'jpeg',
]);

/** True if `token` looks like a repo-relative path this check should validate. */
function looksLikeNamedPath(token) {
  if (!token) return false;
  if (/^(https?:|mailto:)/.test(token)) return false;
  if (token.startsWith('#')) return false;
  if (token.startsWith('/')) return false; // web route, not a repo-relative path
  if (token.startsWith('~')) return false;
  if (/[<>{}*[\]]/.test(token)) return false; // placeholders/globs, not real paths
  if (!token.includes('/')) return false;

  // strip a trailing anchor fragment (e.g. "SKILL.md#inputs")
  const withoutAnchor = token.split('#')[0];
  if (!withoutAnchor) return false;

  if (KNOWN_PREFIXES.some((p) => withoutAnchor.startsWith(p))) return true;

  const lastSegment = withoutAnchor.replace(/\/$/, '').split('/').pop() || '';
  const dot = lastSegment.lastIndexOf('.');
  if (dot > 0) {
    const ext = lastSegment.slice(dot + 1).toLowerCase();
    if (KNOWN_EXTENSIONS.has(ext)) return true;
  }
  return false;
}

function stripAnchor(token) {
  return token.split('#')[0];
}

function stripWrappingPunctuation(token) {
  return token.replace(/^['"(]+/, '').replace(/['").,;:]+$/, '');
}

// --- main --------------------------------------------------------------------

function main() {
  const args = process.argv.slice(2);
  const fixturesIdx = args.indexOf('--fixtures');
  const walkRoot = fixturesIdx !== -1 ? args[fixturesIdx + 1] : repoRoot;
  const ignoreSet = fixturesIdx !== -1 ? new Set() : TOP_LEVEL_IGNORE;

  const skillMdFiles = findSkillMdFiles(walkRoot, ignoreSet);

  if (skillMdFiles.length === 0) {
    console.error('No SKILL.md files found. Did the folder layout change?');
    process.exit(2);
  }

  // The full set of recognized skill entry points in this run, used to constrain
  // the cross-skill SKILL.md exemption below: a named path is only exempt from the
  // escapes-root/missing-file checks when it resolves to one of *these* files, not
  // to any file on disk that happens to be named SKILL.md.
  const skillMdFileSet = new Set(skillMdFiles);

  // Group entries by resolution root, since a plugin-nested root can host several
  // skills whose combined named-path set determines whether a shared file is an orphan.
  const entriesByRoot = new Map(); // root -> [{ file }]
  for (const file of skillMdFiles) {
    const root = resolveRootFor(file);
    if (!entriesByRoot.has(root)) entriesByRoot.set(root, []);
    entriesByRoot.get(root).push(file);
  }

  const failures = [];
  let skillCount = 0;

  for (const [root, files] of entriesByRoot) {
    const namedFilesForRoot = new Set(); // resolved files reached directly or via a named dir
    const namedDirsForRoot = new Set(); // dirs containing a named file, for indirect-reach

    for (const skillMd of files) {
      skillCount += 1;
      const raw = readFileSync(skillMd, 'utf8');
      const body = raw.replace(/^---\n[\s\S]*?\n---\n/, ''); // drop frontmatter
      const tokens = candidateTokensFromBody(body);

      for (const rawToken of tokens) {
        const token = stripWrappingPunctuation(rawToken);
        if (!looksLikeNamedPath(token)) continue;
        const clean = stripAnchor(token);
        if (!clean) continue;

        // Paths are resolved relative to the skill's resolution root, not the
        // SKILL.md file's own directory — for a flat skill those are the same
        // place, but for a nested/plugin-nested skill they are not (see header).
        const resolved = join(root, clean);

        // Exemption: a bare cross-reference to *another recognized skill's* own
        // SKILL.md is a navigational pointer, not a file dependency this skill
        // must ship. Constrained to the walk's own skillMdFileSet, not "any file
        // on disk named SKILL.md" — otherwise a path like ../../../x/SKILL.md
        // would pass even when it escapes the repo entirely.
        if (skillMdFileSet.has(resolved) && resolved !== skillMd) {
          continue;
        }

        const rel = relative(root, resolved);
        const escapesRoot = rel.startsWith('..') || rel === '';
        if (escapesRoot) {
          failures.push(`${relative(repoRoot, skillMd)}: names "${rawToken}" which resolves outside its own skill folder (${relative(repoRoot, resolved) || '.'})`);
          continue;
        }

        if (!existsSync(resolved)) {
          failures.push(`${relative(repoRoot, skillMd)}: names "${rawToken}" which does not exist (expected ${relative(repoRoot, resolved)})`);
          continue;
        }

        if (isDir(resolved)) {
          for (const f of listFilesUnder(resolved)) namedFilesForRoot.add(f);
          namedDirsForRoot.add(resolved);
        } else {
          namedFilesForRoot.add(resolved);
          namedDirsForRoot.add(dirname(resolved));
        }
      }
    }

    // Orphan check: every shipped file under this root must be reached, directly or
    // indirectly, by the combined named-path set of every skill sharing this root.
    const allFiles = listFilesUnder(root);
    const skillMdFilesInRoot = new Set(files);

    for (const file of allFiles) {
      const rel = relative(root, file);
      const parts = rel.split(sep);
      const basename = parts[parts.length - 1];

      if (skillMdFilesInRoot.has(file)) continue; // a skill's own entry point
      if (ALWAYS_EXEMPT_BASENAMES.has(basename)) continue;
      if (parts[0] === '.claude-plugin') continue;
      if (parts[0] === 'agents') continue; // plugin component, loaded by folder convention

      const relFromRepo = relative(repoRoot, file).split(sep).join('/');
      if (KNOWN_ORPHAN_ALLOWLIST.has(relFromRepo)) continue;

      if (namedFilesForRoot.has(file)) continue;
      if (namedDirsForRoot.has(dirname(file))) continue; // reached indirectly

      failures.push(`${relative(repoRoot, file)}: shipped file is not named by any path in a SKILL.md under ${relative(repoRoot, root) || '.'}/`);
    }
  }

  // No internal count guard here: skillCount is incremented once per entry in
  // skillMdFiles, so comparing them would be a tautology that can never fire. The
  // real, independent check — that the walk found every SKILL.md actually on
  // disk — lives in scripts/test-check-skill-files.mjs (its disk-count case,
  // computed by a second, separately-written directory walk) and is wired into
  // CI as its own step.

  if (failures.length > 0) {
    console.error('Skill file check FAILED:');
    for (const f of [...new Set(failures)].sort()) console.error('  - ' + f);
    process.exit(1);
  }

  console.log(`checked ${skillCount} skills, all referenced files resolve inside their own skill folder`);
}

main();
