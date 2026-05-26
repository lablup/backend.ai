export PS1="%F{green}%n@${BACKENDAI_CLUSTER_HOST:-main}%F{yellow}[${BACKENDAI_SESSION_NAME}]%f:%F{blue}%~%f\$ "

# Print the persistent-path notice only in interactive shells; otherwise stdout
# would corrupt SFTP/SCP/rsync subsystems that use the same channel as data.
if [[ -o interactive ]]; then
  if [[ -n "${BACKENDAI_PERSISTENT_PATHS:-}" ]]; then
    echo "\e[33m⚠ Only the following vfolder paths are persistent (all other files will be lost on session termination):\e[0m"
    local IFS=':'
    for _p in ${=BACKENDAI_PERSISTENT_PATHS}; do
      echo "\e[33m   - $_p\e[0m"
    done
  else
    echo "\e[33m⚠ No persistent storage mounted. All files will be lost when the session is terminated.\e[0m"
  fi
fi

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
