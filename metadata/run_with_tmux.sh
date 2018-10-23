#!/usr/bin/env bash

# window=${session}:0
# pane=${window}.4
# tmux send-keys -t "$pane" C-z 'some -new command' Enter
# tmux select-pane -t "$pane"
# tmux select-window -t "$window"
# tmux attach-session -t "$session"

aliases() {
  case $( uname -s ) in
    Linux)
          _tail=tail
          ;;
    Darwin)
          _tail=gtail
          ;;
  esac
}

command_exists() {
  command -v "$@" > /dev/null 2>&1
}

check_dependency() {
  if ! command_exists $1 ; then
    echo "Error: please install command: $1"
    exit 1
  fi
}

# Check dependencies
aliases
check_dependency $_tail

# Setup tmux
session=metadata_ingestion
main_window=${session}:0

# Draw windows

tmux new-session -d -s "$session" ;
#tmux set -g pane-border-format "#P: #{pane_current_command}" # for debug
#tmux setw pane-border-status top # for debug
tmux split-window -t "${main_window}.0" -h
tmux split-window -t "${main_window}.1" -v
tmux split-window -t "${main_window}.0" -v -p 60
tmux split-window -t "${main_window}" -v -p 30

# Resulting layout
# +-----------------+----------------+
# |                 |                |
# |        0        |                |
# |                 |       1        |
# +-----------------+                |
# |                 |                |
# |        3        +----------------+
# |                 |                |
# +-----------------+       2        |
# |        4        |                |
# |                 |                |
# +-----------------+----------------+

# Run commands
compose_pane="${main_window}.0"
stream_log_pane="${main_window}.1"
cache_log_pane="${main_window}.2"
ignore_files_panel="${main_window}.3"
debug_console="${main_window}.4"
tmux send-keys -t "$compose_pane" C-z 'sudo umount /tmp/onedata ; source envs ; sudo -E docker-compose up' Enter
tmux send-keys -t "$stream_log_pane" C-z "$_tail -F logs/stream.log" Enter
tmux send-keys -t "$cache_log_pane" C-z "$_tail  -F logs/cache.db" Enter
tmux send-keys -t "$ignore_files_panel" C-z "$_tail  -F logs/ignore_forever_files" Enter
tmux select-pane -t "$debug_console" 

tmux at