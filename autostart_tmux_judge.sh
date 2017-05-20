#!/bin/bash

sleep 30
ip=$(hostname -I | awk '{print $1}')
cd "$(dirname "$0")"
git pull
sed -i '/JUDGE_NAME =/d' settings.py
echo "JUDGE_NAME = 'judge.$ip'" >> settings.py
tmux new-session -d -s judge
tmux send-keys ./judge/judge.py C-m
tmux detach -s judge
