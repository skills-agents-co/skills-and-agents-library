#!/usr/bin/env node
/**
 * test-build-index.mjs
 *
 * Fixture-driven tests for scripts/build-index.mjs, the largest piece of logic
 * in this repo and, until now, the one with no test of its own. Its only
 * coverage was check-index-additive.mjs's check 1, which regenerates the index
 * and compares it to the committed file — a self-consistency check that cannot
 * catch a derivation that is systematically wrong in both.
 *
 * Follows the repo's convention for script tests (test-check-skill-files.mjs,
 * test-check-backlinks.mjs): drive the real script via spawnSync against a
 * fixture tree and assert on its exit code and output.
 *
 * The fixture is a throwaway git repository, because the behavior under test is
 * *where the script reads content from*. build-index.mjs locates its repo root
 * relative to its own file, so the script and its library are copied into the
 * fixture repo and run from there. That keeps every git command in these tests
 * pointed at the fixture and never at this repo.
 *
 * What is covered:
 *   - the three entry layouts: flat, nested (skills/<name>/SKILL.md), and
 *     agent (agents/<name>.md)
 *   - --tag reads content AT that ref: a file committed after the tag must not
 *     appear in the tagged manifest, and a file deleted after the tag must
 *     still appear in it
 *   - an unresolvable ref is a hard failure, not a silent working-tree fallback
 *   - --worktree is the explicit escape hatch and still reads the working tree
 *   - an unsafe ref is rejected before it reaches git or a published URL
 *
 * No network access needed.
 *
 * Usage: node scripts/test-build-index.mjs
 */

import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync, mkdtempSync, rmSync, copyFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

const TAG = 'v9.9.9';

const scratch = mkdtempSync(join(tmpdir(), 'test-build-index-'));
process.on('exit', () => rmSync(scratch, { recursive: true, force: true }));

// --- Build the fixture repo --------------------------------------------------

const fixture = join(scratch, 'repo');

// The fixture must not inherit the developer's own git configuration: a global
// commit.gpgsign, a core.hooksPath pointing at a hook that rejects the commit,
// or a templatedir would make these tests fail for reasons that have nothing to
// do with build-index.mjs. Every invocation is isolated the same way, including
// `git init`.
const GIT_ISOLATION = [
  '-c', 'commit.gpgsign=false',
  '-c', 'tag.gpgsign=false',
  '-c', 'core.hooksPath=/dev/null',
  '-c', 'init.templateDir=',
];

function git(...args) {
  const res = spawnSync('git', [...GIT_ISOLATION, ...args], {
    cwd: fixture,
    encoding: 'utf8',
    env: { ...process.env, GIT_CONFIG_GLOBAL: '/dev/null', GIT_CONFIG_SYSTEM: '/dev/null' },
  });
  if (res.status !== 0) {
    console.error(`fixture git ${args.join(' ')} failed: ${res.stderr || res.stdout}`);
    process.exit(1);
  }
  return res.stdout;
}

function write(relPath, text) {
  const full = join(fixture, relPath);
  mkdirSync(dirname(full), { recursive: true });
  writeFileSync(full, text);
}

function skillMd(name, description) {
  return `---\nname: ${name}\ndescription: ${description}\nversion: 1.0.0\n---\n\nBody for ${name}.\n`;
}

mkdirSync(fixture, { recursive: true });
git('init', '-q', '-b', 'main');
git('config', 'user.email', 'test@example.com');
git('config', 'user.name', 'Fixture');

// Layout 1: flat skill.
write('flat-skill/SKILL.md', skillMd('flat-skill', 'A flat skill.'));
write('flat-skill/references/notes.md', 'notes\n');
write('flat-skill/scripts/run.py', 'print("hi")\n');

// Layout 2: nested skill — slug comes from skills/<name>/, install folder is
// the top-level directory.
write('nested-pack/skills/nested-skill/SKILL.md', skillMd('nested-skill', 'A nested skill.'));
write('nested-pack/references/guide.md', 'guide\n');

// Layout 3: agent — slug comes from agents/<name>.md.
write('agent-pack/SKILL.md', skillMd('agent-pack', 'A skill that ships an agent.'));
write('agent-pack/agents/helper-agent.md', skillMd('helper-agent', 'An agent.'));

