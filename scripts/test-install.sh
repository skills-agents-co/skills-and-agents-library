#!/usr/bin/env bash
# test-install.sh
#
# Installs every index.json entry the way the README documents it: one pinned
# tarball, extracted per entry into ~/.claude/skills/<installFolder>-shaped
# layout, then a strict check that the entry's manifest (installFolder,
# skillFilePath, files) actually arrived on disk. Exits non-zero on the first
# entry whose manifest does not check out, or on the last line's failure count.
#
# Usage:
#   bash scripts/test-install.sh [path/to/index.json]
#
# The optional first argument overrides which index.json is loaded, used by
# scripts/test-install-negative.mjs to point this script at doctored fixture
# copies without touching the real one.

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INDEX="${1:-$REPO_ROOT/index.json}"

if [[ ! -f "$INDEX" ]]; then
  echo "index.json not found at $INDEX" >&2
  echo "Run: node scripts/build-index.mjs --tag <tag>" >&2
  exit 2
fi

# Deliberately NOT named TMPDIR: that is the POSIX temp-directory variable, so
# assigning it redirects every child process's own temp writes (curl, tar,
# node) into this script's scratch dir, which the trap below then deletes out
# from under them. SCRATCH_DIR is ours alone.
SCRATCH_DIR=$(mktemp -d)
# Single-quoted so the trap expands $SCRATCH_DIR at fire time, not at trap-set
# time — a scratch path containing a space stays one argument to rm -rf.
trap 'rm -rf "$SCRATCH_DIR"' EXIT

FAIL=0
TOTAL=0

