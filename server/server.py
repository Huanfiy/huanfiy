#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gh-cards：GitHub profile 动态 SVG 卡片服务（huanfly.com）。

端点（由 nginx `location ^~ /gh/` 反代到 127.0.0.1:8321）：
  /gh/hero.svg   按北京时间返回 黎明/白天/黄昏/夜晚 场景（启动时预构建）
  /gh/stats.svg  GitHub 公开统计卡（后台线程每 30 分钟刷新，失败保留旧值）
  /gh/keyart     素材位：official/ 目录有图则返回最新一张，否则回退原创插画
  /gh/health     健康检查

仅用 stdlib；部署目录需含 artlib.py / cards.py / content.py /
wenkai-medium.b64 / fallback-art.svg。
"""
import base64
import json
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

import cards  # noqa: E402
from content import HERO_MOTTO  # noqa: E402

USER = "Huanfiy"
PORT = 8321
REFRESH_SEC = 1800
TZ = timezone(timedelta(hours=8))
FONT_B64 = (BASE / "wenkai-medium.b64").read_text().strip()
CACHE_FILE = BASE / "cache.json"
OFFICIAL_DIR = BASE / "official"
FALLBACK_ART = BASE / "fallback-art.svg"

MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".webp": "image/webp", ".gif": "image/gif",
        ".svg": "image/svg+xml; charset=utf-8"}


def log(*a):
    print(datetime.now(TZ).strftime("%m-%d %H:%M:%S"), *a, flush=True)


# ------------------------------------------------------------ GitHub 数据 --

def _get(url, binary=False):
    req = urllib.request.Request(url, headers={
        "User-Agent": "gh-cards/1.0 (+https://huanfly.com)",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        data = r.read()
        ctype = r.headers.get("Content-Type", "")
    return (data, ctype) if binary else json.loads(data)


def fetch_stats():
    api = "https://api.github.com"
    user = _get(f"{api}/users/{USER}")
    repos = _get(f"{api}/users/{USER}/repos?per_page=100&type=owner")

    stars = sum(r["stargazers_count"] for r in repos)
    # 按非 fork 仓库的主语言计数（字节统计会被 vendored SDK/BSP 扭曲）；
    # 白名单里的 fork 属于长期主力维护项目，一并计入
    include_forks = {"VocoType-linux"}
    lang_count = {}
    for r in repos:
        if (r["fork"] and r["name"] not in include_forks) \
                or not r.get("language"):
            continue
        lang_count[r["language"]] = lang_count.get(r["language"], 0) + 1
    total = sum(lang_count.values()) or 1
    langs = sorted(lang_count.items(), key=lambda kv: -kv[1])[:5]
    langs = [(k, round(v * 100.0 / total, 1)) for k, v in langs]

    created = datetime.strptime(user["created_at"],
                                "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc)
    years = max(1, int((datetime.now(timezone.utc) - created).days // 365))

    avatar_b64 = ""
    try:
        raw, _ = _get(user["avatar_url"] + "&s=120", binary=True)
        avatar_b64 = base64.b64encode(raw).decode()
    except Exception as e:
        log("avatar fail:", e)

    return {
        "login": USER,
        "name": user.get("name") or USER,
        "motto": user.get("bio") or HERO_MOTTO,
        "avatar_b64": avatar_b64,
        "repos": user["public_repos"],
        "stars": stars,
        "followers": user["followers"],
        "years": years,
        "langs": langs,
        "updated": datetime.now(TZ).strftime("%Y-%m-%d %H:%M"),
    }


# ---------------------------------------------------------------- 缓存层 --

_lock = threading.Lock()
_stats_svg = None


def _load_disk_cache():
    global _stats_svg
    if CACHE_FILE.exists():
        try:
            data = json.loads(CACHE_FILE.read_text())
            _stats_svg = cards.build_stats(data, FONT_B64)
            log("loaded disk cache from", data.get("updated"))
        except Exception as e:
            log("disk cache broken:", e)


def _refresh_loop():
    global _stats_svg
    while True:
        try:
            data = fetch_stats()
            svg = cards.build_stats(data, FONT_B64)
            with _lock:
                _stats_svg = svg
            CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False))
            log("stats refreshed:", data["repos"], "repos,",
                data["stars"], "stars")
        except Exception as e:
            log("refresh failed (keep stale):", e)
        time.sleep(REFRESH_SEC)


# ---------------------------------------------------------------- hero 层 --

HERO = {p: cards.build_hero(p, FONT_B64)
        for p in ("dawn", "day", "dusk", "night")}


def hero_phase(now=None):
    h = (now or datetime.now(TZ)).hour
    if 5 <= h < 8:
        return "dawn"
    if 8 <= h < 17:
        return "day"
    if 17 <= h < 20:
        return "dusk"
    return "night"


def keyart():
    """official/ 目录里最新的一张图；没有则回退原创插画。"""
    files = [p for p in OFFICIAL_DIR.glob("*")
             if p.suffix.lower() in MIME and p.is_file()]
    if files:
        p = max(files, key=lambda p: p.stat().st_mtime)
        return p.read_bytes(), MIME[p.suffix.lower()]
    return FALLBACK_ART.read_bytes(), MIME[".svg"]


# ------------------------------------------------------------------ HTTP --

class Handler(BaseHTTPRequestHandler):
    server_version = "gh-cards/1.0"

    def _send(self, body, ctype, max_age):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", f"max-age={max_age}")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        try:
            if path == "/gh/hero.svg":
                self._send(HERO[hero_phase()],
                           "image/svg+xml; charset=utf-8", 900)
            elif path == "/gh/stats.svg":
                with _lock:
                    svg = _stats_svg
                if svg is None:
                    self.send_error(503, "stats not ready")
                    return
                self._send(svg, "image/svg+xml; charset=utf-8", 1800)
            elif path == "/gh/keyart":
                body, ctype = keyart()
                self._send(body, ctype, 3600)
            elif path == "/gh/health":
                self._send("ok", "text/plain", 0)
            else:
                self.send_error(404)
        except BrokenPipeError:
            pass
        except Exception as e:
            log("500:", path, e)
            try:
                self.send_error(500)
            except Exception:
                pass

    def log_message(self, fmt, *args):
        pass  # 访问日志交给 nginx


def main():
    OFFICIAL_DIR.mkdir(exist_ok=True)
    _load_disk_cache()
    threading.Thread(target=_refresh_loop, daemon=True).start()
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    log(f"gh-cards listening on 127.0.0.1:{PORT}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
