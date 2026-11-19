#!/usr/bin/env bash
# 部署 gh-cards 服务到 huanfly.com（在仓库根目录执行：bash server/deploy.sh）
set -euo pipefail
HOST=ubuntu@huanfly.com
APP=/home/ubuntu/apps/gh-cards

# Camo fetches large loops from GitHub's CDN. Never point at an unpublished SHA.
git diff --quiet HEAD -- assets/playback || { echo 'Commit and push playback assets first' >&2; exit 1; }
REV=$(git log -1 --format=%H -- assets/playback)
curl -fsSI "https://raw.githubusercontent.com/Huanfiy/huanfiy/$REV/assets/playback/hero-night.webp" >/dev/null
ssh "$HOST" "mkdir -p $APP/official $APP/playback; printf '%s\n' '$REV' > $APP/playback/revision.tmp && mv $APP/playback/revision.tmp $APP/playback/revision"
rsync -a assets/playback/stats-tiles.json "$HOST:$APP/playback/"
scp tools/artlib.py tools/cards.py tools/content.py tools/stat_playback.py \
    tools/fonts/wenkai-medium.b64 tools/fonts/wenkai-medium.metrics.json \
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
