# -*- coding: utf-8 -*-
"""生成 README 用的全部静态 SVG 资产到 ../assets/。

用法: python genart.py <font_medium.b64> [font_regular.b64]
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import artlib as A
import cards
from content import (PALETTE, SKY, LANG_COLORS, STACK_TITLE, STACK_TITLE_SUB,
                     STACK_GROUPS, PROJECT_CARDS, FOOTER_QUOTE, FOOTER_SIGN)

OUT = Path(__file__).parent.parent / "assets"


# ================================================================= 分隔符 ==

def divider():
    # 明暗主题都可见：中间调暖棕 + 蓝色副线
    W, H = 1000, 34
    cx, cy = W / 2, H / 2 + 1
    line, sub = "#a18a68", "#7b9cc9"
    body = []
    for sign, seed in ((-1, 3), (1, 4)):
        x_far = cx + sign * 470
        x_near = cx + sign * 46
        body.append(A.stroke(A.wobbly_line(x_far, cy, x_near, cy, seed=seed,
                                           amp=1.8), line, 2.2, opacity=0.9))
        body.append(A.stroke(A.wobbly_line(x_far + sign * -60, cy + 5,
                                           x_near + sign * 30, cy + 5,
                                           seed=seed + 9, amp=1.4),
                             sub, 1.3, opacity=0.55))
    # 中心菱形符印 + 呼吸光
    s = 8
    d = f"M {cx} {cy - s} L {cx + s} {cy} L {cx} {cy + s} L {cx - s} {cy} Z"
    body.append(f'<g filter="url(#softglow)">'
                + A.stroke(d, sub, 2.0)
                + f'<circle cx="{cx}" cy="{cy}" r="2.6" fill="{PALETTE["glow"]}">'
                  f'<animate attributeName="opacity" values="0.3;1;0.3" '
                  f'dur="3.2s" repeatCount="indefinite"/></circle></g>')
    body.append(A.sparkle(cx - 26, cy - 4, 4.5, color="#d9b36a", seed=11,
                          delay=0.6))
    body.append(A.sparkle(cx + 26, cy + 3, 4.5, color="#d9b36a", seed=12,
                          delay=1.8))
    return A.svg_doc(W, H, "".join(body), title="divider", grain=False)


# ============================================================== 章节图标 ==

def _icon_doc(body, label):
    # 羊皮纸底衬，保证暗色主题可见
    chip = (f'<rect x="1.5" y="1.5" width="37" height="37" rx="9" '
            f'fill="{PALETTE["paper"]}"/>'
            + A.stroke(A.wobbly_rect_d(3.5, 3.5, 33, 33, seed=2, amp=0.8),
                       PALETTE["ink"], 1.5, opacity=0.7))
    return A.svg_doc(40, 40, chip + body, title=label, grain=False)


def icon_about():
    # 羽毛笔 + 墨点
    body = [A.stroke("M 30 6 Q 20 10 13 22 Q 10 28 9 33", PALETTE["roxy"], 2.4),
            A.stroke("M 30 6 Q 26 16 17 26 M 25 12 Q 21 14 15 21 M 28 9 "
                     "Q 24 17 19 24", PALETTE["roxy"], 1.3, opacity=0.7),
            A.stroke("M 9 33 L 7 36", PALETTE["ink"], 2.2),
            f'<circle cx="12" cy="35.5" r="1.8" fill="{PALETTE["ink"]}" '
            f'opacity="0.75"/>']
    return _icon_doc("".join(body), "about")


def icon_stack():
    # 魔导书：封面 + 书签 + 星印
    body = [A.stroke(A.wobbly_rect_d(7, 8, 24, 27, seed=3, amp=1.0),
                     PALETTE["ink"], 2.2),
            A.stroke("M 11 8 L 11 35", PALETTE["ink"], 1.3, opacity=0.6),
            A.fill_path("M 24 8 L 24 18 L 27 15 L 30 18 L 30 8 Z",
                        PALETTE["red"], 0.85),
            A.sparkle(19, 24, 5, color=PALETTE["gold"], seed=5, dur=2.8)]
    return _icon_doc("".join(body), "stack")


def icon_works():
    # 宝箱
    body = [A.stroke(A.wobbly_rect_d(6, 17, 28, 16, seed=4, amp=1.0),
                     PALETTE["ink"], 2.2),
            A.stroke("M 6 17 Q 20 5 34 17", PALETTE["ink"], 2.2),
            A.stroke("M 20 17 L 20 33 M 6 24 L 34 24", PALETTE["ink"], 1.2,
                     opacity=0.5),
            A.fill_path("M 17.5 20 L 22.5 20 L 22.5 27 L 20 29 L 17.5 27 Z",
                        PALETTE["gold"], 0.9),
            A.sparkle(31, 10, 4, seed=6, delay=1.1)]
    return _icon_doc("".join(body), "works")


def icon_stats():
    # 水晶球 + 底座
    body = [A.stroke(A.wobbly_circle_d(20, 17, 11.5, seed=7), PALETTE["roxy"], 2.2),
            A.fill_path(A.wobbly_circle_d(20, 17, 10, seed=8, irregular=0.05),
                        PALETTE["glow"], 0.25),
            A.stroke("M 14 12 Q 17 9 21 9.5", "#ffffff", 1.6, opacity=0.9),
            A.stroke("M 11 30 Q 20 25 29 30 L 27 34 L 13 34 Z",
                     PALETTE["ink"], 2.0),
            A.sparkle(20, 17, 4.5, color="#ffffff", seed=9, dur=2.2)]
    return _icon_doc("".join(body), "stats")


# ============================================================ 技术栈面板 ==

def _chip(x, y, w, h, label, color, seed, font_size=15):
    parts = [
        A.fill_path(f"M {x+3} {y+3} h {w-6} a 6 6 0 0 1 6 6 v {h-18} "
                    f"a 6 6 0 0 1 -6 6 h {-(w-6)} a 6 6 0 0 1 -6 -6 "
                    f"v {-(h-18)} a 6 6 0 0 1 6 -6 Z", "#ffffff", 0.5),
        A.stroke(A.wobbly_rect_d(x, y, w, h, seed=seed, amp=1.2),
                 PALETTE["ink"], 1.7, opacity=0.9),
        f'<circle cx="{x + 12}" cy="{y + h / 2}" r="3" fill="{color}" '
        f'opacity="0.9"/>',
        A.text(x + 12 + (w - 12) / 2, y + h / 2 + 5.5, label, font_size),
    ]
    return "".join(parts)


def _doodle_chipset(cx, cy):
    """芯片：方体 + 引脚 + 核心星。"""
    p = [A.stroke(A.wobbly_rect_d(cx - 13, cy - 13, 26, 26, seed=3, amp=1.0),
                  PALETTE["ink"], 2.0)]
    for i in range(4):
        off = -9 + i * 6
        p.append(A.stroke(f"M {cx + off} {cy - 13} L {cx + off} {cy - 18} "
                          f"M {cx + off} {cy + 13} L {cx + off} {cy + 18}",
                          PALETTE["ink"], 1.5, opacity=0.8))
        p.append(A.stroke(f"M {cx - 13} {cy + off} L {cx - 18} {cy + off} "
                          f"M {cx + 13} {cy + off} L {cx + 18} {cy + off}",
                          PALETTE["ink"], 1.5, opacity=0.8))
    p.append(A.sparkle(cx, cy, 5, color=PALETTE["roxy"], seed=4, dur=3.0))
    return "".join(p)


def _doodle_gear(cx, cy):
    p = [A.stroke(A.wobbly_circle_d(cx, cy, 12, seed=5), PALETTE["ink"], 2.0),
         A.stroke(A.wobbly_circle_d(cx, cy, 4.5, seed=6, irregular=0.06),
                  PALETTE["ink"], 1.6)]
    for i in range(8):
        a = math.tau * i / 8 + 0.2
        x1, y1 = cx + 12 * math.cos(a), cy + 12 * math.sin(a)
        x2, y2 = cx + 17 * math.cos(a), cy + 17 * math.sin(a)
        p.append(A.stroke(f"M {x1:.1f} {y1:.1f} L {x2:.1f} {y2:.1f}",
                          PALETTE["ink"], 2.2))
    g = "".join(p)
    return (f'<g>{g}<animateTransform attributeName="transform" type="rotate" '
            f'from="0 {cx} {cy}" to="360 {cx} {cy}" dur="26s" '
            f'repeatCount="indefinite"/></g>')


def _doodle_potion(cx, cy):
    body_d = (f"M {cx - 4} {cy - 16} L {cx - 4} {cy - 7} "
              f"Q {cx - 14} {cy + 2} {cx - 11} {cy + 9} "
              f"Q {cx - 8} {cy + 16} {cx} {cy + 16} "
              f"Q {cx + 8} {cy + 16} {cx + 11} {cy + 9} "
              f"Q {cx + 14} {cy + 2} {cx + 4} {cy - 7} "
              f"L {cx + 4} {cy - 16}")
    liquid = (f"M {cx - 11.5} {cy + 6} Q {cx} {cy + 2} {cx + 11.5} {cy + 6} "
              f"Q {cx + 9} {cy + 15} {cx} {cy + 15} "
              f"Q {cx - 9} {cy + 15} {cx - 11.5} {cy + 6} Z")
    p = [A.fill_path(liquid, PALETTE["gold"], 0.55),
         A.stroke(body_d, PALETTE["ink"], 2.0),
         A.stroke(f"M {cx - 6} {cy - 17.5} L {cx + 6} {cy - 17.5}",
                  PALETTE["ink"], 2.4),
         f'<circle cx="{cx - 3}" cy="{cy + 8}" r="1.6" fill="#ffffff" '
         f'opacity="0.8"><animate attributeName="cy" '
         f'values="{cy + 10};{cy + 4};{cy + 10}" dur="3.4s" '
         f'repeatCount="indefinite"/></circle>']
    return "".join(p)


def stack_panel():
    W, H = 1000, 400
    body = [A.paper_bg(W, H, seed=6)]
    # 标题
    body.append(A.magic_circle(500, 52, 34, seed=13, opacity=0.16,
                               dur_outer=60, dur_inner=45, sw=1.1,
                               color=PALETTE["roxy"]))
    body.append(A.text(500, 60, STACK_TITLE, 30, weight="bold", spacing="8"))
    body.append(A.text(500, 86, STACK_TITLE_SUB, 13, color=PALETTE["ink_soft"],
                       spacing="3"))
    body.append(A.stroke(A.wobbly_line(360, 100, 640, 100, seed=19, amp=1.5),
                         PALETTE["gold"], 1.8, opacity=0.75))

    doodles = [_doodle_chipset, _doodle_gear, _doodle_potion]
    col_w = 300
    x0 = (W - col_w * 3 - 40) / 2
    for gi, (gname, gcolor_key, items) in enumerate(STACK_GROUPS):
        gcolor = PALETTE[gcolor_key]
        gx = x0 + gi * (col_w + 20)
        # 组底水彩
        body.append(A.watercolor_blob(gx + col_w / 2, 250, 120, gcolor,
                                      seed=41 + gi, opacity=0.07))
        # 组头：图标 + 名 + 下划线
        body.append(doodles[gi](gx + 44, 152))
        body.append(A.text(gx + 80, 158, gname, 21, weight="bold",
                           anchor="start"))
        body.append(A.stroke(A.wobbly_line(gx + 78, 172, gx + 78 + 120, 172,
                                           seed=45 + gi, amp=1.2),
                             gcolor, 2.4, opacity=0.85))
        # 2 列 × 3 行芯片
        chip_w, chip_h = 132, 38
        for i, item in enumerate(items):
            cxp = gx + 8 + (i % 2) * (chip_w + 14)
            cyp = 196 + (i // 2) * (chip_h + 16)
            body.append(_chip(cxp, cyp, chip_w, chip_h, item, gcolor,
                              seed=100 + gi * 10 + i))
        # 组内小星
        body.append(A.sparkle(gx + col_w - 18, 136, 5, color=gcolor,
                              seed=60 + gi, delay=gi * 0.9))
    return A.svg_doc(W, H, "".join(body), font_b64=FONT_M,
                     title="tech stack grimoire")


# ============================================================== 项目卡片 ==

def _doodle_mic(cx, cy):
    p = [A.stroke(A.wobbly_rect_d(cx - 9, cy - 22, 18, 28, seed=3, amp=1.0),
                  PALETTE["ink"], 2.0),
         A.stroke(f"M {cx - 5} {cy - 15} L {cx + 5} {cy - 15} "
                  f"M {cx - 5} {cy - 8} L {cx + 5} {cy - 8} "
                  f"M {cx - 5} {cy - 1} L {cx + 5} {cy - 1}",
                  PALETTE["ink"], 1.2, opacity=0.55),
         A.stroke(f"M {cx - 15} {cy - 2} Q {cx - 15} {cy + 14} {cx} {cy + 14} "
                  f"Q {cx + 15} {cy + 14} {cx + 15} {cy - 2}",
                  PALETTE["ink"], 2.0),
         A.stroke(f"M {cx} {cy + 14} L {cx} {cy + 22} M {cx - 8} {cy + 23} "
                  f"L {cx + 8} {cy + 23}", PALETTE["ink"], 2.0)]
    # 声波
    for i, r in enumerate((24, 30)):
        p.append(
            f'<path d="M {cx + r} {cy - 16} Q {cx + r + 6} {cy - 6} '
            f'{cx + r} {cy + 4}" fill="none" stroke="{PALETTE["roxy"]}" '
            f'stroke-width="1.8" stroke-linecap="round" opacity="0.7">'
            f'<animate attributeName="opacity" values="0.15;0.8;0.15" '
            f'dur="2.4s" begin="{i * 0.5}s" repeatCount="indefinite"/></path>')
    return "".join(p)


def _doodle_keyboard(cx, cy):
    p = [A.stroke(A.wobbly_rect_d(cx - 26, cy - 12, 52, 26, seed=8, amp=1.0),
                  PALETTE["ink"], 2.0)]
    rnd = random.Random(12)
    for r in range(2):
        for c in range(6):
            kx = cx - 21 + c * 8
            ky = cy - 7 + r * 8
            p.append(A.stroke(A.wobbly_rect_d(kx, ky, 5.5, 5.5,
                                              seed=rnd.randint(1, 999),
                                              amp=0.5),
                              PALETTE["ink"], 1.0, opacity=0.6))
    p.append(A.stroke(f"M {cx - 12} {cy + 8} L {cx + 12} {cy + 8}",
                      PALETTE["ink"], 1.4, opacity=0.7))
    # 输入提示光标
    p.append(f'<rect x="{cx + 18}" y="{cy - 24}" width="7" height="3" '
             f'fill="{PALETTE["grass_deep"]}"><animate attributeName="opacity" '
             f'values="1;0;1" dur="1.6s" repeatCount="indefinite"/></rect>')
    p.append(A.text(cx - 2, cy - 19, "拼", 13, color=PALETTE["grass_deep"]))
    return "".join(p)


def _doodle_terminal(cx, cy):
    p = [A.stroke(A.wobbly_rect_d(cx - 26, cy - 19, 52, 38, seed=9, amp=1.0),
                  PALETTE["ink"], 2.0),
         A.stroke(f"M {cx - 26} {cy - 10} L {cx + 26} {cy - 10}",
                  PALETTE["ink"], 1.3, opacity=0.6)]
    for i, col in enumerate((PALETTE["red"], PALETTE["gold"],
                             PALETTE["grass"])):
        p.append(f'<circle cx="{cx - 20 + i * 7}" cy="{cy - 14.5}" r="2" '
                 f'fill="{col}"/>')
    p.append(A.text(cx - 20, cy + 3, ">_", 12, color=PALETTE["grass_deep"],
                    anchor="start", weight="bold"))
    p.append(f'<rect x="{cx - 4}" y="{cy - 4}" width="6" height="9" '
             f'fill="{PALETTE["grass_deep"]}" opacity="0.85">'
             f'<animate attributeName="opacity" values="0.85;0;0.85" '
             f'dur="1.4s" repeatCount="indefinite"/></rect>')
    p.append(A.stroke(f"M {cx - 20} {cy + 12} L {cx + 2} {cy + 12}",
                      PALETTE["ink"], 1.2, opacity=0.4))
    return "".join(p)


def project_card(spec, accent):
    W, H = 490, 168
    body = [A.paper_bg(W, H, rx=12, seed=7)]
    body.append(A.watercolor_blob(70, H / 2, 64, accent, seed=21, opacity=0.11))
    doodle = {"mic": _doodle_mic, "keyboard": _doodle_keyboard,
              "terminal": _doodle_terminal}[spec["doodle"]]
    body.append(doodle(72, H / 2 - 4))
    tx = 150
    body.append(A.text(tx, 52, spec["repo"], 23, weight="bold", anchor="start"))
    body.append(A.stroke(A.wobbly_line(tx, 64, tx + 200, 64, seed=31, amp=1.2),
                         accent, 2.0, opacity=0.8))
    body.append(A.text(tx, 94, spec["desc"], 17, anchor="start"))
    body.append(A.text(tx, 118, spec["desc2"], 13, color=PALETTE["ink_soft"],
                       anchor="start"))
    # 语言徽章
    lcolor = LANG_COLORS.get(spec["lang"], PALETTE["ink_soft"])
    body.append(f'<circle cx="{tx + 8}" cy="141" r="4.5" fill="{lcolor}"/>')
    body.append(A.text(tx + 19, 146, spec["lang"], 13,
                       color=PALETTE["ink_soft"], anchor="start"))
    body.append(A.sparkle(W - 34, 34, 5, color=accent, seed=25, delay=0.8))
    # 右下角小箭头暗示可点
    body.append(A.stroke(f"M {W - 44} {H - 32} L {W - 28} {H - 32} "
                         f"M {W - 33} {H - 38} L {W - 28} {H - 32} "
                         f"L {W - 33} {H - 26}", PALETTE["ink_soft"], 1.8,
                         opacity=0.7))
    return A.svg_doc(W, H, "".join(body), font_b64=FONT_M,
                     title=spec["repo"])


# ================================================================== 页脚 ==

def _traveler(cx, cy, scale=1.0):
    """持杖旅人剪影（原创小人）：斗篷 + 法杖 + 顶端光球。"""
    s = scale
    ink = "#3c3529"
    p = []
    # 斗篷身体
    p.append(A.fill_path(
        f"M {cx} {cy - 30*s} Q {cx + 12*s} {cy - 26*s} {cx + 11*s} {cy - 8*s} "
        f"Q {cx + 13*s} {cy} {cx + 9*s} {cy} L {cx - 10*s} {cy} "
        f"Q {cx - 13*s} {cy - 2*s} {cx - 11*s} {cy - 10*s} "
        f"Q {cx - 12*s} {cy - 26*s} {cx} {cy - 30*s} Z", ink, 0.92))
    # 头 + 兜帽尖
    p.append(A.fill_path(A.wobbly_circle_d(cx, cy - 36*s, 7.5*s, seed=3,
                                           irregular=0.06), ink, 0.92))
    p.append(A.fill_path(
        f"M {cx - 6*s} {cy - 41*s} Q {cx} {cy - 48*s} {cx + 7*s} {cy - 39*s} "
        f"Q {cx + 2*s} {cy - 44*s} {cx - 6*s} {cy - 41*s} Z", ink, 0.92))
    # 法杖
    sx = cx + 17 * s
    p.append(A.stroke(f"M {sx} {cy} L {sx + 3*s} {cy - 46*s}", ink, 2.6 * s))
    p.append(f'<circle cx="{sx + 3.6*s}" cy="{cy - 50*s}" r="{4.2*s}" '
             f'fill="{PALETTE["glow"]}" filter="url(#bigglow)">'
             f'<animate attributeName="opacity" values="0.55;1;0.55" '
             f'dur="3.6s" repeatCount="indefinite"/></circle>')
    return "".join(p)


def footer():
    W, H = 1000, 190
    top, mid, bot = SKY["dusk"]
    body = [f'''
  <defs>
    <linearGradient id="fsky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{mid}"/>
      <stop offset="1" stop-color="{top}"/>
    </linearGradient>
    <clipPath id="fround"><rect width="{W}" height="{H}" rx="16"/></clipPath>
  </defs>
  <g clip-path="url(#fround)">
  <rect width="{W}" height="{H}" fill="url(#fsky)"/>''']
    # 落日
    body.append(f'<circle cx="760" cy="118" r="34" fill="#ffdf9e" '
                f'opacity="0.9" filter="url(#bigglow)"/>')
    # 云与鸟
    body.append(A.cloud(220, 52, 0.9, "#fbe3c4", 0.7, seed=71, drift=20, dur=50))
    body.append(A.cloud(560, 38, 0.65, "#fbe3c4", 0.6, seed=72, drift=-16, dur=44))
    for i, (bx, by) in enumerate([(806, 42), (836, 34), (862, 48)]):
        body.append(A.stroke(f"M {bx - 7} {by} Q {bx} {by - 6} {bx + 7} {by} ",
                             "#5d4a38", 1.6, opacity=0.8 - i * 0.15))
    # 山丘与草地
    body.append(A.hills(W, 128, 14, "#b5975f", seed=73, opacity=0.55))
    body.append(A.hills(W, 148, 10, "#8fae6a", seed=74, opacity=0.9))
    body.append(A.hills(W, 166, 7, "#6f9455", seed=75))
    body.append(A.grass_tufts(W, 182, 30, seed=76, color="#4d6e3f"))
    # 旅人
    body.append(_traveler(500, 168, 1.0))
    # 粒子与星
    rnd = random.Random(7)
    for i in range(8):
        body.append(A.dot_particle(rnd.uniform(80, W - 80),
                                   rnd.uniform(90, 170),
                                   rnd.uniform(1.2, 2.2), "#fff2cf",
                                   seed=500 + i, rise=rnd.uniform(10, 18)))
    body.append(A.sparkle(120, 42, 5, color="#fff2cf", seed=81, delay=0.4))
    body.append(A.sparkle(880, 58, 5, color="#fff2cf", seed=82, delay=1.5))
    # 文字
    body.append(A.text(500, 58, FOOTER_QUOTE, 20, color="#4a3a2a",
                       spacing="2"))
    body.append(A.text(500, 84, FOOTER_SIGN, 14, color="#4a3a2a", opacity=0.8))
    body.append(A.stroke(A.wobbly_rect_d(8, 8, W - 16, H - 16, seed=15),
                         "#4a3a2a", 2.0, opacity=0.5))
    body.append('</g>')
    return A.svg_doc(W, H, "".join(body), font_b64=FONT_M, title="footer scene")


# ======================================================== 素材位回退插画 ==

def fallback_art():
    """官方素材位的原创回退插画：悬浮魔导书 + 光球 + 魔法阵。"""
    W, H = 480, 640
    cx = W / 2
    body = [A.paper_bg(W, H, rx=14, seed=17, color=PALETTE["paper"])]
    # 背景水彩
    body.append(A.watercolor_blob(cx, 260, 150, PALETTE["roxy"], seed=91,
                                  opacity=0.09, layers=3))
    body.append(A.watercolor_blob(140, 500, 100, PALETTE["gold"], seed=92,
                                  opacity=0.09, layers=2))
    body.append(A.watercolor_blob(360, 540, 80, PALETTE["grass"], seed=93,
                                  opacity=0.07, layers=2))
    # 魔法阵背景
    body.append(A.magic_circle(cx, 300, 168, seed=19, opacity=0.32,
                               dur_outer=90, dur_inner=70,
                               color=PALETTE["roxy"], sw=1.4))
    # ---- 悬浮的摊开魔导书 ----
    by = 330  # 书脊底部
    book = []
    # 封面（略大于纸页）
    book.append(A.fill_path(
        f"M {cx} {by + 10} Q {cx - 60} {by - 4} {cx - 118} {by + 4} "
        f"L {cx - 118} {by - 40} Q {cx - 60} {by - 50} {cx} {by - 36} "
        f"Q {cx + 60} {by - 50} {cx + 118} {by - 40} L {cx + 118} {by + 4} "
        f"Q {cx + 60} {by - 4} {cx} {by + 10} Z", PALETTE["roxy"], 0.85))
    # 左右纸页
    for sign in (-1, 1):
        book.append(A.fill_path(
            f"M {cx} {by} Q {cx + sign * 55} {by - 14} {cx + sign * 106} "
            f"{by - 6} L {cx + sign * 106} {by - 44} "
            f"Q {cx + sign * 55} {by - 56} {cx} {by - 42} Z", "#fdf8ea", 1.0))
        book.append(A.stroke(
            f"M {cx} {by} Q {cx + sign * 55} {by - 14} {cx + sign * 106} "
            f"{by - 6} L {cx + sign * 106} {by - 44} "
            f"Q {cx + sign * 55} {by - 56} {cx} {by - 42}",
            PALETTE["ink"], 2.0))
        # 页面文字线
        for li in range(3):
            yy = by - 36 + li * 9
            book.append(A.stroke(A.wobbly_line(
                cx + sign * 14, yy + 3, cx + sign * 88, yy - 2,
                seed=200 + li * 7 + (0 if sign < 0 else 3), amp=0.8),
                PALETTE["ink_soft"], 1.1, opacity=0.5))
    book.append(A.stroke(f"M {cx} {by} L {cx} {by - 42}", PALETTE["ink"], 2.0,
                         opacity=0.8))
    # 光球悬浮于书页之上
    book.append(f'<circle cx="{cx}" cy="{by - 96}" r="15" '
                f'fill="{PALETTE["glow"]}" opacity="0.9" '
                f'filter="url(#bigglow)">'
                f'<animate attributeName="r" values="13.5;16;13.5" dur="4s" '
                f'repeatCount="indefinite"/></circle>')
    book.append(f'<circle cx="{cx - 4}" cy="{by - 100}" r="4.5" '
                f'fill="#ffffff" opacity="0.9"/>')
    # 从书页升起的微光符文
    for i in range(4):
        rx = cx - 54 + i * 36
        rune_d = A._rune(rx, by - 64, 6, 300 + i)
        book.append(
            f'<path d="{rune_d}" fill="none" stroke="{PALETTE["roxy"]}" '
            f'stroke-width="1.5" stroke-linecap="round" opacity="0">'
            f'<animate attributeName="opacity" values="0;0.8;0" '
            f'dur="{4.5 + i * 0.8:.1f}s" begin="{i * 1.1:.1f}s" '
            f'repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 0; 0 -26" dur="{4.5 + i * 0.8:.1f}s" '
            f'begin="{i * 1.1:.1f}s" repeatCount="indefinite"/></path>')
    # 书整体轻浮
    body.append(f'<g>{"".join(book)}'
                f'<animateTransform attributeName="transform" '
                f'type="translate" values="0 0; 0 -9; 0 0" dur="6.5s" '
                f'repeatCount="indefinite" calcMode="spline" '
                f'keySplines="0.45 0 0.55 1; 0.45 0 0.55 1"/></g>')
    # 漂浮水珠
    for i, (wx, wy, wr) in enumerate([(120, 200, 9), (368, 176, 7),
                                      (350, 330, 6), (116, 350, 5)]):
        body.append(
            f'<g><ellipse cx="{wx}" cy="{wy}" rx="{wr}" ry="{wr * 1.15}" '
            f'fill="{PALETTE["glow"]}" opacity="0.5"/>'
            f'<ellipse cx="{wx}" cy="{wy}" rx="{wr}" ry="{wr * 1.15}" '
            f'fill="none" stroke="{PALETTE["roxy"]}" stroke-width="1.4" '
            f'opacity="0.7"/>'
            f'<circle cx="{wx - wr * 0.3}" cy="{wy - wr * 0.4}" r="{wr * 0.25}" '
            f'fill="#ffffff" opacity="0.9"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 0; 0 {-8 - i * 2}; 0 0" dur="{5 + i * 1.3:.1f}s" '
            f'repeatCount="indefinite" calcMode="spline" '
            f'keySplines="0.45 0 0.55 1; 0.45 0 0.55 1"/></g>')
    # 底部粒子
    rnd = random.Random(31)
    for i in range(10):
        body.append(A.dot_particle(rnd.uniform(60, W - 60),
                                   rnd.uniform(360, 580),
                                   rnd.uniform(1.2, 2.4), PALETTE["glow"],
                                   seed=700 + i, rise=rnd.uniform(14, 30)))
    return A.svg_doc(W, H, "".join(body), title="original placeholder art")


# =================================================================== main ==

if __name__ == "__main__":
    FONT_M = Path(sys.argv[1]).read_text().strip()
    OUT.mkdir(exist_ok=True)
    accents = [PALETTE["roxy"], PALETTE["grass_deep"], PALETTE["gold"]]
    outputs = {
        "divider.svg": divider(),
        "icon-about.svg": icon_about(),
        "icon-stack.svg": icon_stack(),
        "icon-works.svg": icon_works(),
        "icon-stats.svg": icon_stats(),
        "stack-panel.svg": stack_panel(),
        "footer.svg": footer(),
        "fallback-art.svg": fallback_art(),
        "hero-fallback.svg": cards.build_hero("day", FONT_M),
        "stats-sample.svg": cards.build_stats(cards.SAMPLE_STATS, FONT_M),
    }
    for i, spec in enumerate(PROJECT_CARDS):
        outputs[f"card-{spec['slug']}.svg"] = project_card(spec, accents[i])
    for name, svg in outputs.items():
        p = OUT / name
        p.write_text(svg, encoding="utf-8")
        print(f"{name:24s} {len(svg)/1024:8.1f} KiB")
