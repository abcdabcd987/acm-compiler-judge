#!/bin/bash

sleep 30
ip=$(hostname -I | sed 's/10.0.2.15//g' | awk '{print $1}')
cd "$(dirname "$0")"
git pull
sed -i '/JUDGE_NAME =/d' settings.py
echo "JUDGE_NAME = 'judge.$ip'" >> settings.py

tmux new-session -d -s judge
tmux send-keys -t judge:0 "while true; do ./judge/judge.py; sleep 1; done" C-m

tmux new-window -d -t judge
tmux send-keys -t judge:1 "ping www.baidu.com" C-m

tmux new-window -d -t judge
tmux send-keys -t judge:2 "htop" C-m

tmux detach -s judge
