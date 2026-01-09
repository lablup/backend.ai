tmux new-session -d -s backendai-manager-dev \
    "./backend.ai mgr start-server --debug"

tmux new-session -d -s backendai-agent-dev \
    "./backend.ai ag start-server --debug"

tmux new-session -d -s backendai-storage-dev \
    "./backend.ai storage start-server --debug"

tmux new-session -d -s backendai-webserver-dev \
    "./backend.ai web start-server --debug"

tmux new-session -d -s backendai-appproxy-dev

tmux new-window -t backendai-appproxy-dev -n "coordinator"
tmux send-keys "./backend.ai app-proxy-coordinator start-server --debug" C-m

tmux new-window -t backendai-appproxy-dev -n "worker"
tmux send-keys "./backend.ai app-proxy-worker start-server --debug" C-m
