export PS1="\[\033[01;32m\]\u@${BACKENDAI_CLUSTER_HOST:-main}\[\033[01;33m\][${BACKENDAI_SESSION_NAME}]\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ "

if [[ `uname` == "Linux"  ]]; then
    alias ls="ls --color"
fi
alias ll="ls -al"
alias l="ls -a"