// A file that exists at the tag and is deleted afterwards.
write('flat-skill/references/removed-later.md', 'gone in a later commit\n');

// Copy the script under test and its library in, so the script's own
// repo-root-relative lookups resolve to the fixture repo.
mkdirSync(join(fixture, 'scripts', 'lib'), { recursive: true });
copyFileSync(join(__dirname, 'build-index.mjs'), join(fixture, 'scripts', 'build-index.mjs'));
copyFileSync(join(__dirname, 'lib', 'index-ref.mjs'), join(fixture, 'scripts', 'lib', 'index-ref.mjs'));

git('add', '-A');
git('commit', '-q', '-m', 'fixture at the tag');
git('tag', TAG);

// Now move the working tree AWAY from the tag, in both directions.
write('flat-skill/references/added-later.md', 'added after the tag\n');
rmSync(join(fixture, 'flat-skill/references/removed-later.md'));
git('add', '-A');
git('commit', '-q', '-m', 'post-tag changes');

const script = join(fixture, 'scripts', 'build-index.mjs');

function build(args) {
  const out = join(scratch, `out-${Math.random().toString(36).slice(2)}.json`);
  const res = spawnSync('node', [script, ...args, '--out', out], {
    cwd: fixture, encoding: 'utf8', timeout: 60_000,
  });
  let index = null;
  if (res.status === 0) {
    try { index = JSON.parse(readFileSync(out, 'utf8')); } catch { /* leave null */ }
  }
  return { code: res.status, out: (res.stdout || '') + (res.stderr || ''), index };
}

// --- Cases -------------------------------------------------------------------

let failures = 0;

function check(name, fn) {
  const problems = [];
  try {
    fn((cond, msg) => { if (!cond) problems.push(msg); });
  } catch (err) {
    problems.push(`threw: ${err.message}`);
  }
  const pass = problems.length === 0;
  console.log(`  [${pass ? 'PASS' : 'FAIL'}] ${name}`);
  if (!pass) {
    failures++;
    for (const p of problems) console.log('        - ' + p);
  }
}

check('the three layouts each produce one correctly-shaped entry', (want) => {
  const { code, index, out } = build(['--tag', TAG]);
  want(code === 0, `exit ${code}, wanted 0. Output: ${out}`);
  if (!index) return;

  want(
    JSON.stringify(Object.keys(index)) === JSON.stringify(['agent-pack', 'flat-skill', 'helper-agent', 'nested-skill']),
    `slugs were ${JSON.stringify(Object.keys(index))}`
  );

  const flat = index['flat-skill'];
  want(flat.kind === 'skill', `flat kind was ${flat.kind}`);
  want(flat.installFolder === 'flat-skill', `flat installFolder was ${flat.installFolder}`);
  want(flat.skillFilePath === 'SKILL.md', `flat skillFilePath was ${flat.skillFilePath}`);
  want(flat.path === 'flat-skill/SKILL.md', `flat path was ${flat.path}`);

  // Nested: the slug is the inner folder, but the install folder is the top
  // one — the distinction the README's old slug==folder assumption got wrong.
  const nested = index['nested-skill'];
  want(nested.kind === 'skill', `nested kind was ${nested.kind}`);
  want(nested.installFolder === 'nested-pack', `nested installFolder was ${nested.installFolder}`);
  want(nested.skillFilePath === 'skills/nested-skill/SKILL.md', `nested skillFilePath was ${nested.skillFilePath}`);
  want(nested.files.includes('references/guide.md'), 'nested manifest lost the sibling references file');

  // Derived CONTENT, not just structure. Everything above could be right while
  // name/description/version were read out of the wrong file, or off by one
  // entry, and the structural assertions would not notice — which is exactly
  // the class of bug check-index-additive.mjs's self-comparison cannot see
  // either. These values come straight from the fixture's own frontmatter.
  want(flat.name === 'flat-skill', `flat name was ${JSON.stringify(flat.name)}`);
  want(flat.description === 'A flat skill.', `flat description was ${JSON.stringify(flat.description)}`);
  want(flat.version === '1.0.0', `flat version was ${JSON.stringify(flat.version)}`);

  want(nested.name === 'nested-skill', `nested name was ${JSON.stringify(nested.name)}`);
  want(
    nested.description === 'A nested skill.',
    `nested description was ${JSON.stringify(nested.description)} — a derivation that read the wrong SKILL.md would land here`
  );
  want(nested.version === '1.0.0', `nested version was ${JSON.stringify(nested.version)}`);

  const agent = index['helper-agent'];
  want(agent.kind === 'agent', `agent kind was ${agent.kind}`);
  want(agent.installFolder === 'agent-pack', `agent installFolder was ${agent.installFolder}`);
  want(agent.skillFilePath === 'agents/helper-agent.md', `agent skillFilePath was ${agent.skillFilePath}`);

  // Every entry reconstructs its own path and lists its own skill file — the
  // same invariants check-index-additive.mjs enforces on the real index.
  for (const [slug, v] of Object.entries(index)) {
    want(`${v.installFolder}/${v.skillFilePath}` === v.path, `${slug}: installFolder + skillFilePath != path`);
    want(v.files.includes(v.skillFilePath), `${slug}: files does not list its own skillFilePath`);
    want(v.skillFileUrl.includes(`/${TAG}/`), `${slug}: skillFileUrl is not pinned to ${TAG}`);
  }
});

