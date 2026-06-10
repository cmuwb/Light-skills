#!/usr/bin/env bash
# Light installer (macOS / Linux)
# Links Light's 28 skills + shared knowledge bases into Claude Code and/or Codex.
# Usage:  ./install.sh            # installs into both clients
#         ./install.sh claude
#         ./install.sh codex
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLIENT="${1:-both}"

install_into() {
  local skills_dir="$1"
  local parent
  parent="$(dirname "$skills_dir")"
  mkdir -p "$skills_dir"
  local n=0
  for d in "$REPO"/skills/light-*/; do
    local name
    name="$(basename "$d")"
    rm -rf "$skills_dir/$name"
    ln -s "$d" "$skills_dir/$name"
    [ -f "$skills_dir/$name/SKILL.md" ] && n=$((n+1))
  done
  # shared libraries as siblings so skills' relative paths resolve
  rm -rf "$parent/databases" "$parent/code_assets"
  ln -s "$REPO/databases"   "$parent/databases"
  ln -s "$REPO/code_assets" "$parent/code_assets"
  echo "  $skills_dir  ->  $n/28 skills"
}

if [ "$CLIENT" = both ] || [ "$CLIENT" = claude ]; then
  echo 'Claude Code:'
  install_into "$HOME/.claude/skills"
fi
if [ "$CLIENT" = both ] || [ "$CLIENT" = codex ]; then
  echo 'Codex:'
  install_into "$HOME/.agents/skills"
fi
echo 'Done. Restart your client to discover the skills.'
