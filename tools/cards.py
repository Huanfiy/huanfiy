# -*- coding: utf-8 -*-
"""hero（昼夜场景）与 stats（冒险者档案）两张卡的构建器。

genart.py 用它产静态备份，server 用它出动态卡。纯函数，无 IO。
"""
import random

import artlib as A
from content import (PALETTE, SKY, LANG_COLORS, LANG_FALLBACK_COLOR,
                     HERO_TITLE, HERO_MOTTO, HERO_SUB, STATS_LABELS)


# =================================================================== hero ==

HERO_W, HERO_H = 1000, 340

_PHASE = {
    "dawn": dict(cloud="#fdf3e6", cloud_shade="#d9bfae", cloud_op=0.80,
                 mc=PALETTE["roxy"], mc_op=0.28, title=PALETTE["ink"],
                 sub=PALETTE["ink_soft"], stars=8, star_color="#fff7e0",
                 glow="#ffe4c2", glow_op=0.55, ridge="#a7b3c8", ridge_op=0.55,
                 mist="#f8e9d8", hill_far="#a6bf95", hill_near="#8cb277",
                 tuft=PALETTE["grass_deep"], particle="#fff6e6",
                 frame=PALETTE["ink"], firefly=None),
    "day":  dict(cloud="#ffffff", cloud_shade="#c9dcea", cloud_op=0.88,
                 mc=PALETTE["roxy"], mc_op=0.24, title=PALETTE["ink"],
                 sub=PALETTE["ink_soft"], stars=0, star_color="#ffffff",
                 glow="#ffffff", glow_op=0.55, ridge="#9dbfd6", ridge_op=0.55,
                 mist="#eef7f2", hill_far="#a8cf90", hill_near=PALETTE["grass"],
                 tuft=PALETTE["grass_deep"], particle="#ffffff",
                 frame=PALETTE["ink"], firefly=None),
    "dusk": dict(cloud="#f8dcc6", cloud_shade="#c99a8e", cloud_op=0.74,
                 mc="#ffd9a0", mc_op=0.34, title=PALETTE["ink"],
                 sub=PALETTE["ink_soft"], stars=9, star_color="#fff2d6",
                 glow="#ffcf96", glow_op=0.6, ridge="#9a86a6", ridge_op=0.6,
                 mist="#f5d9bf", hill_far="#98a878", hill_near="#7f955f",
                 tuft="#5c7a48", particle="#ffe9c9",
                 frame=PALETTE["ink"], firefly="#ffe08a"),
    "night": dict(cloud="#8b9cc3", cloud_shade="#56679a", cloud_op=0.26,
                  mc=PALETTE["glow"], mc_op=0.62, title="#f3ecd8",
                  sub="#cfcbbb", stars=14, star_color="#f6f1d8",
                  glow="#6d84bf", glow_op=0.45, ridge="#22334f", ridge_op=0.9,
                  mist="#3a4f78", hill_far="#2b3c56", hill_near="#21304a",
                  tuft="#3a5068", particle=PALETTE["glow"],
                  frame="#f3ecd8", firefly="#c9f0a8"),
}


def _sun(phase):
    if phase == "night":
        return (A.horizon_glow(846, 73, 70, 70, "#b5d5e8", 0.18)
                + '<path d="M 850 45 A 27 27 0 1 0 865 88 '
                  'A 23 23 0 0 1 850 45 Z" fill="#f6edcd" '
                  'filter="url(#softglow)"/>'
                + A.stroke("M 822 65 Q 817 84 836 93", "#ffffff", 1, opacity=0.7)
                + A.sparkle(886, 53, 3.5, color="#f6edcd", seed=10, dur=5))
    x, y, r, color = {
        "day": (837, 66, 25, "#fff4ce"),
        "dawn": (764, 210, 28, "#ffeac8"),
        "dusk": (761, 212, 32, "#ffdda7"),
    }[phase]
    return (A.horizon_glow(x, y, r * 3.5, r * 3.5, color, 0.5)
            + f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}" opacity="0.95"/>'
            + f'<circle cx="{x}" cy="{y}" r="{r + 7}" fill="none" '
              f'stroke="{color}" stroke-width="0.8" opacity="0.45"/>')


