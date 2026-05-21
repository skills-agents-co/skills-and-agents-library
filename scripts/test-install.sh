#!/usr/bin/env bash
# test-install.sh
#
# Reads index.json, runs the real catalog install pattern from a clean tmp dir
# for every entry, and verifies each downloaded file starts with YAML frontmatter.
# Exits non-zero on first failure.

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INDEX="$REPO_ROOT/index.json"

if [[ ! -f "$INDEX" ]]; then
  echo "index.json not found at $INDEX" >&2
  echo "Run: node scripts/build-index.mjs --tag <tag>" >&2
  exit 2
fi

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

FAIL=0
TOTAL=0

# Use node to emit "slug\turl" lines so we don't depend on jq.
ENTRIES=$(node -e '
  const idx = JSON.parse(require("fs").readFileSync(process.argv[1], "utf8"));
  for (const [slug, v] of Object.entries(idx)) {
    process.stdout.write(slug + "\t" + v.skillFileUrl + "\n");
  }
' "$INDEX")

while IFS=$'\t' read -r slug url; do
  [[ -z "$slug" ]] && continue
  TOTAL=$((TOTAL + 1))
  dest="$TMPDIR/$slug/SKILL.md"
  mkdir -p "$(dirname "$dest")"
  if ! curl -fsSL -o "$dest" "$url"; then
    echo "FAIL $slug: curl failed for $url" >&2
    FAIL=$((FAIL + 1))
    continue
  fi
  if ! head -n 1 "$dest" | grep -q '^---'; then
    echo "FAIL $slug: missing frontmatter at $url" >&2
    FAIL=$((FAIL + 1))
    continue
  fi
  echo "OK   $slug"
done <<< "$ENTRIES"

echo ""
echo "Total: $TOTAL, Failures: $FAIL"
[[ $FAIL -eq 0 ]]
