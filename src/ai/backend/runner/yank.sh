#!/bin/bash
# This is a simplified and modified version of https://github.com/samoshkin/tmux-config/blob/af2efd9/tmux/yank.sh
# to make it working with no-clear, no-cancel variants of the tmux copy-pipe commands
set -eu

tmux=/opt/kernel/tmux

# get data either form stdin or from file
buf=$(cat "$@")

# Copy via OSC 52 ANSI escape sequence to controlling terminal
buflen=$( printf %s "$buf" | wc -c )

# https://sunaku.github.io/tmux-yank-osc52.html
# The maximum length of an OSC 52 escape sequence is 100_000 bytes, of which
# 7 bytes are occupied by a "\033]52;c;" header, 1 byte by a "\a" footer, and
# 99_992 bytes by the base64-encoded result of 74_994 bytes of copyable text
maxlen=74994

# warn if exceeds maxlen
if [ "$buflen" -gt "$maxlen" ]; then
  printf "yank.sh: input is too long (%d bytes, max: $maxlen bytes)" "$(( buflen - maxlen ))" >&2
fi

# build up OSC 52 ANSI escape sequence
esc="\033]52;c;$( printf %s "$buf" | head -c $maxlen | base64 | tr -d '\r\n' )\a"

# resolve target terminal to send escape sequence
pane_active_tty=$("$tmux" list-panes -F "#{pane_active} #{pane_tty}" | awk '$1=="1" { print $2 }')
target_tty="${SSH_TTY:-$pane_active_tty}"

printf "$esc" > "$target_tty"