def build_hero(phase, font_b64):
    st = _PHASE[phase]
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

    # 地平线柔光 + 夜空银河
    body.append(A.horizon_glow(500, 262, 640, 150, st["glow"], st["glow_op"]))
    if phase == "night":
        body.append(f'<ellipse cx="560" cy="120" rx="520" ry="46" '
                    f'fill="#a9b8e0" opacity="0.09" '
                    f'transform="rotate(-9 560 120)" filter="url(#wcblur2)"/>')
        body.append(A.star_field(W, H, 70, seed=77, color="#f6f1d8"))
    elif phase in ("dusk", "dawn"):
        body.append(A.star_field(W, H, 22, seed=78, color="#fff6e0",
                                 y_max=H * 0.4, op_lo=0.15, op_hi=0.5))
    for i in range(st["stars"]):
        x = rnd.uniform(20, W - 20)
        y = rnd.uniform(14, H * 0.5)
        s = rnd.uniform(2.0, 4.6)
        body.append(A.sparkle(x, y, s, color=st["star_color"], seed=100 + i,
                              delay=rnd.uniform(0, 3)))
    body.append(_sun(phase))

    # 远景云（带底部阴影）
    cloud_specs = [(125, 65, 0.78, 22, 68), (377, 48, 0.55, -16, 60),
                   (696, 87, 0.7, 18, 74), (962, 108, 0.64, -14, 54),
                   (266, 191, 0.44, 14, 82)]
    for i, (cx, cy, sc, drift, dur) in enumerate(cloud_specs):
        body.append(A.cloud(cx, cy, sc, st["cloud"],
                            st["cloud_op"] * (1 - 0.12 * (i % 3)),
                            seed=20 + i, drift=drift, dur=dur,
                            shade=st["cloud_shade"]))

    # 淡金星盘像地图水印，装饰不争抢文字的对比度。
    body.append(A.magic_circle(500, 143, 108, color=st["mc"], seed=3,
                               opacity=st["mc_op"] * 0.7, sw=0.9))
    body.append(A.stroke("M 254 143 Q 277 108 302 111 M 725 158 Q 748 178 774 166",
                         st["mc"], 0.9, opacity=0.4, dash="2 6"))
    for sx, sy in [(266, 124), (754, 172)]:
        body.append(A.sparkle(sx, sy, 3.8, color=st["mc"], dur=5.5, lo=0.35))

    # 飞鸟（白天/黎明/黄昏）
    if phase != "night":
        body.append(A.birds([(300, 66, 1.0), (330, 56, 0.85), (356, 70, 0.7)],
                            PALETTE["ink_soft"] if phase != "dusk"
                            else "#5d4a48"))

    # 层叠远山与受光山脊，中心压低，给标题和地平线留白。
    body.append(A.ridge(W, 254, 45, st["ridge"], seed=88, opacity=st["ridge_op"] * 0.55))
    mountains = ("M 0 253 L 70 228 108 235 190 188 263 248 312 226 "
                 "390 264 481 253 570 265 649 237 694 249 778 199 "
                 "825 227 868 214 932 250 1000 232 V 340 H 0 Z")
    body.append(A.fill_path(mountains, st["ridge"], st["ridge_op"]))
    body.append(A.fill_path("M 190 188 L 171 220 189 215 203 230 211 228 Z "
                           "M 778 199 L 753 226 777 217 796 231 807 225 Z",
                           st["mist"], 0.55))
    body.append(A.stroke("M 190 189 L 214 241 244 254 M 778 200 L 796 240 821 253",
                         st["mist"], 1.1, opacity=0.35))
    body.append(A.mist_band(0, 236, W, 44, st["mist"], opacity=0.7))

    # 浮岛是一座可居住的小世界；夜间使用冷色岩石与暖窗。
    night = phase == "night"
    island_grass = "#57796f" if night else st["hill_near"]
    island_deep = "#3b605b" if night else st["tuft"]
    body.append(A.floating_island(148, 157, 156, seed=11, bob=4, dur=10,
                                  waterfall=True, grass=island_grass,
                                  grass_deep=island_deep,
                                  rock="#506676" if night else "#92937e",
                                  night=night))
    body.append(A.floating_island(860, 179, 99, seed=23, bob=3, dur=8,
                                  grass=island_grass, grass_deep=island_deep,
                                  rock="#506676" if night else "#92937e",
                                  landmark="arch", night=night))

    # 草原与蜿蜒溪流：窄的远端和宽的近端形成透视。
    body.append(A.hills(W, 273, 19, st["hill_far"], seed=8, opacity=0.95))
    body.append(A.mist_band(0, 260, W, 30, st["mist"], opacity=0.4))
    body.append(A.hills(W, 300, 19, st["hill_near"], seed=15))
    river = ("M 571 272 Q 543 280 558 286 Q 595 298 552 308 "
             "Q 507 320 503 340 H 403 Q 427 316 501 305 "
             "Q 568 295 543 288 Q 530 280 568 272 Z")
    body.append(A.fill_path(river, "#83b9ca" if not night else "#456b83", 0.88))
    body.append(A.stroke("M 569 274 Q 540 282 553 288 Q 580 298 518 310 "
                         "Q 462 322 446 340", st["mist"], 1.5, opacity=0.6))
    body.append(A.stroke("M 555 294 h 16 M 526 306 h 18 M 481 319 h 26 "
                         "M 485 326 h 11 M 440 334 h 30", st["mist"], 1, opacity=0.55))
    # 成组的小树林与近景坡地，避免整齐重复。
    for px, py, sc in [(39, 286, .34), (55, 287, .43), (71, 286, .28),
                        (309, 292, .28), (325, 293, .39), (342, 294, .24),
                        (731, 287, .28), (746, 287, .4), (762, 287, .3),
                        (944, 280, .42), (962, 279, .54), (982, 280, .37)]:
        body.append(A.pine(px, py, sc, st["tuft"], st["hill_far"]))
    body.append(A.fill_path("M 0 296 Q 128 286 264 322 Q 300 331 349 340 H 0 Z",
                           st["tuft"], 0.65))
    body.append(A.fill_path("M 692 340 Q 814 298 1000 306 V 340 Z",
                           st["tuft"], 0.65))
    body.append(A.meadow(W, 334, seed=9, color=st["tuft"],
                         flower="#d6ded1" if night else "#fbf1d5", count=40, height=20))
    for x, y, sc, flip in [(28, 346, .86, False), (87, 350, .55, True),
                            (971, 346, .9, True), (920, 350, .48, False)]:
        body.append(A.botanical(x, y, sc, color=st["tuft"],
                                flower=st["mist"], flip=flip))

    # 魔力粒子 / 萤火
    for i in range(12):
        x = rnd.uniform(60, W - 60)
        y = rnd.uniform(H * 0.5, H * 0.9)
        body.append(A.dot_particle(x, y, rnd.uniform(1.2, 2.4), st["particle"],
                                   seed=300 + i, rise=rnd.uniform(12, 26)))
    if st["firefly"]:
        for i in range(8):
            x = rnd.uniform(40, W - 40)
            y = rnd.uniform(H * 0.6, H * 0.92)
            body.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.8" '
                f'fill="{st["firefly"]}" filter="url(#softglow)" opacity="0">'
                f'<animate attributeName="opacity" values="0;0.9;0;0;0.7;0" '
                f'dur="{rnd.uniform(4, 7):.1f}s" begin="{rnd.uniform(0, 5):.1f}s" '
                f'repeatCount="indefinite"/></circle>')

    # 标题组：柔光衬底 + 标题 + 座右铭 + 副标
    halo = "#fdfbf5" if phase != "night" else "#141f3a"
    body.append(f'<ellipse cx="500" cy="176" rx="250" ry="78" fill="{halo}" '
                f'opacity="0.22" filter="url(#wcblur2)"/>')
    body.append(A.text(500, 150, HERO_TITLE, 64, color=halo, weight="bold",
                       spacing="2", opacity=0.6,
                       extra='stroke="' + halo + '" stroke-width="7" '
                             'stroke-linejoin="round" filter="url(#wcblur)"'))
    body.append(A.text(500, 150, HERO_TITLE, 64, color=st["title"],
                       weight="bold", spacing="2"))
    body.append(A.text(500, 190, HERO_MOTTO, 22, color=st["title"],
                       opacity=0.92))
    # 副标两侧短线 + 中心小星
    sw_ = A.text_w(HERO_SUB, 14, spacing=3)
    lx1, lx2 = 500 - sw_ / 2 - 16, 500 + sw_ / 2 + 16
    body.append(A.stroke(A.wobbly_line(lx1 - 46, 220, lx1, 220, seed=71, amp=0.8),
                         st["sub"], 1.1, opacity=0.7))
    body.append(A.stroke(A.wobbly_line(lx2, 220, lx2 + 46, 220, seed=72, amp=0.8),
                         st["sub"], 1.1, opacity=0.7))
    body.append(A.text(500, 225, HERO_SUB, 14, color=st["sub"],
                       spacing="3", opacity=0.9))

    # 细线角花替代粗重方框，保留插画的完整轮廓。
    body.append(A.ornament_frame(W, H, st["frame"], inset=10, opacity=0.45))
    body.append('</g>')
    return A.svg_doc(W, H, "".join(body), font_b64=font_b64,
                     title="Huanfly - hand drawn fantasy banner")


