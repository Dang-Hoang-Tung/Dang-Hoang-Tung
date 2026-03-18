#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# --- Shell rc files ---
for rc in ~/.zshrc ~/.bashrc; do
  echo "\n# --- BEGIN user settings ---" >> "$rc"
  cat .zshrc >> "$rc"
  echo "# --- END user settings ---" >> "$rc"
done

# --- Gitconfig ---
cp .gitconfig ~/.gitconfig

# --- Claude ---
curl -fsSL https://claude.ai/install.sh | bash
cp .claude/settings.json ~/.claude/settings.json
