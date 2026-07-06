#!/usr/bin/env bash
# 部署 gh-cards 服务到 huanfly.com（在仓库根目录执行：bash server/deploy.sh）
set -euo pipefail
HOST=ubuntu@huanfly.com
APP=/home/ubuntu/apps/gh-cards

ssh "$HOST" "mkdir -p $APP/official"
scp tools/artlib.py tools/cards.py tools/content.py \
    tools/fonts/wenkai-medium.b64 \
    server/server.py \
    assets/fallback-art.svg \
    "$HOST:$APP/"
scp server/gh-cards.service "$HOST:/tmp/gh-cards.service"
ssh "$HOST" 'sudo mv /tmp/gh-cards.service /etc/systemd/system/gh-cards.service \
  && sudo systemctl daemon-reload \
  && sudo systemctl enable --now gh-cards \
  && sudo systemctl restart gh-cards \
  && sleep 1 && systemctl is-active gh-cards \
  && curl -sf http://127.0.0.1:8321/gh/health && echo " health OK"'
