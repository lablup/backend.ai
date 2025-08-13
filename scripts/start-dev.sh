tmux new-session -d -s backendai-manager-dev \
    "./backend.ai mgr start-server --debug"

tmux new-session -d -s backendai-agent-dev \
    "./backend.ai ag start-server --debug"

tmux new-session -d -s backendai-storage-dev \
    "./backend.ai storage start-server --debug"

tmux new-session -d -s backendai-webserver-dev \
    "./backend.ai web start-server --debug"

tmux new-session -d -s backendai-wsproxy-dev \
    "./backend.ai wsproxy start-server --debug"
