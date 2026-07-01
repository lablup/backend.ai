export PS1="\[\033[01;32m\]\u@${BACKENDAI_CLUSTER_HOST:-main}\[\033[01;33m\][${BACKENDAI_SESSION_NAME}]\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ "

# Print the persistent-path notice only in interactive shells; otherwise stdout
# would corrupt SFTP/SCP/rsync subsystems that use the same channel as data.
if [[ $- == *i* ]]; then
  if [[ -n "${BACKENDAI_PERSISTENT_PATHS:-}" ]]; then
    echo -e "\e[33m⚠ Only the following vfolder paths are persistent (all other files will be lost on session termination):\e[0m"
    IFS=':' read -ra _paths <<< "$BACKENDAI_PERSISTENT_PATHS"
    for _p in "${_paths[@]}"; do
      echo -e "\e[33m   - $_p\e[0m"
    done
  else
    echo -e "\e[33m⚠ No persistent storage mounted. All files will be lost when the session is terminated.\e[0m"
  fi
fi

if [[ `uname` == "Linux"  ]]; then
    alias ls="ls --color"
fi
alias ll="ls -al"
alias l="ls -a"
