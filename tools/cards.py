# -*- coding: utf-8 -*-
"""hero（昼夜场景）与 stats（冒险者档案）两张卡的构建器。

genart.py 用它产静态备份，server 用它出动态卡。纯函数，无 IO。
"""
import math
import random

import artlib as A
from content import (PALETTE, SKY, LANG_COLORS, LANG_FALLBACK_COLOR,
                     HERO_TITLE, HERO_MOTTO, HERO_SUB,
                     STATS_TITLE, STATS_SUB, STATS_LABELS)


# =================================================================== hero ==

HERO_W, HERO_H = 1000, 340

_PHASE_STYLE = {
    #        云色        云透明  魔法阵透明 标题色              星星数
    "dawn":  ("#fdf3e3", 0.75, 0.50, PALETTE["ink"],      6),
    "day":   ("#ffffff", 0.80, 0.48, PALETTE["ink"],      0),
    "dusk":  ("#f9dcc0", 0.70, 0.55, PALETTE["ink"],      8),
    "night": ("#8b9cc3", 0.28, 0.90, "#f3ecd8",          26),
}

_MC_COLOR = {"dawn": "roxy", "day": "roxy", "dusk": None, "night": "glow"}


def _sun(phase):
    if phase == "day":
        return (f'<circle cx="840" cy="70" r="30" fill="#fff3c9" '
                f'opacity="0.95" filter="url(#bigglow)"/>')
    if phase == "dawn":
        return (f'<circle cx="820" cy="180" r="26" fill="#ffe9bd" '
                f'opacity="0.9" filter="url(#bigglow)"/>')
    if phase == "dusk":
        return (f'<circle cx="810" cy="185" r="30" fill="#ffcf8a" '
                f'opacity="0.95" filter="url(#bigglow)"/>')
    # night: 弯月
    return (f'<g filter="url(#bigglow)"><path d="M 848 58 A 26 26 0 1 0 862 '
            f'104 A 21 21 0 1 1 848 58 Z" fill="#f4ecc9" opacity="0.95"/></g>')


def build_hero(phase, font_b64):
    st = _PHASE_STYLE[phase]
    cloud_color, cloud_op, mc_op, title_color, n_stars = st
    top, mid, bot = SKY[phase]
    rnd = random.Random(42)
    W, H = HERO_W, HERO_H

    body = [f'''
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{top}"/>
      <stop offset="0.62" stop-color="{mid}"/>
      <stop offset="1" stop-color="{bot}"/>
    </linearGradient>
    <clipPath id="round"><rect width="{W}" height="{H}" rx="16"/></clipPath>
  </defs>
  <g clip-path="url(#round)">
  <rect width="{W}" height="{H}" fill="url(#sky)"/>''']

    # 星星（夜/晨昏）
    for i in range(n_stars):
        x = rnd.uniform(20, W - 20)
        y = rnd.uniform(14, H * 0.55)
        s = rnd.uniform(2.2, 5.0)
        color = "#f6f1d8" if phase == "night" else "#fff7e0"
        body.append(A.sparkle(x, y, s, color=color, seed=100 + i,
                              delay=rnd.uniform(0, 3)))
    body.append(_sun(phase))

    # 远景云
    cloud_specs = [(150, 80, 1.15, 30, 55), (415, 52, 0.8, -22, 48),
                   (700, 105, 1.0, 26, 62), (905, 60, 0.7, -18, 40),
                   (280, 150, 0.62, 20, 70)]
    for i, (cx, cy, sc, drift, dur) in enumerate(cloud_specs):
        body.append(A.cloud(cx, cy, sc, cloud_color, cloud_op * (1 - 0.12 * (i % 3)),
                            seed=20 + i, drift=drift, dur=dur))

    # 大魔法阵（标题背后）
    key = _MC_COLOR[phase]
    mc_color = PALETTE[key] if key else "#ffd9a0"
    body.append(A.magic_circle(500, 156, 134, color=mc_color, seed=3,
                               opacity=mc_op, sw=1.5))

    # 飞鸟（白天/黎明）
    if phase in ("day", "dawn"):
        for i, (bx, by) in enumerate([(300, 66), (330, 56), (356, 70)]):
            body.append(A.stroke(
                f"M {bx - 7} {by} Q {bx} {by - 6} {bx + 7} {by}",
                PALETTE["ink_soft"], 1.6, opacity=0.75 - i * 0.15))

    # 浮空岛
    body.append(A.floating_island(148, 118, 118, seed=11, bob=5, dur=8.5,
                                  waterfall=True))
    body.append(A.floating_island(866, 150, 74, seed=23, bob=4, dur=6.5))
    if phase == "night":
        # 夜晚岛下的萤光
        body.append(A.dot_particle(148, 150, 2.2, PALETTE["glow"], seed=61, rise=10))
        body.append(A.dot_particle(866, 176, 1.8, PALETTE["glow"], seed=62, rise=8))

    # 远山与草原
    hill_far = {"day": "#a8cf90", "dawn": "#9fb98c", "dusk": "#96a06e",
                "night": "#2c3d55"}[phase]
    hill_near = {"day": PALETTE["grass"], "dawn": "#8cb277", "dusk": "#7d925f",
                 "night": "#22304a"}[phase]
    body.append(A.hills(W, 268, 16, hill_far, seed=8, opacity=0.9))
    body.append(A.hills(W, 296, 12, hill_near, seed=15))
    tuft_color = PALETTE["grass_deep"] if phase != "night" else "#3a5068"
    body.append(A.grass_tufts(W, 322, 26, seed=9, color=tuft_color))

    # 魔力粒子
    pcolor = PALETTE["glow"] if phase == "night" else "#ffffff"
    for i in range(14):
        x = rnd.uniform(60, W - 60)
        y = rnd.uniform(H * 0.45, H * 0.9)
        body.append(A.dot_particle(x, y, rnd.uniform(1.2, 2.6), pcolor,
                                   seed=300 + i, rise=rnd.uniform(12, 26)))

    # 标题组
    halo = "#fdfbf5" if phase != "night" else "#141f3a"
    body.append(A.text(500, 150, HERO_TITLE, 64, color=halo, weight="bold",
                       spacing="2", opacity=0.55,
                       extra='stroke="' + halo + '" stroke-width="7" '
                             'stroke-linejoin="round" filter="url(#wcblur)"'))
    body.append(A.text(500, 150, HERO_TITLE, 64, color=title_color,
                       weight="bold", spacing="2"))
    body.append(A.text(500, 192, HERO_MOTTO, 23, color=title_color,
                       opacity=0.92))
    sub_color = title_color if phase == "night" else PALETTE["ink_soft"]
    body.append(A.text(500, 224, HERO_SUB, 14.5, color=sub_color,
                       spacing="3", opacity=0.85))

    # 手绘内边框
    frame_color = "#f3ecd8" if phase == "night" else PALETTE["ink"]
    body.append(A.stroke(A.wobbly_rect_d(8, 8, W - 16, H - 16, seed=5),
                         frame_color, 2.2, opacity=0.65))
    body.append('</g>')
    return A.svg_doc(W, H, "".join(body), font_b64=font_b64,
                     title="Huanfly - hand drawn fantasy banner")


