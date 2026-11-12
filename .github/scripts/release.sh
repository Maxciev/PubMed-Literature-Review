#!/usr/bin/env bash
# Publish a GitHub release for a skill repo, with the .skill attached and marked Latest.
# Normally run by the repo's GitHub Actions workflow (templates/release.yml), which sets SRC_DIR to its
# checkout and GH_TOKEN to the workflow token. Cloud Claude sessions get HTTP 403 on release creation.
# Usage: release.sh <owner/repo> <version> [--dry-run]
#   e.g. release.sh Maxciev/PubMed-Literature-Review 1.2.0 --dry-run
# Expects at the repo root: <skill>/SKILL.md, <skill>.skill, CHANGELOG.md with "## <version> — <date>",
# CITATION.cff with "version: <version>". <skill> is the lowercased repo name.
set -euo pipefail
repo=${1:?owner/repo}; ver=${2:?version}; dry=${3:-}
name=$(basename "$repo" | tr '[:upper:]' '[:lower:]')
tag="v$ver"
work=$(mktemp -d "${TMPDIR:-/tmp}/skill-release.XXXXXX")
trap 'rm -rf "$work"' EXIT
fail() { echo "STOP: $*"; exit 1; }

echo "== 1. Prerequisites"
command -v gh >/dev/null || fail "gh missing (https://cli.github.com)"
gh --version | head -1
gh auth status >/dev/null 2>&1 || fail "gh not logged in: run gh auth login, then re-run"
if gh release view "$tag" --repo "$repo" >/dev/null 2>&1; then fail "release $tag already exists"; fi

if [ -n "${SRC_DIR:-}" ]; then
  echo "== 2. Use checkout $SRC_DIR"
  cd "$SRC_DIR"
else
  echo "== 2. Clone main"
  git clone -q --depth 1 "https://github.com/$repo.git" "$work/repo"
  cd "$work/repo"
fi

echo "== 3. Sanity checks"
grep -q "^version: $ver\$" CITATION.cff || fail "CITATION.cff is not version $ver"
grep -q "^## $ver " CHANGELOG.md || fail "CHANGELOG.md has no '## $ver' section"
[ -f "$name.skill" ] || fail "$name.skill not found"
unzip -l "$name.skill"
while IFS= read -r f; do
  unzip -p "$name.skill" "$f" | cmp -s - "$f" || fail "$f in $name.skill differs from the source (rebuild it)"
done < <(find "$name" -type f | LC_ALL=C sort)
inzip=$(unzip -Z1 "$name.skill" | grep -v '/$' | LC_ALL=C sort)
insrc=$(find "$name" -type f | LC_ALL=C sort)
[ "$inzip" = "$insrc" ] || fail "file list of $name.skill differs from $name/ (rebuild it)"
echo "zip matches $name/"

echo "== 4. Release notes"
notes="$work/notes.md"
awk -v v="## $ver " 'index($0,v)==1{on=1;next} on&&/^## /{exit} on' CHANGELOG.md > "$notes"
[ -s "$notes" ] || fail "empty release notes"
cat >> "$notes" <<EOF

## Install
Download \`$name.skill\` below, then in Claude: **Customize → Skills** (claude.ai/customize/skills) → **+** → **Create skill** → **Upload a skill**. If the file picker only accepts ZIP files, rename it to \`$name.zip\`.
EOF
cat "$notes"

if [ "$dry" = "--dry-run" ]; then echo "== DRY RUN: stopping before gh release create"; exit 0; fi

echo "== 5. Create release $tag (Latest)"
gh release create "$tag" "$name.skill" --repo "$repo" --target "${GITHUB_SHA:-main}" \
  --title "$tag" --notes-file "$notes" --latest

echo "== 6. Verify"
gh release view "$tag" --repo "$repo"
latest=$(gh release view --repo "$repo" --json tagName -q .tagName)
[ "$latest" = "$tag" ] || fail "Latest is $latest, not $tag"
curl -fsSL -o "$work/dl.skill" "https://github.com/$repo/releases/latest/download/$name.skill"
cmp "$work/dl.skill" "$name.skill" && echo "latest/download matches the local .skill"
curl -fsSL -o "$work/main.skill" "https://github.com/$repo/raw/main/$name.skill"
cmp "$work/main.skill" "$name.skill" && echo "raw/main matches the local .skill"
echo "RELEASE OK: https://github.com/$repo/releases/tag/$tag"
