# My dev set up

Copy Claude settings into global:

```sh
cp -r .claude ~/.claude
```

Copy .zshrc settings into global:

```sh
echo "\n# --- BEGIN user settings ---" >> ~/.zshrc
cat .zshrc >> ~/.zshrc
echo "# --- END user settings ---" >> ~/.zshrc
source ~/.zshrc
```
