#!/bin/bash

sleep 10
ip=$(ifconfig | sed -En 's/127.0.0.1//;s/172.17.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p')
cd "$(dirname "$0")"
sed -i '/JUDGE_NAME =/d' settings.py
echo "JUDGE_NAME = 'judge.$ip'" >> settings.py
tmux new-session -d -s judge
tmux send-keys ./judge/judge.py C-m
tmux detach -s judge
