#!/usr/bin/env bash
# test-install.sh
#
# Reads index.json, downloads ONE pinned tarball of the repo (the README
# install pattern, not a per-file curl), then for every entry extracts that
# skill's own subdirectory the same way the README command does and asserts
# every path listed in the entry's `files` array actually arrived on disk.
# Also sanity-checks that SKILL.md/agent .md files still start with YAML
# frontmatter. Exits non-zero on first class of failure encountered.

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INDEX="$REPO_ROOT/index.json"

# Allow an alternate index.json (used by the negative-test harness below).
INDEX="${1:-$INDEX}"

if [[ ! -f "$INDEX" ]]; then
  echo "index.json not found at $INDEX" >&2
  echo "Run: node scripts/build-index.mjs --tag <tag>" >&2
  exit 2
fi

# NOTE: intentionally NOT named TMPDIR. TMPDIR is the POSIX temp-directory
# variable every child process (mktemp, curl, tar, ...) consults to decide
# where to put ITS OWN scratch files; assigning it here would redirect their
# writes into this script's own scratch dir, which the trap below then
# deletes out from under them.
SCRATCH_DIR=$(mktemp -d)
trap 'rm -rf "$SCRATCH_DIR"' EXIT

FAIL=0
TOTAL=0

# Every entry in index.json was built from a single --tag, so every
# skillFileUrl is pinned to the same ref. Recover that ref from the first
# entry rather than hardcoding it, so this script stays correct as the pin
# changes.
REF=$(node -e '
  const idx = JSON.parse(require("fs").readFileSync(process.argv[1], "utf8"));
  const first = Object.values(idx)[0];
  if (!first) { process.exit(0); }
  const m = first.skillFileUrl.match(/^https:\/\/raw\.githubusercontent\.com\/Anlo-Ventures\/skills-and-agents-library\/([^/]+)\//);
  if (!m) { console.error("could not parse ref from skillFileUrl: " + first.skillFileUrl); process.exit(1); }
  process.stdout.write(m[1]);
' "$INDEX")

if [[ -z "$REF" ]]; then
  echo "index.json has no entries; nothing to test" >&2
  exit 0
fi

echo "Downloading tarball for ref '$REF' (same pin the README install command uses)..."
TARBALL="$SCRATCH_DIR/repo.tar.gz"
if ! curl -fsSL -o "$TARBALL" "https://codeload.github.com/Anlo-Ventures/skills-and-agents-library/tar.gz/$REF"; then
  echo "FAIL: could not download tarball for ref $REF" >&2
  exit 1
fi

TOPDIR=$(tar -tzf "$TARBALL" | head -n 1 | cut -d/ -f1)
if [[ -z "$TOPDIR" ]]; then
  echo "FAIL: could not determine tarball top-level directory" >&2
  exit 1
fi

# Use node to emit one JSON object per line: {slug, folder, strip, files[]}.
# "folder" is the entry's own top-level repo folder (first path segment of
# its `path` field), i.e. the same <skill-name> the README command extracts.
ENTRIES=$(node -e '
  const idx = JSON.parse(require("fs").readFileSync(process.argv[1], "utf8"));
  for (const [slug, v] of Object.entries(idx)) {
    const folder = v.path.split("/")[0];
    process.stdout.write(JSON.stringify({ slug, folder, strip: v.installStrip, files: v.files }) + "\n");
  }
' "$INDEX")

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  TOTAL=$((TOTAL + 1))

  slug=$(node -e 'console.log(JSON.parse(process.argv[1]).slug)' "$line")
  folder=$(node -e 'console.log(JSON.parse(process.argv[1]).folder)' "$line")
  strip=$(node -e 'console.log(JSON.parse(process.argv[1]).strip)' "$line")

  dest="$SCRATCH_DIR/install/$slug"
  mkdir -p "$dest"

  if ! tar -xzf "$TARBALL" --strip-components="$strip" -C "$dest" "$TOPDIR/$folder" 2>/dev/null; then
    echo "FAIL $slug: tar extraction of $TOPDIR/$folder failed" >&2
    FAIL=$((FAIL + 1))
    continue
  fi

  entry_ok=1
  while IFS= read -r relpath; do
    [[ -z "$relpath" ]] && continue
    # Each `files` path is repo-relative (e.g. "resume-tailor/scripts/x.py"),
    # i.e. it already excludes the tarball's "<repo>-<ref>/" prefix that
    # --strip-components also strips. So only (strip - 1) leading segments
    # need to come off here to land on the path within `dest`.
    rel_local=$(node -e '
      const parts = process.argv[1].split("/");
      process.stdout.write(parts.slice(Number(process.argv[2]) - 1).join("/"));
    ' "$relpath" "$strip")
    if [[ ! -e "$dest/$rel_local" ]]; then
      echo "FAIL $slug: missing $relpath after install (expected $dest/$rel_local)" >&2
      entry_ok=0
      continue
    fi
    base="$(basename "$rel_local")"
    if [[ "$base" == "SKILL.md" || "$rel_local" == agents/*.md ]]; then
      if ! head -n 1 "$dest/$rel_local" | grep -q '^---'; then
        echo "FAIL $slug: $relpath missing YAML frontmatter" >&2
        entry_ok=0
      fi
    fi
  done <<< "$(node -e 'console.log(JSON.parse(process.argv[1]).files.join("\n"))' "$line")"

  if [[ "$entry_ok" -eq 1 ]]; then
    echo "OK   $slug"
  else
    FAIL=$((FAIL + 1))
  fi
done <<< "$ENTRIES"

echo ""
echo "Total: $TOTAL, Failures: $FAIL"
[[ $FAIL -eq 0 ]]
