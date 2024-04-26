#!/bin/sh

# Use current Shell as API Mode
tmux rename-window API-Mode

# Session Mode
tmux new-window
tmux rename-window Session-Mode

# Manager
tmux new-window
tmux rename-window manager

# Agent
tmux new-window
tmux rename-window agent

# Storage
tmux new-window
tmux rename-window storage

# Web UI
tmux new-window
tmux rename-window web

sleep 2

tmux send-keys -t manager './backend.ai mgr start-server --debug' Enter
tmux send-keys -t agent './backend.ai ag start-server --debug' Enter
tmux send-keys -t storage './py -m ai.backend.storage.server' Enter
tmux send-keys -t web './py -m ai.backend.web.server' Enter
tmux send-keys -t API-Mode 'source env-local-admin-api.sh' Enter
tmux send-keys -t Session-Mode 'source env-local-admin-session.sh' Enter
