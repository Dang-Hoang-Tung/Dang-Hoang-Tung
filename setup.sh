#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# --- Zshrc ---
echo "\n# --- BEGIN user settings ---" >> ~/.zshrc
cat .zshrc >> ~/.zshrc
echo "# --- END user settings ---" >> ~/.zshrc

# --- Claude ---
curl -fsSL https://claude.ai/install.sh | bash
cp .claude/settings.json ~/.claude/settings.json