# ================================================================== stats ==

STATS_W, STATS_H = 1000, 354


def _stat_chip(x, y, w, h, label, value, color, seed):
    d = A.wobbly_rounded_rect_d(x, y, w, h, 10, seed=seed, amp=1.0)
    parts = [A.fill_path(d, "#ffffff", 0.45),
             A.fill_path(d, color, 0.08),
             A.stroke(d, color, 1.7, opacity=0.75)]
    parts.append(A.text(x + w / 2, y + 33, str(value), 27, weight="bold"))
    parts.append(A.text(x + w / 2, y + 55, label, 13,
                        color=PALETTE["ink_soft"]))
    return "".join(parts)


def _mana_bar(x, y, w, name, pct, color, seed):
    """魔力槽：手绘外框 + 彩色注入 + 光点。"""
    bar_h = 14
    fill_w = max(6.0, w * pct / 100.0)
    parts = [A.text(x - 14, y + bar_h / 2 + 5, name, 14, anchor="end")]
    d = A.wobbly_rounded_rect_d(x, y, w, bar_h, 6, seed=seed, amp=0.7)
    parts.append(A.fill_path(d, "#ffffff", 0.4))
    parts.append(A.stroke(d, PALETTE["ink"], 1.3, opacity=0.6))
    parts.append(
        f'<rect x="{x + 2}" y="{y + 2.5}" width="{fill_w - 4:.1f}" '
        f'height="{bar_h - 5}" rx="4.5" fill="{color}" opacity="0.78"/>')
    parts.append(
        f'<circle cx="{x + fill_w - 4:.1f}" cy="{y + bar_h / 2:.1f}" r="3" '
        f'fill="#ffffff" opacity="0.9" filter="url(#softglow)">'
        f'<animate attributeName="opacity" values="0.4;1;0.4" dur="2.6s" '
        f'repeatCount="indefinite"/></circle>')
    parts.append(A.text(x + w + 14, y + bar_h / 2 + 4.5, f"{pct:.1f}%", 12.5,
                        color=PALETTE["ink_soft"], anchor="start"))
    return "".join(parts)


