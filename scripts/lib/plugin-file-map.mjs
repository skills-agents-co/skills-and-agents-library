/**
 * plugin-file-map.mjs
 *
 * Shared validation for plugin-file-map.json, the manifest read by both
 * scripts/generate-plugin-files.mjs (which writes the `generated` copies) and
 * scripts/check-plugin-files-fresh.mjs (which only verifies they're up to
 * date). The two used to each carry their own copy of resolveInRoot and
 * validateManifest — ~90 identical lines — which is exactly how the two could
 * have drifted on what counts as a valid manifest. Following the convention
 * scripts/lib/index-ref.mjs already set for this repo: pull the logic every
 * reader must agree on into one shared module, keep `fail`/argv parsing local
 * to each script since those are script-specific.
 *
 * Both exports take a `fail` callback rather than importing one, so each
 * script keeps its own `fail(message)` (print "FAIL: ..." and exit 1) and
 * this module stays agnostic about how a problem gets reported.
 */

import { existsSync, statSync, realpathSync } from 'node:fs';
import { dirname, resolve, isAbsolute, sep } from 'node:path';

/**
 * The nearest existing ancestor of `p` (which may be `p` itself), or null if
 * no ancestor exists on disk (e.g. every segment up to the filesystem root is
 * missing — not expected in practice, but resolveInRoot must not crash on
 * it).
 */
function nearestExistingAncestor(p) {
  let cur = p;
  for (;;) {
    if (existsSync(cur)) return cur;
    const parent = dirname(cur);
    if (parent === cur) return null;
    cur = parent;
  }
}

/**
 * Resolve `relPath` against `root` and abort (via `fail`) if it would escape
 * `root`. Returns the resolved absolute path — every call site should use
 * this return value rather than recomputing join(root, relPath) itself.
 *
 * Containment is checked twice:
 *   1. Lexically, on the strings alone (catches "../../etc/passwd").
 *   2. On disk, via realpathSync of the nearest existing ancestor (catches a
 *      symlinked path segment that resolves lexically inside root but points
 *      somewhere else once the filesystem follows it). A `generated` path
 *      frequently doesn't exist yet, so the disk check walks up to whichever
 *      ancestor directory does exist and realpath-checks that instead of the
 *      file itself.
 */
export function resolveInRoot(root, relPath, label, fail) {
  const rootResolved = resolve(root);
  if (isAbsolute(relPath)) {
    fail(`${label} "${relPath}" must be a relative path, not absolute`);
  }
  const resolved = resolve(root, relPath);
  if (resolved !== rootResolved && !resolved.startsWith(rootResolved + sep)) {
    fail(`${label} "${relPath}" resolves outside of ${root} (path escapes the root)`);
  }

  let realRoot;
  try {
    realRoot = realpathSync(rootResolved);
  } catch {
    return resolved; // root doesn't exist on disk yet — nothing more to check
  }

  const nearestExisting = nearestExistingAncestor(resolved);
  if (nearestExisting === null) return resolved;

  let realNearest;
  try {
    realNearest = realpathSync(nearestExisting);
  } catch {
    return resolved;
  }
  if (realNearest !== realRoot && !realNearest.startsWith(realRoot + sep)) {
    fail(`${label} "${relPath}" escapes ${root} once symlinks on disk are resolved`);
  }

  return resolved;
}

/**
 * Validate the shape of a parsed plugin-file-map.json manifest and every path
 * it names, aborting (via `fail`) with a clear message on the first problem
 * found — including an empty-array manifest, which checks nothing and
 * silently disables whichever guard is calling this.
 *
 * On success, returns a normalized array of
 *   { source, sourcePath, generated: [{ path, resolvedPath }] }
 * with every path already resolved against `root`, so callers never need to
 * re-resolve a path this function already resolved.
 */
export function validateManifest(manifest, root, manifestPath, fail) {
  if (!Array.isArray(manifest)) {
    fail(`manifest ${manifestPath} must be a JSON array, got ${typeof manifest}`);
  }

  if (manifest.length === 0) {
    fail(`manifest ${manifestPath} is an empty array — an empty manifest checks nothing and disables this guard`);
  }

  const normalized = [];
  const allGenerated = [];

  manifest.forEach((entry, i) => {
    if (typeof entry !== 'object' || entry === null || Array.isArray(entry)) {
      fail(`manifest ${manifestPath}: entry ${i} must be an object, got ${JSON.stringify(entry)}`);
    }
    if (typeof entry.source !== 'string' || entry.source.trim() === '') {
      fail(`manifest ${manifestPath}: entry ${i} must have a non-empty string "source", got ${JSON.stringify(entry.source)}`);
    }
    if (!Array.isArray(entry.generated) || entry.generated.length === 0) {
      fail(`manifest ${manifestPath}: entry ${i} (source "${entry.source}") must have a non-empty array "generated"`);
    }
    entry.generated.forEach((g, j) => {
      if (typeof g !== 'string' || g.trim() === '') {
        fail(`manifest ${manifestPath}: entry ${i} (source "${entry.source}") generated[${j}] must be a non-empty string, got ${JSON.stringify(g)}`);
      }
    });

    const sourcePath = resolveInRoot(root, entry.source, `manifest ${manifestPath}: entry ${i} source`, fail);

    if (existsSync(sourcePath) && !statSync(sourcePath).isFile()) {
      fail(`manifest ${manifestPath}: entry ${i} source "${entry.source}" is not a file (is it a directory?)`);
    }

    const generated = entry.generated.map((g) => ({
      path: g,
      resolvedPath: resolveInRoot(root, g, `manifest ${manifestPath}: entry ${i} (source "${entry.source}") generated`, fail),
    }));

    normalized.push({ source: entry.source, sourcePath, generated });
    allGenerated.push(...entry.generated);
  });

  const generatedSeen = new Set();
  for (const g of allGenerated) {
    if (generatedSeen.has(g)) {
      fail(`manifest ${manifestPath}: "${g}" is listed as a "generated" path more than once`);
    }
    generatedSeen.add(g);
  }

  const sourceSet = new Set(normalized.map((e) => e.source));
  for (const g of allGenerated) {
    if (sourceSet.has(g)) {
      fail(`manifest ${manifestPath}: "${g}" is listed as both a "source" and a "generated" path`);
    }
  }

  return normalized;
}
