#!/usr/bin/env bash
# test-readme-install.sh
#
# Runs the install command README.md actually documents, as written, and
# asserts the skill arrives complete.
#
# scripts/test-install.sh is a bash reimplementation of the same shape. It can
# stay green while the documented text drifts away from it, and the documented
# text is the deliverable: it is what a stranger pastes into a terminal. This
# script closes that gap by extracting the fenced block out of README.md and
# executing it, with $HOME pointed at a scratch directory so nothing touches
# the developer's real ~/.claude.
#
# Two runs:
#   1. The block verbatim (skill="resume-tailor"), the flat-layout case.
#   2. The block with skill="ads-copilot" plus the documented follow-up mv,
#      the nested-layout case, asserting SKILL.md ends up at the top of the
#      install directory where Claude Code looks for it.
#
# Needs network access (each run downloads the pinned tarball).
#
# Usage: bash scripts/test-readme-install.sh

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INDEX="$REPO_ROOT/index.json"
README="$REPO_ROOT/README.md"

SCRATCH_DIR=$(mktemp -d)
trap 'rm -rf "$SCRATCH_DIR"' EXIT

FAIL=0

# --- Extract the documented install block from README.md ---------------------

BLOCK="$SCRATCH_DIR/install-block.sh"
node -e '
  const fs = require("fs");
  const readme = fs.readFileSync(process.argv[1], "utf8");
  const fences = readme.match(/```bash\n[\s\S]*?\n```/g) || [];
  const block = fences.find((b) => b.includes("codeload.github.com/skills-agents-co/skills-and-agents-library"));
  if (!block) {
    console.error("No fenced bash block in README.md fetches the codeload tarball.");
    process.exit(1);
  }
  fs.writeFileSync(process.argv[2], block.replace(/^```bash\n/, "").replace(/\n```$/, "") + "\n");
' "$README" "$BLOCK"

echo "Extracted README install block:"
sed 's/^/  | /' "$BLOCK"
echo ""

# --- Run 1: verbatim ---------------------------------------------------------

run_block() {
  # $1 = skill to install ("" means leave the block untouched), $2 = HOME
  local skill="$1" home="$2" script="$SCRATCH_DIR/run.sh"
  mkdir -p "$home"
  if [[ -n "$skill" ]]; then
    # The block's own comment tells the reader to change this line and nothing
    # else, so that is the only substitution made here.
    sed "s|^  skill=\"[^\"]*\"|  skill=\"$skill\"|" "$BLOCK" > "$script"
  else
    cp "$BLOCK" "$script"
  fi
  ( HOME="$home" bash "$script" )
}

check_manifest() {
  # $1 = index slug, $2 = install directory, $3 = "flat" or "nested"
  local slug="$1" dir="$2" layout="$3"
  node -e '
    const fs = require("fs");
    const [indexPath, slug, dir, layout] = process.argv.slice(1);
    const entry = JSON.parse(fs.readFileSync(indexPath, "utf8"))[slug];
    if (!entry) { console.error("no index entry for " + slug); process.exit(1); }
    let missing = [];
    for (const f of entry.files) {
      // In the nested layout the documented follow-up mv lifts SKILL.md to the
      // top of the install directory, so it is checked there instead.
      const p = (layout === "nested" && f === entry.skillFilePath) ? "SKILL.md" : f;
      const full = dir + "/" + p;
      if (!fs.existsSync(full) || fs.statSync(full).size === 0) missing.push(p);
    }
    const skillMd = layout === "nested" ? dir + "/SKILL.md" : dir + "/" + entry.skillFilePath;
    if (!fs.existsSync(skillMd)) missing.push(skillMd + " (skill file)");
    else if (!fs.readFileSync(skillMd, "utf8").startsWith("---")) missing.push(skillMd + " (no frontmatter)");
    if (missing.length) {
      console.error("FAIL " + slug + ": " + missing.length + " missing or empty: " + missing.slice(0, 5).join(", "));
      process.exit(1);
    }
    console.log("OK   " + slug + ": all " + entry.files.length + " manifest files arrived, SKILL.md has frontmatter");
  ' "$INDEX" "$slug" "$dir" "$layout"
}

echo "--- Run 1: the block verbatim (flat layout) ---"
HOME1="$SCRATCH_DIR/home1"
run_block "" "$HOME1"
if ! check_manifest "resume-tailor" "$HOME1/.claude/skills/resume-tailor" flat; then
  FAIL=$((FAIL + 1))
fi
if compgen -G "$SCRATCH_DIR/home1/*.tgz" > /dev/null; then
  echo "FAIL: the documented install left a tarball behind in HOME" >&2
  FAIL=$((FAIL + 1))
fi
echo ""

echo "--- Run 2: nested layout (ads-copilot) plus the documented mv ---"
HOME2="$SCRATCH_DIR/home2"
run_block "ads-copilot" "$HOME2"

# The documented follow-up for the two nested skills, run the same way.
MVBLOCK="$SCRATCH_DIR/mv-block.sh"
node -e '
  const fs = require("fs");
  const readme = fs.readFileSync(process.argv[1], "utf8");
  // The nested follow-up lives in a blockquoted fence, so each line carries a
  // leading "> ". Strip it, then take the fenced bash block that does the mv.
  const unquoted = readme.split("\n").map((l) => l.replace(/^> ?/, "")).join("\n");
  const fences = unquoted.match(/```bash\n[\s\S]*?\n```/g) || [];
  const block = fences.find((b) => b.includes("mv ") && b.includes("SKILL.md"));
  if (!block) {
    console.error("No fenced bash block in README.md documents the nested SKILL.md mv.");
    process.exit(1);
  }
  fs.writeFileSync(process.argv[2], block.replace(/^```bash\n/, "").replace(/\n```$/, "") + "\n");
' "$README" "$MVBLOCK"
echo "Extracted README nested-skill follow-up:"
sed 's/^/  | /' "$MVBLOCK"
( HOME="$HOME2" bash "$MVBLOCK" )

if ! check_manifest "ads-copilot" "$HOME2/.claude/skills/ads-copilot" nested; then
  FAIL=$((FAIL + 1))
fi

echo ""
echo "Total: 2 documented installs, Failures: $FAIL"
[[ $FAIL -eq 0 ]]
