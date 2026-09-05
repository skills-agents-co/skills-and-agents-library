/**
 * index-ref.mjs
 *
 * The single source of truth for "which git ref does this repo's published
 * install pin to". Two readers need the answer and used to carry their own
 * copy of the regex (scripts/test-install.sh and scripts/check-index-additive.mjs),
 * so an org rename or a URL change could silently desynchronize them.
 *
 * Also usable as a CLI, which is how the bash script consumes it:
 *
 *   node scripts/lib/index-ref.mjs index <path/to/index.json>   # prints the ref
 *   node scripts/lib/index-ref.mjs readme <path/to/README.md>   # prints the ref
 *
 * Exits 1 with a message on stderr when the ref cannot be found.
 */

import { readFileSync } from 'node:fs';

export const REPO_SLUG = 'skills-agents-co/skills-and-agents-library';

/** Matches the pinned ref in a raw.githubusercontent.com skillFileUrl. */
export const SKILL_FILE_URL_RE = new RegExp(
  '^https://raw\\.githubusercontent\\.com/' + REPO_SLUG.replace('/', '/') + '/([^/]+)/'
);

/** A ref this repo is willing to put in a URL: git-ref-safe, and no "..". */
export function isSafeRef(ref) {
  return typeof ref === 'string' && ref.length > 0 && /^[A-Za-z0-9._/-]+$/.test(ref) && !ref.includes('..');
}

/**
 * The ref index.json pins, read off the first entry's skillFileUrl. Every
 * entry carries the same ref, so the first is representative.
 * Returns null when it cannot be determined.
 */
export function refFromIndex(indexJsonText) {
  let idx;
  try {
    idx = JSON.parse(indexJsonText);
  } catch {
    return null;
  }
  const first = Object.values(idx)[0];
  if (!first || typeof first.skillFileUrl !== 'string') return null;
  const m = first.skillFileUrl.match(SKILL_FILE_URL_RE);
  return m ? m[1] : null;
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

const isMain = process.argv[1] && process.argv[1].endsWith('index-ref.mjs');
if (isMain) {
  const [mode, path] = process.argv.slice(2);
  if (!mode || !path) {
    console.error('Usage: node scripts/lib/index-ref.mjs <index|readme> <path>');
    process.exit(2);
  }
  const text = readFileSync(path, 'utf8');
  const ref = mode === 'index' ? refFromIndex(text) : mode === 'readme' ? refFromReadme(text) : undefined;
  if (ref === undefined) {
    console.error(`Unknown mode "${mode}" (want "index" or "readme")`);
    process.exit(2);
  }
  if (!ref) {
    console.error(`Could not extract a ref from ${path}`);
    process.exit(1);
  }
  process.stdout.write(ref);
}
