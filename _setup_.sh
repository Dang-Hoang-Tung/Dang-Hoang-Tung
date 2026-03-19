#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# --- Shell rc files ---
for rc in ~/.zshrc ~/.bashrc; do
  printf "\n# --- BEGIN user settings ---\n" >> "$rc"
  cat .zshrc >> "$rc"
  printf "# --- END user settings ---\n" >> "$rc"
done

# --- Gitconfig ---
cp .gitconfig ~/.gitconfig

# --- Claude ---
cp .claude/settings.json ~/.claude/settings.json
rm -rf ~/.claude/skills/ && cp -r .claude/skills/ ~/.claude/skills/