check('--tag reads content AT the ref, not the working tree', (want) => {
  const { code, index } = build(['--tag', TAG]);
  want(code === 0, `exit ${code}, wanted 0`);
  if (!index) return;
  const files = index['flat-skill'].files;
  // This is the whole point of reading at a ref: the tarball a user downloads
  // for TAG contains removed-later.md and does not contain added-later.md, so
  // the manifest that describes TAG must say the same.
  want(files.includes('references/removed-later.md'), 'a file present at the tag is missing from the tagged manifest');
  want(!files.includes('references/added-later.md'), 'a file added after the tag leaked into the tagged manifest');
});

check('an unresolvable ref fails loudly instead of falling back to the working tree', (want) => {
  const { code, out, index } = build(['--tag', 'v0.0.0-not-in-this-clone']);
  want(code !== 0, `exit ${code}, wanted non-zero — a silent working-tree fallback is the deadlock this guards`);
  want(index === null, 'an index was written despite the ref not resolving');
  want(out.includes('does not resolve in this clone'), `output did not name the unresolvable ref. Output: ${out}`);
  want(out.includes('--worktree'), 'the failure message does not point at the --worktree escape hatch');
});

check('--worktree is the explicit escape hatch and reads the working tree', (want) => {
  // Same unresolvable ref as above. With --worktree it must succeed, label the
  // URLs with that ref, and read post-tag working-tree content.
  const { code, out, index } = build(['--tag', 'v0.0.0-not-in-this-clone', '--worktree']);
  want(code === 0, `exit ${code}, wanted 0. Output: ${out}`);
  if (!index) return;
  const files = index['flat-skill'].files;
  want(files.includes('references/added-later.md'), '--worktree did not pick up the post-tag file');
  want(!files.includes('references/removed-later.md'), '--worktree still lists a file deleted after the tag');
  want(out.includes('working tree'), 'the run did not say it read from the working tree');
});

check('an unsafe ref is rejected before it reaches git or a published URL', (want) => {
  for (const bad of ['-x', '../etc', 'a..b']) {
    const { code, out, index } = build(['--tag', bad]);
    want(code === 2, `ref ${JSON.stringify(bad)}: exit ${code}, wanted 2`);
    want(index === null, `ref ${JSON.stringify(bad)}: an index was written anyway`);
    want(out.includes('unsafe ref'), `ref ${JSON.stringify(bad)}: output did not say the ref was unsafe`);
  }
});

check('a missing --tag is a usage error', (want) => {
  const { code, out } = build([]);
  want(code === 2, `exit ${code}, wanted 2`);
  want(out.includes('Usage:'), 'no usage message');
});

console.log('');
if (failures > 0) {
  console.error(`TEST FAILURES: ${failures}`);
  process.exit(1);
}
console.log('All build-index cases behaved as expected.');
process.exit(0);
