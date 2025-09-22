#!/bin/bash
while true; do
  git add .
  git commit -m "auto: $(date '+%Y-%m-%d %H:%M:%S')" >/dev/null 2>&1
  git push origin main >/dev/null 2>&1
  sleep 10
     # 每 60 秒 push 一次，你可以改成 10 秒
done
