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
# Four runs:
#   1. The block verbatim (skill="resume-tailor"), the flat-layout case.
#   2. The block with skill="ads-copilot" plus the documented follow-up mv,
#      the nested-layout case, asserting SKILL.md ends up at the top of the
#      install directory where Claude Code looks for it.
#   3. The block with skill="ceo-todo" plus the documented agent cp step,
#      asserting the agent file lands in ~/.claude/agents/ where Claude Code
#      loads subagents from. Without this the Spec's "installing an agent slug
#      succeeds by the documented command" criterion had no test behind it.
#   4. A NEGATIVE run: the block with an empty skill name must refuse to
#      proceed, because the unguarded version turns its own `rm -rf` into a
#      delete of the user's entire ~/.claude/skills/ directory.
#
# Needs network access (each positive run downloads the pinned tarball).
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
    // The loop above already asserted this file exists and is non-empty (it is
    // one of entry.files), so re-checking existence here could never fire. What
    // is NOT covered above is that it is the skill file Claude Code can load,
    // so that is what is asserted: real frontmatter, terminated, with a name.
    const skillMd = layout === "nested" ? dir + "/SKILL.md" : dir + "/" + entry.skillFilePath;
    const head = fs.existsSync(skillMd) ? fs.readFileSync(skillMd, "utf8") : "";
    if (!head.startsWith("---\n")) missing.push(skillMd + " (no opening frontmatter fence)");
    else if (head.indexOf("\n---", 4) === -1) missing.push(skillMd + " (frontmatter never terminates)");
    else if (!/^name:\s*\S/m.test(head.slice(0, head.indexOf("\n---", 4)))) missing.push(skillMd + " (frontmatter has no name)");
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
# The block downloads into its own mktemp -d, never into HOME, so globbing for
# a *.tgz under HOME asserted something the command could not do either way.
# What it CAN get wrong is leaving something behind in HOME that is not the
# install itself, so that is what is checked: after a successful run, HOME
# holds exactly ".claude" and nothing else.
leftovers=$(cd "$HOME1" && ls -A | grep -v '^\.claude$' || true)
if [[ -n "$leftovers" ]]; then
  echo "FAIL: the documented install left files in HOME besides .claude: $leftovers" >&2
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

# --- Run 3: the documented agent cp step -------------------------------------
#
# The Spec's "installing an agent slug succeeds by the documented command"
# criterion had no test behind it. Claude Code loads subagents from
# ~/.claude/agents/, so an agent that never lands there is not installed no
# matter how well the skill folder extracted.

echo "--- Run 3: the documented agent install (ceo-todo + the cp step) ---"
HOME3="$SCRATCH_DIR/home3"
run_block "ceo-todo" "$HOME3"

AGENTBLOCK="$SCRATCH_DIR/agent-block.sh"
node -e '
  const fs = require("fs");
  const readme = fs.readFileSync(process.argv[1], "utf8");
  const fences = readme.match(/```bash\n[\s\S]*?\n```/g) || [];
  const block = fences.find((b) => b.includes("cp ") && b.includes(".claude/agents"));
  if (!block) {
    console.error("No fenced bash block in README.md documents the agent cp step.");
    process.exit(1);
  }
  fs.writeFileSync(process.argv[2], block.replace(/^```bash\n/, "").replace(/\n```$/, "") + "\n");
' "$README" "$AGENTBLOCK"
echo "Extracted README agent-install block:"
sed 's/^/  | /' "$AGENTBLOCK"
( HOME="$HOME3" bash "$AGENTBLOCK" )

AGENT_DEST="$HOME3/.claude/agents/ceo-todo-daily.md"
if [[ ! -s "$AGENT_DEST" ]]; then
  echo "FAIL: the documented agent step did not leave ceo-todo-daily.md in ~/.claude/agents/" >&2
  FAIL=$((FAIL + 1))
elif ! head -n 1 "$AGENT_DEST" | grep -q '^---'; then
  echo "FAIL: the installed agent file has no frontmatter, so it will not register" >&2
  FAIL=$((FAIL + 1))
else
  echo "OK   ceo-todo-daily: agent file installed to ~/.claude/agents/ with frontmatter"
fi
echo ""

# --- Run 4: the guard on $skill actually fires -------------------------------
#
# The install removes "$HOME/.claude/skills/$skill" before copying. An empty
# $skill turns that line into `rm -rf "$HOME/.claude/skills/"`, deleting every
# skill the user has installed, and tar happily "succeeds" beforehand because
# an empty member prefix matches every member in the archive. The guard has to
# fail closed, and the pre-existing install has to survive.

echo "--- Run 4: an empty skill name is refused before anything is deleted ---"
HOME4="$SCRATCH_DIR/home4"
mkdir -p "$HOME4/.claude/skills/already-installed"
echo "sentinel" > "$HOME4/.claude/skills/already-installed/SKILL.md"

BADBLOCK="$SCRATCH_DIR/bad-skill.sh"
sed 's|^  skill="[^"]*"|  skill=""|' "$BLOCK" > "$BADBLOCK"

set +e
( HOME="$HOME4" bash "$BADBLOCK" ) > "$SCRATCH_DIR/bad-skill.out" 2>&1
bad_status=$?
set -e

if [[ $bad_status -eq 0 ]]; then
  echo "FAIL: the documented install accepted an empty skill name (exit 0)" >&2
  FAIL=$((FAIL + 1))
elif ! grep -q "plain folder name" "$SCRATCH_DIR/bad-skill.out"; then
  echo "FAIL: an empty skill name failed, but not via the guard's own message" >&2
  sed 's/^/       /' "$SCRATCH_DIR/bad-skill.out" >&2
  FAIL=$((FAIL + 1))
elif [[ ! -s "$HOME4/.claude/skills/already-installed/SKILL.md" ]]; then
  echo "FAIL: an empty skill name destroyed an unrelated installed skill" >&2
  FAIL=$((FAIL + 1))
else
  echo "OK   empty skill name refused, and the pre-existing install survived"
fi

echo ""
echo "Total: 3 documented installs + 1 refused, Failures: $FAIL"
[[ $FAIL -eq 0 ]]
