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
# Every entry's skillFileUrl is pinned to the same ref. Read it through
# scripts/lib/index-ref.mjs rather than carrying a second copy of the URL
# regex here, so this script and check-index-additive.mjs cannot disagree
# about what index.json pins after an org or URL change.
#
# TEST_INSTALL_REF overrides it. CI sets it to the pushed tag on a tag build,
# so the tag users are actually told to install gets exercised against itself
# instead of against whatever ref the committed index.json still names.
if [[ -n "${TEST_INSTALL_REF:-}" ]]; then
  REF="$TEST_INSTALL_REF"
  echo "Ref overridden by TEST_INSTALL_REF"
else
  REF=$(node "$REPO_ROOT/scripts/lib/index-ref.mjs" index "$INDEX")
fi

if [[ -z "$REF" ]] || [[ ! "$REF" =~ ^[A-Za-z0-9._/-]+$ ]] || [[ "$REF" == *".."* ]]; then
  echo "Refusing to use unsafe ref extracted from index.json: '$REF'" >&2
  exit 2
fi

echo "Ref: $REF"

# --- 2. Download the tarball once --------------------------------------------

TARBALL="$SCRATCH_DIR/repo.tgz"
TARBALL_URL="https://codeload.github.com/skills-agents-co/skills-and-agents-library/tar.gz/$REF"

# TEST_INSTALL_TARBALL reuses an already-downloaded tarball for this same ref.
# test-install-negative.mjs sets it so driving this script once per fixture
# costs one codeload fetch for the whole suite instead of one per case.
if [[ -n "${TEST_INSTALL_TARBALL:-}" && -s "${TEST_INSTALL_TARBALL}" ]]; then
  TARBALL="$TEST_INSTALL_TARBALL"
  echo "Reusing tarball: $TARBALL"
elif ! curl -fsSL --connect-timeout 10 --max-time 120 -o "$TARBALL" "$TARBALL_URL"; then
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
    // slug is in this list because it is interpolated into the per-entry
    // destination directory, which is then handed to rm -rf: a slug of
    // "../.." would delete outside the scratch dir.
    const suspects = [slug, v.installFolder, v.skillFilePath, ...v.files];
    const bad = suspects.find((p) => typeof p !== "string" || TRAVERSAL.test(p));
    if (bad !== undefined) { console.log(["BAD", slug, "path traversal in manifest: " + bad].join("\t")); continue; }
    // The line protocol below is tab-separated, \x1f-joined, newline-terminated,
    // and git preserves all three characters in a filename. Reject them rather
    // than letting one entry split into two malformed records.
    const delim = suspects.find((p) => /[\n\t\x1f]/.test(p));
    if (delim !== undefined) { console.log(["BAD", slug, "manifest path contains a newline, tab, or \\x1f: " + JSON.stringify(delim)].join("\t")); continue; }
    console.log(["OK", slug, v.installFolder, v.skillFilePath, v.files.join(US)].join("\t"));
  }
' "$INDEX")

# --- 4. Install and verify each entry ----------------------------------------

extract_dir="$SCRATCH_DIR/out"
mkdir -p "$extract_dir"

# field1/field2/field3 carry different things depending on $status: for a BAD
# line field1 is the rejection reason and the rest are empty; for an OK line
# they are installFolder, skillFilePath, and the \x1f-joined files list. They
# are named positionally here and immediately given meaningful names below, so
# no one variable silently means two things inside the loop body.
while IFS=$'\t' read -r status slug field1 field2 field3; do
  [[ -z "$status" ]] && continue
  TOTAL=$((TOTAL + 1))

  if [[ "$status" == "BAD" ]]; then
    echo "FAIL $slug: $field1" >&2
    FAIL=$((FAIL + 1))
    continue
  fi

  installFolder="$field1"
  skillFilePath="$field2"
  IFS=$'\x1f' read -r -a files <<< "$field3"

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

  # Free this entry's extraction before the next one. Otherwise all 45
  # installed skill folders sit on disk until the EXIT trap fires.
  rm -rf "$dest"
done <<< "$MANIFEST"

echo ""
echo "Total: $TOTAL, Failures: $FAIL"
[[ $FAIL -eq 0 ]]
