export PS1="%F{green}%n@${BACKENDAI_CLUSTER_HOST:-main}%F{yellow}[${BACKENDAI_SESSION_NAME}]%f:%F{blue}%~%f\$ "

# Set up autocompletion
autoload -Uz compinit
compinit
zstyle ':completion:*' completer _expand _complete _correct _approximate
zstyle ':completion:*' menu select=2
eval "$(dircolors -b)"
zstyle ':completion:*:default' list-colors ${(s.:.)LS_COLORS}

# Aliases
if [[ `uname` == "Linux"  ]]; then
    alias ls="ls --color"
fi
alias ll="ls -al"
alias l="ls -a"
