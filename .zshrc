# Git aliases
alias gs="git status"
alias ga="git add"
alias gaa="git add --all"
alias gc="git commit -m"
alias gca="git commit -am"
alias gps="git push"
alias gpl="git pull"
alias gl="git log --oneline --graph --decorate"
alias gd="git diff"
alias gco="git checkout"
alias gcob="git checkout -b"
alias gb="git branch"
alias gst="git stash"
alias gstp="git stash pop"
gcnoci() { git commit -m "$* [skip ci]"; }
alias gwtl="git worktree list"
alias gwta="git worktree add"
alias gwtr="git worktree remove"
alias gwtp="git worktree prune"

# Add ~/.local/bin to PATH
export PATH="$HOME/.local/bin:$PATH"
