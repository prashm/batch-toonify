#!/usr/bin/env bash
# Build a release zip and publish it as a GitHub Release (downloads are counted by GitHub).
# Usage: ./scripts/release.sh 1.0.0
set -euo pipefail

VERSION="${1:?Usage: ./scripts/release.sh <version>, e.g. 1.0.0}"
TAG="v${VERSION}"
NAME="batch-toonify-${TAG}"
ZIP="dist/${NAME}.zip"

cd "$(dirname "$0")/.."

# Only release committed, pushed code from main.
[[ "$(git branch --show-current)" == "main" ]] || { echo "Switch to main first."; exit 1; }
[[ -z "$(git status --porcelain)" ]] || { echo "Commit or stash your changes first."; exit 1; }
git fetch -q origin main
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]] || { echo "Push main to GitHub first."; exit 1; }
if git rev-parse -q --verify "refs/tags/${TAG}" >/dev/null; then echo "Tag ${TAG} already exists."; exit 1; fi

# Zip only tracked files (honours export-ignore in .gitattributes), inside a versioned folder.
mkdir -p dist
git archive --format=zip --prefix="${NAME}/" -o "${ZIP}" HEAD
echo "Built ${ZIP}:"
unzip -l "${ZIP}"

gh release create "${TAG}" "${ZIP}" \
  --title "batch-toonify ${TAG}" \
  --generate-notes
echo "Published: $(gh release view "${TAG}" --json url -q .url)"