# ================================================================== stats ==

STATS_W, STATS_H = 900, 430


def _stat_chip(x, y, w, label, value, color, seed):
    parts = [A.sketchy_frame(x, y, w, 64, seed=seed, color=color, sw=2.0,
                             double=False)]
    parts.append(A.watercolor_blob(x + w / 2, y + 32, w * 0.42, color,
                                   seed=seed + 3, opacity=0.10, layers=1))
    parts.append(A.text(x + w / 2, y + 30, str(value), 26, weight="bold"))
    parts.append(A.text(x + w / 2, y + 52, label, 13.5,
                        color=PALETTE["ink_soft"]))
    return "".join(parts)


def _mana_bar(x, y, w, name, pct, color, seed):
    """魔力槽：手绘外框 + 彩色注入 + 光点。"""
    bar_h = 15
    fill_w = max(6.0, w * pct / 100.0)
    parts = [A.text(x - 12, y + bar_h / 2 + 5, name, 14.5, anchor="end")]
    parts.append(A.stroke(A.wobbly_rect_d(x, y, w, bar_h, seed=seed, amp=1.1),
                          PALETTE["ink"], 1.6, opacity=0.85))
    parts.append(
        f'<rect x="{x + 2}" y="{y + 2.5}" width="{fill_w - 4:.1f}" '
        f'height="{bar_h - 5}" rx="5" fill="{color}" opacity="0.78"/>')
    parts.append(
        f'<circle cx="{x + fill_w - 4:.1f}" cy="{y + bar_h / 2:.1f}" r="3.2" '
        f'fill="#ffffff" opacity="0.9" filter="url(#softglow)">'
        f'<animate attributeName="opacity" values="0.4;1;0.4" dur="2.6s" '
        f'repeatCount="indefinite"/></circle>')
    parts.append(A.text(x + w + 14, y + bar_h / 2 + 5, f"{pct:.1f}%", 13,
                        color=PALETTE["ink_soft"], anchor="start"))
    return "".join(parts)


