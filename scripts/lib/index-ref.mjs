/**
 * index-ref.mjs
 *
 * The single source of truth for "which git ref does this repo's published
 * install pin to". Two readers need the answer and used to carry their own
 * copy of the regex (scripts/test-install.sh and scripts/check-index-additive.mjs),
 * so an org rename or a URL change could silently desynchronize them.
 *
 * It also owns the two other rules every one of those readers needs to agree
 * on: what counts as a safe ref, and what counts as a manifest path that stays
 * inside its install folder.
 *
 * Also usable as a CLI, which is how the bash scripts consume it:
 *
 *   node scripts/lib/index-ref.mjs index <path/to/index.json>   # prints the ref
 *   node scripts/lib/index-ref.mjs readme <path/to/README.md>   # prints the ref
 *   node scripts/lib/index-ref.mjs safe-ref <ref>               # exit 0 if safe
 *
 * Exits 1 with a message on stderr when the ref cannot be found.
 */

import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

export const REPO_SLUG = 'skills-agents-co/skills-and-agents-library';

/**
 * Matches the pinned ref in a raw.githubusercontent.com skillFileUrl.
 *
 * REPO_SLUG's one "/" is already a literal in a regex, so it is embedded as-is
 * rather than passed through a replace() that substitutes a character for
 * itself. The earlier `.replace('/', '/')` read like escaping and did nothing.
 */
export const SKILL_FILE_URL_RE = new RegExp(
  '^https://raw\\.githubusercontent\\.com/' + REPO_SLUG + '/([^/]+)/'
);

/**
 * A ref this repo is willing to put in a URL or hand to git: git-ref-safe, no
 * "..", and it must start with an alphanumeric. That last rule is what keeps a
 * value like "-x" or "--upload-pack=..." from reaching git as an option rather
 * than as a ref.
 */
export function isSafeRef(ref) {
  return (
    typeof ref === 'string' &&
    /^[A-Za-z0-9][A-Za-z0-9._/-]*$/.test(ref) &&
    !ref.includes('..')
  );
}

/**
 * A manifest path that escapes its install folder, or names a directory rather
 * than a file: absolute, or holding a "." or ".." segment. Shared so
 * build-index.mjs (which refuses to write one) and check-index-additive.mjs
 * (which refuses to accept one) cannot drift apart on the definition.
 */
export const TRAVERSAL = /(^\/)|(^|\/)\.\.?(\/|$)/;

/** True when `p` is a non-empty string that stays inside its install folder. */
export function isSafeManifestPath(p) {
  return typeof p === 'string' && p.length > 0 && !TRAVERSAL.test(p);
}

/**
 * The ref index.json pins, read off its entries' skillFileUrl.
 *
 * Every entry is expected to carry the same ref. Reading only the first and
 * assuming the rest agree is how a half-regenerated index.json would go
 * unnoticed, so all entries are checked and a disagreement returns null rather
 * than an arbitrary winner.
 *
 * Returns null when it cannot be determined.
 */
export function refFromIndex(indexJsonText) {
  let idx;
  try {
    idx = JSON.parse(indexJsonText);
  } catch {
    return null;
  }
  if (!idx || typeof idx !== 'object') return null;
  const entries = Object.values(idx);
  if (entries.length === 0) return null;
  let ref = null;
  for (const entry of entries) {
    if (!entry || typeof entry.skillFileUrl !== 'string') return null;
    const m = entry.skillFileUrl.match(SKILL_FILE_URL_RE);
    if (!m) return null;
    if (ref === null) ref = m[1];
    else if (ref !== m[1]) return null;
  }
  return ref;
}

/**
 * The ref README.md's documented install pins.
 *
 * Scoped to the fenced bash block that contains the codeload URL, rather than
 * the first `ref="..."` anywhere in the file: an unrelated earlier occurrence
 * (an anchor, a second example) would otherwise make the caller compare the
 * wrong value. Returns null when no such block carries a ref.
 */
export function refFromReadme(readmeText) {
  const fences = readmeText.match(/```bash\n[\s\S]*?\n```/g) || [];
  for (const block of fences) {
    if (!block.includes('codeload.github.com/' + REPO_SLUG)) continue;
    const m = block.match(/^\s*ref="([^"]+)"/m);
    if (m) return m[1];
  }
  return null;
}

// --- CLI -------------------------------------------------------------------

// Compare resolved URLs rather than matching the filename's suffix. The old
// endsWith('index-ref.mjs') test also matched any importer whose own filename
// ended the same way (scripts/test-index-ref.mjs did), so importing this
// module from there ran the CLI and exited before a single test could run.
const isMain = process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (isMain) {
  const [mode, path] = process.argv.slice(2);
  if (!mode || path === undefined) {
    console.error('Usage: node scripts/lib/index-ref.mjs <index|readme|safe-ref> <path-or-ref>');
    process.exit(2);
  }
  // safe-ref takes a ref rather than a file, so it answers before the read.
  if (mode === 'safe-ref') {
    if (!isSafeRef(path)) {
      console.error(`Refusing to use unsafe ref: '${path}'`);
      process.exit(1);
    }
    process.exit(0);
  }
  // Validate the mode before touching the filesystem: an unknown mode with an
  // unreadable path used to throw an ENOENT stack trace instead of saying which
  // modes exist.
  if (mode !== 'index' && mode !== 'readme') {
    console.error(`Unknown mode "${mode}" (want "index", "readme", or "safe-ref")`);
    process.exit(2);
  }
  const text = readFileSync(path, 'utf8');
  const ref = mode === 'index' ? refFromIndex(text) : refFromReadme(text);
  if (!ref) {
    console.error(`Could not extract a ref from ${path}`);
    process.exit(1);
  }
  process.stdout.write(ref);
}
