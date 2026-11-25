#!/usr/bin/env bash
# Copy only the allowlisted website files into ./site for Cloudflare Pages.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ALLOW="$ROOT/scripts/pages-allowlist.txt"
DEST="$ROOT/site"
rm -rf "$DEST"
mkdir -p "$DEST"
while IFS= read -r line; do
  [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
  src="$ROOT/$line"
  if [[ ! -f "$src" ]]; then
    echo "missing: $line" >&2
    exit 1
  fi
  mkdir -p "$DEST/$(dirname "$line")"
  cp -a "$src" "$DEST/$line"
  echo "copied $line"
done < "$ALLOW"
echo "Publish directory: $DEST"