def build_stats(data, font_b64):
    """data: login,name,motto,avatar_b64,repos,stars,followers,years,
             langs[(name,pct)],updated"""
    W, H = STATS_W, STATS_H
    body = [A.paper_bg(W, H, seed=5)]

    # 角落装饰
    body.append(A.magic_circle(64, H - 62, 46, seed=7, opacity=0.18,
                               dur_outer=70, dur_inner=50, sw=1.2,
                               color=PALETTE["roxy"]))
    body.append(A.watercolor_blob(W - 110, 320, 70, PALETTE["glow"], seed=31,
                                  opacity=0.07))
    body.append(A.watercolor_blob(120, 90, 60, PALETTE["gold"], seed=33,
                                  opacity=0.08))
    for i, (sx, sy) in enumerate([(W - 46, 40), (W - 70, 96), (44, 46),
                                  (W - 40, 300)]):
        body.append(A.sparkle(sx, sy, 5, seed=40 + i, delay=i * 0.7))

    # ------- 左栏：头像 + 名字 -------
    ax, ay, ar = 132, 172, 62
    if data.get("avatar_b64"):
        body.append(f'''
  <clipPath id="av"><circle cx="{ax}" cy="{ay}" r="{ar - 4}"/></clipPath>
  <image href="data:image/png;base64,{data["avatar_b64"]}"
    x="{ax - ar + 4}" y="{ay - ar + 4}" width="{(ar - 4) * 2}"
    height="{(ar - 4) * 2}" clip-path="url(#av)"/>''')
    else:
        # 无头像时的手绘纹章占位
        body.append(A.fill_path(A.wobbly_circle_d(ax, ay, ar - 5, seed=4),
                                PALETTE["paper_deep"], 0.9))
        body.append(A.magic_circle(ax, ay, ar - 16, seed=27, opacity=0.5,
                                   dur_outer=50, dur_inner=36, sw=1.1,
                                   color=PALETTE["roxy"]))
        body.append(A.text(ax, ay + 12, "H", 34, weight="bold",
                           color=PALETTE["roxy"], opacity=0.85))
    body.append(A.stroke(A.wobbly_circle_d(ax, ay, ar, seed=3), PALETTE["ink"], 2.6))
    body.append(A.stroke(A.wobbly_circle_d(ax, ay, ar + 6, seed=9,
                                           irregular=0.04),
                         PALETTE["roxy"], 1.3, opacity=0.5,
                         dash="6 5"))
    body.append(A.text(ax, ay + ar + 34, data["name"], 27, weight="bold"))
    body.append(A.text(ax, ay + ar + 60, data["motto"], 13.5,
                       color=PALETTE["ink_soft"]))
    # Lv 徽章
    lv = f'Lv.{data["years"]}'
    body.append(A.stroke(A.wobbly_circle_d(ax, 62, 25, seed=17, irregular=0.05),
                         PALETTE["gold"], 2.2))
    body.append(A.text(ax, 69, lv, 17, weight="bold", color="#9a7434"))

    # ------- 标题 -------
    body.append(A.text(560, 62, STATS_TITLE, 30, weight="bold", spacing="6"))
    body.append(A.text(560, 88, STATS_SUB, 13.5, color=PALETTE["ink_soft"],
                       spacing="2"))
    body.append(A.stroke(A.wobbly_line(330, 104, 790, 104, seed=21, amp=1.4),
                         PALETTE["roxy"], 1.8, opacity=0.6))

    # ------- 数值行 -------
    chips = [
        (STATS_LABELS["repos"], data["repos"], PALETTE["roxy"]),
        (STATS_LABELS["stars"], data["stars"], PALETTE["gold"]),
        (STATS_LABELS["followers"], data["followers"], PALETTE["red"]),
        (STATS_LABELS["years"], data["years"], PALETTE["grass_deep"]),
    ]
    cw, gap, x0 = 118, 14, 300
    for i, (label, value, color) in enumerate(chips):
        body.append(_stat_chip(x0 + i * (cw + gap), 128, cw, label, value,
                               color, seed=50 + i))

    # ------- 魔力构成（语言条） -------
    body.append(A.text(300, 246, STATS_LABELS["mana"], 19, weight="bold",
                       anchor="start"))
    body.append(A.text(414, 246, STATS_LABELS["mana_sub"], 12.5,
                       color=PALETTE["ink_soft"], anchor="start"))
    langs = data["langs"][:5]
    for i, (name, pct) in enumerate(langs):
        color = LANG_COLORS.get(name, LANG_FALLBACK_COLOR)
        body.append(_mana_bar(392, 268 + i * 28, 330, name, pct, color,
                              seed=70 + i))

    # ------- 更新时间 -------
    body.append(A.text(W - 26, H - 22,
                       f'{STATS_LABELS["updated"]} {data["updated"]} (UTC+8)',
                       11.5, color=PALETTE["ink_soft"], anchor="end",
                       opacity=0.8))
    return A.svg_doc(W, H, "".join(body), font_b64=font_b64,
                     title="Huanfly - GitHub adventurer profile")


SAMPLE_STATS = {
    "login": "Huanfiy", "name": "Huanfly", "motto": HERO_MOTTO,
    "avatar_b64": "", "repos": 13, "stars": 2, "followers": 1, "years": 3,
    "langs": [("C", 38.2), ("Python", 24.6), ("C++", 18.1), ("Shell", 12.4),
              ("Lua", 6.7)],
    "updated": "2026-07-06 15:00",
}
