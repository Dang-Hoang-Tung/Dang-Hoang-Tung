# My dev set up

## Zshrc

Copy .zshrc settings into global:

```sh
echo "\n# --- BEGIN user settings ---" >> ~/.zshrc
cat .zshrc >> ~/.zshrc
echo "# --- END user settings ---" >> ~/.zshrc
source ~/.zshrc
```

## Claude

Download Claude Code:

```sh
curl -fsSL https://claude.ai/install.sh | bash
```

Copy Claude settings into global:

```sh
cp -r .claude ~/.claude
```
