/**
 * skill-walk.mjs
 *
 * The one place that decides which files in the repo are catalog entries, and
 * which plugins install them. Shared by build-index.mjs (writes index.json)
 * and check-marketplace-parity.mjs (compares the index side to the plugin
 * side), so the two cannot drift apart.
 *
 * Every function takes a sorted list of repo-relative, forward-slash file
 * paths (git's own listing, or a filesystem listing in tests), never a
 * directory handle. No I/O happens here.
 */

/**
 * Classify `path` as a catalog entry rooted at `folder`, or null.
 *
 *   <folder>/SKILL.md                  -> skill, slug = basename of <folder>
 *   <folder>/skills/<name>/SKILL.md    -> skill, slug = <name>
 *   <folder>/agents/<name>.md          -> agent, slug = <name>
 */
export function classifyUnder(path, folder) {
  const prefix = folder + '/';
  if (!path.startsWith(prefix)) return null;
  const rel = path.slice(prefix.length);
  let m;
  if (rel === 'SKILL.md') {
    return { slug: folder.split('/').pop(), file: path, kind: 'skill' };
  }
  if ((m = rel.match(/^skills\/([^/]+)\/SKILL\.md$/))) {
    return { slug: m[1], file: path, kind: 'skill' };
  }
  if ((m = rel.match(/^agents\/([^/]+)\.md$/))) {
    return { slug: m[1], file: path, kind: 'agent' };
  }
  return null;
}

/**
 * Every catalog entry in the repo: each top-level folder is a candidate
 * root. Dot-folders, scripts/ and node_modules/ are never entries.
 */
export function walkSkillFolders(sourceFiles) {
  const entries = [];
  for (const path of sourceFiles) {
    if (!path.includes('/')) continue;
    const top = path.split('/')[0];
    if (top.startsWith('.') || top === 'scripts' || top === 'node_modules') continue;
    const entry = classifyUnder(path, top);
    if (entry) entries.push(entry);
  }
  return entries;
}

/** Normalize a marketplace `source` ("./plugins/x") to a repo-relative dir, or null. */
export function normalizeSource(source) {
  if (typeof source !== 'string') return null;
  const dir = source.replace(/^\.\//, '').replace(/\/+$/, '');
  if (!dir || dir === '.' || dir.startsWith('/') || dir.split('/').includes('..')) return null;
  return dir;
}

/** Entries a single plugin source dir installs, by the same rules as the repo walk. */
export function walkPluginSource(sourceFiles, sourceDir) {
  const entries = [];
  for (const path of sourceFiles) {
    const entry = classifyUnder(path, sourceDir);
    if (entry) entries.push(entry);
  }
  return entries;
}

/**
 * Map<slug, string[]> of the plugin names that install each slug, in
 * marketplace array order, no duplicates.
 */
export function pluginsBySlug(marketplace, sourceFiles) {
  const map = new Map();
  for (const plugin of (marketplace && marketplace.plugins) || []) {
    const dir = normalizeSource(plugin.source);
    if (!dir || typeof plugin.name !== 'string') continue;
    for (const { slug } of walkPluginSource(sourceFiles, dir)) {
      const names = map.get(slug) || [];
      if (!names.includes(plugin.name)) names.push(plugin.name);
      map.set(slug, names);
    }
  }
  return map;
}