def build_stats(data, font_b64):
    """data: login,name,motto,avatar_b64,repos,stars,followers,years,
             langs[(name,pct)],updated"""
    W, H = STATS_W, STATS_H
    body = [A.paper_bg(W, H, seed=5)]

    # 角落装饰
    body.append(A.magic_circle(W - 64, H - 64, 44, seed=7, opacity=0.13,
                               dur_outer=70, dur_inner=50, sw=1.1,
                               color=PALETTE["roxy"]))
    body.append(A.watercolor_blob(150, 150, 96, PALETTE["roxy"], seed=31,
                                  opacity=0.06, layers=2))
    body.append(A.watercolor_blob(W - 150, 90, 70, PALETTE["gold"], seed=33,
                                  opacity=0.07))
    for i, (sx, sy) in enumerate([(W - 40, 36), (44, 44), (W - 86, 92)]):
        body.append(A.sparkle(sx, sy, 4.5, seed=40 + i, delay=i * 0.7))

    # ------- 左栏：头像 + 名字 -------
    ax, ay, ar = 148, 136, 56
    if data.get("avatar_b64"):
        body.append(f'''
  <clipPath id="av"><circle cx="{ax}" cy="{ay}" r="{ar - 3}"/></clipPath>
  <image href="data:image/png;base64,{data["avatar_b64"]}"
    x="{ax - ar + 3}" y="{ay - ar + 3}" width="{(ar - 3) * 2}"
    height="{(ar - 3) * 2}" clip-path="url(#av)"/>''')
    else:
        body.append(A.fill_path(A.wobbly_circle_d(ax, ay, ar - 4, seed=4),
                                PALETTE["paper_deep"], 0.9))
        body.append(A.magic_circle(ax, ay, ar - 14, seed=27, opacity=0.5,
                                   dur_outer=50, dur_inner=36, sw=1.1,
                                   color=PALETTE["roxy"]))
        body.append(A.text(ax, ay + 11, "H", 32, weight="bold",
                           color=PALETTE["roxy"], opacity=0.85))
    body.append(A.stroke(A.wobbly_circle_d(ax, ay, ar, seed=3), PALETTE["ink"], 2.4))
    body.append(A.stroke(A.wobbly_circle_d(ax, ay, ar + 7, seed=9,
                                           irregular=0.04),
                         PALETTE["roxy"], 1.2, opacity=0.5, dash="6 5"))
    # Lv 徽章挂在头像右上
    bx, by = ax + ar - 8, ay - ar + 8
    body.append(A.fill_path(A.wobbly_circle_d(bx, by, 19, seed=17, irregular=0.04),
                            PALETTE["paper"], 1.0))
    body.append(A.stroke(A.wobbly_circle_d(bx, by, 19, seed=17, irregular=0.04),
                         PALETTE["gold"], 2.2))
    body.append(A.text(bx, by + 5, f'Lv.{data["years"]}', 13, weight="bold",
                       color="#9a7434"))
    body.append(A.text(ax, ay + ar + 36, data["name"], 26, weight="bold"))
    body.append(A.text(ax, ay + ar + 60, data["motto"], 13,
                       color=PALETTE["ink_soft"]))
    # 分栏竖线
    body.append(A.stroke(A.wobbly_line(296, 44, 296, H - 44, seed=21, amp=1.2),
                         PALETTE["ink"], 1.2, opacity=0.22))

    # ------- 数值行 -------
    chips = [
        (STATS_LABELS["repos"], data["repos"], PALETTE["roxy"]),
        (STATS_LABELS["stars"], data["stars"], PALETTE["gold"]),
        (STATS_LABELS["followers"], data["followers"], PALETTE["red"]),
        (STATS_LABELS["years"], data["years"], PALETTE["grass_deep"]),
    ]
    cw, ch, gap = 142, 70, 18
    x0 = 340
    for i, (label, value, color) in enumerate(chips):
        body.append(_stat_chip(x0 + i * (cw + gap), 46, cw, ch, label, value,
                               color, seed=50 + i))

    # ------- 魔力构成（语言条） -------
    body.append(A.text(x0, 158, STATS_LABELS["mana"], 18, weight="bold",
                       anchor="start"))
    mw = A.text_w(STATS_LABELS["mana"], 18)
    body.append(A.text(x0 + mw + 12, 158, STATS_LABELS["mana_sub"], 12,
                       color=PALETTE["ink_soft"], anchor="start", spacing="1"))
    body.append(A.fade_line(x0, 168, x0 + 610, PALETTE["roxy"], w=1.4,
                            opacity=0.55, seed=23, fade_out=0.5))
    langs = data["langs"][:5]
    for i, (name, pct) in enumerate(langs):
        color = LANG_COLORS.get(name, LANG_FALLBACK_COLOR)
        body.append(_mana_bar(x0 + 78, 184 + i * 26, 440, name, pct, color,
                              seed=70 + i))

    # ------- 更新时间 -------
    body.append(A.text(x0, H - 26,
                       f'{STATS_LABELS["updated"]} {data["updated"]} (UTC+8)',
                       11, color=PALETTE["ink_soft"], anchor="start",
                       opacity=0.75))
    return A.svg_doc(W, H, "".join(body), font_b64=font_b64,
                     title="Huanfly - GitHub adventurer profile",
                     grain=(4, 4, W - 8, H - 8, 14))


SAMPLE_STATS = {
    "login": "Huanfiy", "name": "Huanfly", "motto": HERO_MOTTO,
    "avatar_b64": "", "repos": 17, "stars": 1, "followers": 2, "years": 6,
    "langs": [("C", 36.4), ("Python", 36.4), ("Rust", 9.1), ("HTML", 9.1),
              ("Shell", 9.1)],
    "updated": "2026-09-02 20:10",
}