# --- 1. Read and validate the ref out of index.json --------------------------
#
# Every entry's skillFileUrl is pinned to the same ref. Extract it from the
# first entry rather than typing one, so this script and README.md can never
# drift from what index.json actually pins (that agreement is asserted
# separately, in CI, by comparing README.md's fenced block to this same
# field). Reject anything that is not a git-ref-safe token, and explicitly
# reject ".." so a doctored index.json cannot steer the codeload fetch
# outside the intended ref.
REF=$(node -e '
  const idx = JSON.parse(require("fs").readFileSync(process.argv[1], "utf8"));
  const first = Object.values(idx)[0];
  if (!first || typeof first.skillFileUrl !== "string") {
    console.error("index.json has no entries with a skillFileUrl");
    process.exit(1);
  }
  const m = first.skillFileUrl.match(
    /^https:\/\/raw\.githubusercontent\.com\/skills-agents-co\/skills-and-agents-library\/([^/]+)\//
  );
  if (!m) {
    console.error("could not extract a ref from skillFileUrl: " + first.skillFileUrl);
    process.exit(1);
  }
  process.stdout.write(m[1]);
' "$INDEX")

if [[ -z "$REF" ]] || [[ ! "$REF" =~ ^[A-Za-z0-9._/-]+$ ]] || [[ "$REF" == *".."* ]]; then
  echo "Refusing to use unsafe ref extracted from index.json: '$REF'" >&2
  exit 2
fi

echo "Ref: $REF"

# --- 2. Download the tarball once --------------------------------------------

TARBALL="$SCRATCH_DIR/repo.tgz"
TARBALL_URL="https://codeload.github.com/skills-agents-co/skills-and-agents-library/tar.gz/$REF"

if ! curl -fsSL --connect-timeout 10 --max-time 120 -o "$TARBALL" "$TARBALL_URL"; then
  echo "Failed to download tarball: $TARBALL_URL" >&2
  exit 1
fi

# The tarball's top directory is the tag with its leading "v" stripped (e.g.
# "skills-and-agents-library-1.27.0" for ref "v1.27.0"), not something
# composed from the ref, so it has to be read out of the archive listing.
TOPDIR=$(tar -tzf "$TARBALL" | grep -m1 '/' | cut -d/ -f1)
if [[ -z "$TOPDIR" ]]; then
  echo "Could not determine the tarball's top directory" >&2
  exit 1
fi

# --- 3. Emit one manifest line per entry, validated in one node call --------
#
# Each line is either:
#   OK\t<slug>\t<installFolder>\t<skillFilePath>\t<files, \x1f-joined>
#   BAD\t<slug>\t<reason>
# so the rest of this script never re-parses JSON per entry or per file.
MANIFEST=$(node -e '
  const idx = JSON.parse(require("fs").readFileSync(process.argv[1], "utf8"));
  const US = "\x1f";
  const TRAVERSAL = /(^\/)|(^|\/)\.\.(\/|$)/;
  for (const [slug, v] of Object.entries(idx)) {
    if (!("files" in v)) { console.log(["BAD", slug, "index.json entry has no files key"].join("\t")); continue; }
    if (!Array.isArray(v.files)) { console.log(["BAD", slug, "files is not an array"].join("\t")); continue; }
    if (v.files.length === 0) { console.log(["BAD", slug, "files array is empty"].join("\t")); continue; }
    if (!v.installFolder || typeof v.installFolder !== "string") { console.log(["BAD", slug, "missing installFolder"].join("\t")); continue; }
    if (!v.skillFilePath || typeof v.skillFilePath !== "string") { console.log(["BAD", slug, "missing skillFilePath"].join("\t")); continue; }
    const suspects = [v.installFolder, v.skillFilePath, ...v.files];
    const bad = suspects.find((p) => typeof p !== "string" || TRAVERSAL.test(p));
    if (bad !== undefined) { console.log(["BAD", slug, "path traversal in manifest: " + bad].join("\t")); continue; }
    console.log(["OK", slug, v.installFolder, v.skillFilePath, v.files.join(US)].join("\t"));
  }
' "$INDEX")

# --- 4. Install and verify each entry ----------------------------------------

extract_dir="$SCRATCH_DIR/out"
mkdir -p "$extract_dir"

while IFS=$'\t' read -r status slug a b c; do
  [[ -z "$status" ]] && continue
  TOTAL=$((TOTAL + 1))

  if [[ "$status" == "BAD" ]]; then
    echo "FAIL $slug: $a" >&2
    FAIL=$((FAIL + 1))
    continue
  fi

  installFolder="$a"
  skillFilePath="$b"
  IFS=$'\x1f' read -r -a files <<< "$c"

  dest="$extract_dir/$slug"
  rm -rf "$dest"
  mkdir -p "$dest"

  tar_err="$SCRATCH_DIR/tar-err.log"
  if ! tar -xzf "$TARBALL" --strip-components=2 --no-same-owner --no-same-permissions \
      -C "$dest" "$TOPDIR/$installFolder" 2>"$tar_err"; then
    echo "FAIL $slug: tar extraction failed for $TOPDIR/$installFolder" >&2
    sed 's/^/       tar: /' "$tar_err" >&2
    FAIL=$((FAIL + 1))
    continue
  fi

  entry_ok=1
  reason=""

  # A nested skill (ads-copilot, financial-pulse) leaves its SKILL.md two
  # levels down (e.g. skills/ads-copilot/SKILL.md). The documented install
  # then moves it to the top of the install directory so Claude Code's
  # single-level SKILL.md discovery finds it, with its references/ and
  # scripts/ left beside it where its own text expects them.
  skill_basename="$(basename -- "$skillFilePath")"
  if [[ "$skill_basename" == "SKILL.md" && "$skillFilePath" != "SKILL.md" ]]; then
    if [[ -f "$dest/$skillFilePath" ]]; then
      mv "$dest/$skillFilePath" "$dest/SKILL.md"
    fi
    resolved_skill_path="SKILL.md"
  else
    resolved_skill_path="$skillFilePath"
  fi

  # Every path the manifest names must exist as a non-empty regular file.
  # Existence alone (-e) would pass for a directory or a zero-byte file left
  # by a truncated extraction, so use -s (exists and non-empty).
  for f in "${files[@]}"; do
    [[ -z "$f" ]] && continue
    # The entry's own SKILL.md is checked at its resolved (possibly moved)
    # location, matching what the documented install actually leaves behind.
    if [[ "$f" == "$skillFilePath" && "$resolved_skill_path" != "$skillFilePath" ]]; then
      check_path="$dest/$resolved_skill_path"
    else
      check_path="$dest/$f"
    fi
    if [[ ! -s "$check_path" ]]; then
      entry_ok=0
      reason="missing or empty file: $f"
      break
    fi
  done

  if [[ "$entry_ok" == "1" ]]; then
    skill_dest="$dest/$resolved_skill_path"
    if [[ ! -f "$skill_dest" ]] || ! head -n 1 "$skill_dest" | grep -q '^---'; then
      entry_ok=0
      reason="skillFilePath destination missing or has no frontmatter: $resolved_skill_path"
    fi
  fi

  if [[ "$entry_ok" == "1" ]]; then
    echo "OK   $slug"
  else
    echo "FAIL $slug: $reason" >&2
    FAIL=$((FAIL + 1))
  fi
done <<< "$MANIFEST"

echo ""
echo "Total: $TOTAL, Failures: $FAIL"
[[ $FAIL -eq 0 ]]
