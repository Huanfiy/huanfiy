# -*- coding: utf-8 -*-
"""生成 README 用的全部静态 SVG 资产到 ../assets/。

用法: python genart.py <font_medium.b64>
"""
import math
import random
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import artlib as A
import cards
from content import (PALETTE, SKY, THEME_INK, LANG_COLORS, SECTIONS,
                     FOCUS_TAGS, STACK_GROUPS, PROJECT_CARDS, FOOTER_QUOTE,
                     FOOTER_SIGN)

OUT = Path(__file__).parent.parent / "assets"
FONT_M = ""


def _seed(s):
    """字符串 → 稳定 seed（不用内建 hash，避免跨进程随机化）。"""
    return zlib.crc32(s.encode("utf-8")) % 1000


# ============================================================== 章节图标 ==
# 每个图标画在以 (x, y) 为左上角的 40×40 盒子里，ink 为主题墨色。

def _icon_quill(x, y, ink):
    return "".join([
        A.stroke(f"M {x+30} {y+6} Q {x+20} {y+10} {x+13} {y+22} Q {x+10} {y+28} "
                 f"{x+9} {y+33}", PALETTE["roxy"], 2.3),
        A.stroke(f"M {x+30} {y+6} Q {x+26} {y+16} {x+17} {y+26} M {x+25} {y+12} "
                 f"Q {x+21} {y+14} {x+15} {y+21} M {x+28} {y+9} Q {x+24} {y+17} "
                 f"{x+19} {y+24}", PALETTE["roxy"], 1.2, opacity=0.7),
        A.stroke(f"M {x+9} {y+33} L {x+7} {y+36}", ink, 2.0),
        f'<circle cx="{x+12}" cy="{y+35.5}" r="1.7" fill="{ink}" opacity="0.7"/>',
    ])


def _icon_grimoire(x, y, ink):
    return "".join([
        A.stroke(A.wobbly_rect_d(x + 8, y + 8, 24, 27, seed=3, amp=0.9), ink, 2.0),
        A.stroke(f"M {x+12} {y+8} L {x+12} {y+35}", ink, 1.2, opacity=0.55),
        A.fill_path(f"M {x+24} {y+8} L {x+24} {y+18} L {x+27} {y+15} L {x+30} "
                    f"{y+18} L {x+30} {y+8} Z", PALETTE["red"], 0.85),
        A.sparkle(x + 20, y + 25, 4.5, color=PALETTE["gold"], seed=5, dur=2.8),
    ])


def _icon_chest(x, y, ink):
    return "".join([
        A.stroke(A.wobbly_rect_d(x + 7, y + 18, 26, 15, seed=4, amp=0.9), ink, 2.0),
        A.stroke(f"M {x+7} {y+18} Q {x+20} {y+6} {x+33} {y+18}", ink, 2.0),
        A.stroke(f"M {x+20} {y+18} L {x+20} {y+33} M {x+7} {y+25} L {x+33} {y+25}",
                 ink, 1.1, opacity=0.45),
        A.fill_path(f"M {x+17.5} {y+21} L {x+22.5} {y+21} L {x+22.5} {y+27} "
                    f"L {x+20} {y+29} L {x+17.5} {y+27} Z", PALETTE["gold"], 0.9),
        A.sparkle(x + 31, y + 10, 3.8, seed=6, delay=1.1),
    ])


def _icon_orb(x, y, ink):
    return "".join([
        A.stroke(A.wobbly_circle_d(x + 20, y + 17, 11, seed=7), PALETTE["roxy"], 2.0),
        A.fill_path(A.wobbly_circle_d(x + 20, y + 17, 9.5, seed=8, irregular=0.05),
                    PALETTE["glow"], 0.28),
        A.stroke(f"M {x+14} {y+12} Q {x+17} {y+9} {x+21} {y+9.5}", "#ffffff",
                 1.5, opacity=0.9),
        A.stroke(f"M {x+11} {y+30} Q {x+20} {y+25} {x+29} {y+30} L {x+27} {y+34} "
                 f"L {x+13} {y+34} Z", ink, 1.9),
        A.sparkle(x + 20, y + 17, 4.2, color="#ffffff", seed=9, dur=2.2),
    ])


_ICONS = {"quill": _icon_quill, "grimoire": _icon_grimoire,
          "chest": _icon_chest, "orb": _icon_orb}


# ============================================================== 章节标题 ==

def section_header(zh, en, icon, theme):
    """透明底章节标题：上方留白做节间距，图标 + 中文 + 英文小字 + 渐隐线。"""
    W, H = 1000, 84
    t = THEME_INK[theme]
    y0 = 34  # 内容顶
    body = [_ICONS[icon](8, y0 - 6, t["ink"])]
    tx = 56
    body.append(A.text(tx, y0 + 24, zh, 27, color=t["ink"], weight="bold",
                       anchor="start", spacing="2"))
    zw = A.text_w(zh, 27, spacing=2)
    ex = tx + zw + 14
    body.append(A.text(ex, y0 + 23, en, 12.5, color=t["soft"], anchor="start",
                       spacing="2.5", opacity=0.95))
    ew = A.text_w(en, 12.5, spacing=2.5)
    lx = ex + ew + 22
    body.append(A.fade_line(lx, y0 + 18, W - 8, t["line"], w=1.4, opacity=0.9,
                            seed=_seed(zh), amp=1.0, fade_out=0.45))
    body.append(A.sparkle(lx + 4, y0 + 18, 4.2, color=PALETTE["gold"],
                          seed=_seed(en), dur=3.4, lo=0.35))
    # 标题下的手绘短线（强调）
    body.append(A.stroke(A.wobbly_line(tx, y0 + 34, tx + zw, y0 + 34,
                                       seed=_seed(zh) + 7, amp=1.0),
                         PALETTE["roxy"], 2.0, opacity=0.6))
    return A.svg_doc(W, H, "".join(body), font_b64=FONT_M, title=f"{zh} · {en}",
                     grain=False)


# ============================================================ 关于我标签 ==

def focus_tags(theme):
    t = THEME_INK[theme]
    accents = [PALETTE["roxy"], PALETTE["grass_deep"], PALETTE["gold"],
               PALETTE["lavender"]]
    H = 42
    x = 2
    parts = []
    for i, label in enumerate(FOCUS_TAGS):
        svg, w = A.chip(x, 5, label, 14, t["ink"], accents[i % 4], seed=200 + i,
                        h=31, fill=t["chip"], fill_opacity=0.5,
                        tint_opacity=0.14, edge_opacity=0.55)
        parts.append(svg)
        x += w + 10
    W = int(x + 4)
    return A.svg_doc(W, H, "".join(parts), font_b64=FONT_M,
                     title=" · ".join(FOCUS_TAGS), grain=False)


# ============================================================ 技术栈面板 ==

def _doodle_chipset(cx, cy):
    """芯片：方体 + 引脚 + 核心星。"""
    p = [A.stroke(A.wobbly_rect_d(cx - 11, cy - 11, 22, 22, seed=3, amp=0.9),
                  PALETTE["ink"], 1.9)]
    for i in range(3):
        off = -6 + i * 6
        p.append(A.stroke(f"M {cx + off} {cy - 11} L {cx + off} {cy - 16} "
                          f"M {cx + off} {cy + 11} L {cx + off} {cy + 16}",
                          PALETTE["ink"], 1.4, opacity=0.8))
        p.append(A.stroke(f"M {cx - 11} {cy + off} L {cx - 16} {cy + off} "
                          f"M {cx + 11} {cy + off} L {cx + 16} {cy + off}",
                          PALETTE["ink"], 1.4, opacity=0.8))
    p.append(A.sparkle(cx, cy, 4.5, color=PALETTE["roxy"], seed=4, dur=3.0))
    return "".join(p)


def _doodle_gear(cx, cy):
    p = [A.stroke(A.wobbly_circle_d(cx, cy, 10, seed=5), PALETTE["ink"], 1.9),
         A.stroke(A.wobbly_circle_d(cx, cy, 3.8, seed=6, irregular=0.06),
                  PALETTE["ink"], 1.5)]
    for i in range(8):
        a = math.tau * i / 8 + 0.2
        x1, y1 = cx + 10 * math.cos(a), cy + 10 * math.sin(a)
        x2, y2 = cx + 14.5 * math.cos(a), cy + 14.5 * math.sin(a)
        p.append(A.stroke(f"M {x1:.1f} {y1:.1f} L {x2:.1f} {y2:.1f}",
                          PALETTE["ink"], 2.0))
    g = "".join(p)
    return (f'<g>{g}<animateTransform attributeName="transform" type="rotate" '
            f'from="0 {cx} {cy}" to="360 {cx} {cy}" dur="26s" '
            f'repeatCount="indefinite"/></g>')


def _doodle_potion(cx, cy):
    body_d = (f"M {cx - 3.5} {cy - 14} L {cx - 3.5} {cy - 6} "
              f"Q {cx - 12} {cy + 2} {cx - 9.5} {cy + 8} "
              f"Q {cx - 7} {cy + 14} {cx} {cy + 14} "
              f"Q {cx + 7} {cy + 14} {cx + 9.5} {cy + 8} "
              f"Q {cx + 12} {cy + 2} {cx + 3.5} {cy - 6} "
              f"L {cx + 3.5} {cy - 14}")
    liquid = (f"M {cx - 10} {cy + 5} Q {cx} {cy + 2} {cx + 10} {cy + 5} "
              f"Q {cx + 8} {cy + 13} {cx} {cy + 13} "
              f"Q {cx - 8} {cy + 13} {cx - 10} {cy + 5} Z")
    p = [A.fill_path(liquid, PALETTE["gold"], 0.55),
         A.stroke(body_d, PALETTE["ink"], 1.9),
         A.stroke(f"M {cx - 5.5} {cy - 15.5} L {cx + 5.5} {cy - 15.5}",
                  PALETTE["ink"], 2.2),
         f'<circle cx="{cx - 2.5}" cy="{cy + 7}" r="1.4" fill="#ffffff" '
         f'opacity="0.8"><animate attributeName="cy" '
         f'values="{cy + 9};{cy + 4};{cy + 9}" dur="3.4s" '
         f'repeatCount="indefinite"/></circle>']
    return "".join(p)


def stack_panel():
    W = 1000
    col_w, gap, x0 = 300, 30, 20
    doodles = [_doodle_chipset, _doodle_gear, _doodle_potion]
    cols = []
    max_bottom = 0
    for gi, (gname, gcolor_key, items) in enumerate(STACK_GROUPS):
        gcolor = PALETTE[gcolor_key]
        gx = x0 + gi * (col_w + gap)
        parts = [doodles[gi](gx + 26, 54)]
        parts.append(A.text(gx + 52, 61, gname, 20, weight="bold",
                            anchor="start"))
        gw = A.text_w(gname, 20)
        parts.append(A.stroke(A.wobbly_line(gx + 52, 71, gx + 52 + gw, 71,
                                            seed=45 + gi, amp=1.1),
                              gcolor, 2.2, opacity=0.85))
        # 自适应宽度标签流式排布
        cx, cy = gx + 4, 92
        chip_h, hgap, vgap = 32, 9, 11
        for i, item in enumerate(items):
            w = A.text_w(item, 14.5) + 28
            if cx + w > gx + col_w - 2:
                cx, cy = gx + 4, cy + chip_h + vgap
            svg, w = A.chip(cx, cy, item, 14.5, PALETTE["ink"], gcolor,
                            seed=100 + gi * 10 + i, h=chip_h, pad=14,
                            fill_opacity=0.5, tint_opacity=0.11,
                            edge_opacity=0.55, sw=1.25)
            parts.append(svg)
            cx += w + hgap
        max_bottom = max(max_bottom, cy + chip_h)
        cols.append((gx, gcolor, gi, "".join(parts)))
    H = int(max_bottom + 30)
    body = [A.paper_bg(W, H, seed=6)]
    for gx, gcolor, gi, svg in cols:
        body.append(A.watercolor_blob(gx + col_w / 2, H / 2 + 10, 112, gcolor,
                                      seed=41 + gi, opacity=0.06, layers=2))
        body.append(svg)
        body.append(A.sparkle(gx + col_w - 12, 40, 4.5, color=gcolor,
                              seed=60 + gi, delay=gi * 0.9))
    # 列间细分隔线
    for gi in range(1, 3):
        sx = x0 + gi * (col_w + gap) - gap / 2
        body.append(A.stroke(A.wobbly_line(sx, 44, sx, H - 40, seed=80 + gi,
                                           amp=1.0),
                             PALETTE["ink"], 1.0, opacity=0.16))
    return A.svg_doc(W, H, "".join(body), font_b64=FONT_M,
                     title="tech stack", grain=(4, 4, W - 8, H - 8, 14))


# ============================================================== 项目卡片 ==

def _doodle_dashboard(cx, cy):
    """看板：面板 + 呼吸的柱状图 + 折线与亮点。"""
    p = [A.stroke(A.wobbly_rect_d(cx - 26, cy - 19, 52, 38, seed=3, amp=1.0),
                  PALETTE["ink"], 2.0),
         A.stroke(f"M {cx - 26} {cy - 11} L {cx + 26} {cy - 11}",
                  PALETTE["ink"], 1.2, opacity=0.55)]
    for i in range(3):
        p.append(f'<circle cx="{cx - 20 + i * 6}" cy="{cy - 15}" r="1.6" '
                 f'fill="{PALETTE["ink"]}" opacity="0.5"/>')
    base = cy + 13
    for i, h in enumerate((9, 15, 11, 19)):
        x = cx - 19 + i * 9
        p.append(
            f'<rect x="{x}" y="{base - h}" width="6" height="{h}" rx="1.5" '
            f'fill="{PALETTE["roxy"]}" opacity="0.7">'
            f'<animate attributeName="height" values="{h};{h - 4};{h}" '
            f'dur="{3.2 + i * 0.5:.1f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="y" values="{base - h};{base - h + 4};'
            f'{base - h}" dur="{3.2 + i * 0.5:.1f}s" repeatCount="indefinite"/>'
            f'</rect>')
    p.append(A.stroke(f"M {cx + 19} {cy + 10} L {cx + 19} {cy - 4} "
                      f"M {cx + 14} {cy - 4} L {cx + 24} {cy - 4} "
                      f"M {cx + 14} {cy + 1} L {cx + 24} {cy + 1} "
                      f"M {cx + 14} {cy + 6} L {cx + 24} {cy + 6}",
                      PALETTE["ink"], 1.1, opacity=0.35))
    p.append(A.stroke(f"M {cx - 21} {cy + 2} Q {cx - 12} {cy - 6} {cx - 4} {cy - 1} "
                      f"T {cx + 11} {cy - 8}", PALETTE["gold"], 1.7, opacity=0.9))
    p.append(A.sparkle(cx + 11, cy - 8, 3.6, color=PALETTE["gold"], seed=14,
                       dur=2.6, lo=0.4))
    return "".join(p)


def _doodle_keyboard(cx, cy):
    p = [A.stroke(A.wobbly_rect_d(cx - 26, cy - 8, 52, 26, seed=8, amp=1.0),
                  PALETTE["ink"], 2.0)]
    rnd = random.Random(12)
    for r in range(2):
        for c in range(6):
            kx = cx - 21 + c * 8
            ky = cy - 3 + r * 8
            p.append(A.stroke(A.wobbly_rect_d(kx, ky, 5.5, 5.5,
                                              seed=rnd.randint(1, 999),
                                              amp=0.5),
                              PALETTE["ink"], 1.0, opacity=0.6))
    p.append(A.stroke(f"M {cx - 12} {cy + 12} L {cx + 12} {cy + 12}",
                      PALETTE["ink"], 1.4, opacity=0.7))
    p.append(f'<rect x="{cx + 18}" y="{cy - 20}" width="7" height="3" '
             f'fill="{PALETTE["grass_deep"]}"><animate attributeName="opacity" '
             f'values="1;0;1" dur="1.6s" repeatCount="indefinite"/></rect>')
    p.append(A.text(cx - 2, cy - 15, "拼", 13, color=PALETTE["grass_deep"]))
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
    """竖版卡：图案在上、文字在下，1/3 宽度下文字仍可读。"""
    W, H = 320, 236
    cx = W / 2
    body = [A.paper_bg(W, H, rx=14, seed=7, sw=1.7)]
    body.append(A.watercolor_blob(cx, 72, 46, accent, seed=21, opacity=0.13))
    doodle = {"dashboard": _doodle_dashboard, "keyboard": _doodle_keyboard,
              "terminal": _doodle_terminal}[spec["doodle"]]
    body.append(doodle(cx, 72))
    body.append(A.text(cx, 138, spec["repo"], 21, weight="bold"))
    tw = A.text_w(spec["repo"], 21)
    body.append(A.stroke(A.wobbly_line(cx - tw / 2, 148, cx + tw / 2, 148,
                                       seed=31, amp=1.0),
                         accent, 2.0, opacity=0.8))
    body.append(A.text(cx, 172, spec["desc"], 15))
    body.append(A.text(cx, 193, spec["desc2"], 12, color=PALETTE["ink_soft"]))
    # 语言徽章（居中）
    lcolor = LANG_COLORS.get(spec["lang"], PALETTE["ink_soft"])
    lw = A.text_w(spec["lang"], 12)
    lx = cx - (lw + 12) / 2
    body.append(f'<circle cx="{lx + 4}" cy="{H - 22}" r="4" fill="{lcolor}"/>')
    body.append(A.text(lx + 12, H - 18, spec["lang"], 12,
                       color=PALETTE["ink_soft"], anchor="start"))
    body.append(A.sparkle(W - 32, 34, 4.5, color=accent, seed=25, delay=0.8))
    # 右下角小箭头暗示可点
    body.append(A.stroke(f"M {W - 40} {H - 26} L {W - 26} {H - 26} "
                         f"M {W - 31} {H - 31} L {W - 26} {H - 26} "
                         f"L {W - 31} {H - 21}", PALETTE["ink_soft"], 1.6,
                         opacity=0.7))
    return A.svg_doc(W, H, "".join(body), font_b64=FONT_M,
                     title=spec["repo"], grain=(4, 4, W - 8, H - 8, 14))


# ================================================================== 页脚 ==

def _traveler(cx, cy, scale=1.0):
    """持杖旅人剪影（原创小人）：斗篷 + 法杖 + 顶端光球。"""
    s = scale
    ink = "#3c3529"
    p = []
    p.append(A.fill_path(
        f"M {cx} {cy - 30*s} Q {cx + 12*s} {cy - 26*s} {cx + 11*s} {cy - 8*s} "
        f"Q {cx + 13*s} {cy} {cx + 9*s} {cy} L {cx - 10*s} {cy} "
        f"Q {cx - 13*s} {cy - 2*s} {cx - 11*s} {cy - 10*s} "
        f"Q {cx - 12*s} {cy - 26*s} {cx} {cy - 30*s} Z", ink, 0.92))
    p.append(A.fill_path(A.wobbly_circle_d(cx, cy - 36*s, 7.5*s, seed=3,
                                           irregular=0.06), ink, 0.92))
    p.append(A.fill_path(
        f"M {cx - 6*s} {cy - 41*s} Q {cx} {cy - 48*s} {cx + 7*s} {cy - 39*s} "
        f"Q {cx + 2*s} {cy - 44*s} {cx - 6*s} {cy - 41*s} Z", ink, 0.92))
    sx = cx + 17 * s
    p.append(A.stroke(f"M {sx} {cy} L {sx + 3*s} {cy - 46*s}", ink, 2.6 * s))
    p.append(f'<circle cx="{sx + 3.6*s}" cy="{cy - 50*s}" r="{4.2*s}" '
             f'fill="{PALETTE["glow"]}" filter="url(#bigglow)">'
             f'<animate attributeName="opacity" values="0.55;1;0.55" '
             f'dur="3.6s" repeatCount="indefinite"/></circle>')
    return "".join(p)


def footer():
    W, H = 1000, 200
    top, mid, bot = SKY["dusk"]
    body = [f'''
  <defs>
    <linearGradient id="fsky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{top}"/>
      <stop offset="0.55" stop-color="{mid}"/>
      <stop offset="1" stop-color="{bot}"/>
    </linearGradient>
    <clipPath id="fround"><rect width="{W}" height="{H}" rx="16"/></clipPath>
  </defs>
  <g clip-path="url(#fround)">
  <rect width="{W}" height="{H}" fill="url(#fsky)"/>''']
    body.append(A.horizon_glow(740, 132, 420, 110, "#ffd9a6", 0.6))
    body.append(A.star_field(W, H, 16, seed=91, color="#fff6e0", y_max=70,
                             op_lo=0.15, op_hi=0.45))
    body.append(f'<circle cx="740" cy="124" r="30" fill="#ffe3a8" '
                f'opacity="0.92" filter="url(#bigglow)"/>')
    body.append(A.cloud(220, 56, 0.95, "#fbe6cf", 0.7, seed=71, drift=20,
                        dur=50, shade="#d9aa98"))
    body.append(A.cloud(560, 40, 0.65, "#fbe6cf", 0.6, seed=72, drift=-16,
                        dur=44, shade="#d9aa98"))
    body.append(A.birds([(818, 46, 0.9), (846, 38, 0.8), (870, 52, 0.7)],
                        "#5d4a48", opacity=0.75))
    # 远山 → 雾 → 三层丘陵
    body.append(A.ridge(W, 126, 22, "#b39aa6", seed=93, opacity=0.55))
    body.append(A.mist_band(0, 110, W, 36, "#f8dfc4", opacity=0.7))
    body.append(A.hills(W, 138, 12, "#b0b57a", seed=73, opacity=0.8))
    body.append(A.mist_band(0, 132, W, 24, "#f8e6cc", opacity=0.4))
    body.append(A.hills(W, 156, 9, "#8faa6a", seed=74, opacity=0.95))
    body.append(A.hills(W, 172, 7, "#6f9455", seed=75))
    body.append(A.grass_tufts(W, 190, 30, seed=76, color="#4d6e3f"))
    body.append(_traveler(500, 176, 1.0))
    rnd = random.Random(7)
    for i in range(8):
        body.append(A.dot_particle(rnd.uniform(80, W - 80),
                                   rnd.uniform(100, 180),
                                   rnd.uniform(1.2, 2.2), "#fff2cf",
                                   seed=500 + i, rise=rnd.uniform(10, 18)))
    body.append(A.sparkle(120, 44, 4.5, color="#fff2cf", seed=81, delay=0.4))
    body.append(A.sparkle(900, 66, 4.5, color="#fff2cf", seed=82, delay=1.5))
    # 文字
    body.append(A.text(500, 62, FOOTER_QUOTE, 20, color="#463628", spacing="2"))
    body.append(A.text(500, 88, FOOTER_SIGN, 13.5, color="#463628", opacity=0.8))
    body.append(A.stroke(A.wobbly_rect_d(8, 8, W - 16, H - 16, seed=15, amp=1.3),
                         "#463628", 1.8, opacity=0.45))
    body.append('</g>')
    return A.svg_doc(W, H, "".join(body), font_b64=FONT_M, title="footer scene")


# ======================================================== 素材位回退插画 ==

def fallback_art():
    """官方素材位的原创回退插画：悬浮魔导书 + 光球 + 魔法阵。"""
    W, H = 480, 480
    cx = W / 2
    body = [A.paper_bg(W, H, rx=14, seed=17, sw=1.8)]
    body.append(A.watercolor_blob(cx, 220, 140, PALETTE["roxy"], seed=91,
                                  opacity=0.08, layers=3))
    body.append(A.watercolor_blob(110, 390, 80, PALETTE["gold"], seed=92,
                                  opacity=0.08, layers=2))
    body.append(A.watercolor_blob(380, 400, 64, PALETTE["grass"], seed=93,
                                  opacity=0.06, layers=2))
    body.append(A.magic_circle(cx, 248, 158, seed=19, opacity=0.28,
                               dur_outer=90, dur_inner=70,
                               color=PALETTE["roxy"], sw=1.3))
    by = 284  # 书脊底部
    book = []
    book.append(A.fill_path(
        f"M {cx} {by + 10} Q {cx - 60} {by - 4} {cx - 118} {by + 4} "
        f"L {cx - 118} {by - 40} Q {cx - 60} {by - 50} {cx} {by - 36} "
        f"Q {cx + 60} {by - 50} {cx + 118} {by - 40} L {cx + 118} {by + 4} "
        f"Q {cx + 60} {by - 4} {cx} {by + 10} Z", PALETTE["roxy"], 0.85))
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
        for li in range(3):
            yy = by - 36 + li * 9
            book.append(A.stroke(A.wobbly_line(
                cx + sign * 14, yy + 3, cx + sign * 88, yy - 2,
                seed=200 + li * 7 + (0 if sign < 0 else 3), amp=0.8),
                PALETTE["ink_soft"], 1.1, opacity=0.5))
    book.append(A.stroke(f"M {cx} {by} L {cx} {by - 42}", PALETTE["ink"], 2.0,
                         opacity=0.8))
    book.append(f'<circle cx="{cx}" cy="{by - 96}" r="15" '
                f'fill="{PALETTE["glow"]}" opacity="0.9" '
                f'filter="url(#bigglow)">'
                f'<animate attributeName="r" values="13.5;16;13.5" dur="4s" '
                f'repeatCount="indefinite"/></circle>')
    book.append(f'<circle cx="{cx - 4}" cy="{by - 100}" r="4.5" '
                f'fill="#ffffff" opacity="0.9"/>')
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
    body.append(f'<g>{"".join(book)}'
                f'<animateTransform attributeName="transform" '
                f'type="translate" values="0 0; 0 -9; 0 0" dur="6.5s" '
                f'repeatCount="indefinite" calcMode="spline" '
                f'keySplines="0.45 0 0.55 1; 0.45 0 0.55 1"/></g>')
    for i, (wx, wy, wr) in enumerate([(108, 160, 9), (378, 140, 7),
                                      (366, 300, 6), (100, 316, 5)]):
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
    rnd = random.Random(31)
    for i in range(10):
        body.append(A.dot_particle(rnd.uniform(60, W - 60),
                                   rnd.uniform(320, 440),
                                   rnd.uniform(1.2, 2.4), PALETTE["glow"],
                                   seed=700 + i, rise=rnd.uniform(14, 30)))
    for i, (sx, sy) in enumerate([(64, 70), (416, 56), (424, 404), (56, 424)]):
        body.append(A.sparkle(sx, sy, 5, color=PALETTE["gold"], seed=800 + i,
                              delay=i * 0.8, lo=0.2))
    return A.svg_doc(W, H, "".join(body), title="original placeholder art",
                     grain=(4, 4, W - 8, H - 8, 14))


# =================================================================== main ==

if __name__ == "__main__":
    FONT_M = Path(sys.argv[1]).read_text().strip()
    OUT.mkdir(exist_ok=True)
    accents = [PALETTE["roxy"], PALETTE["grass_deep"], PALETTE["gold"]]
    outputs = {
        "stack-panel.svg": stack_panel(),
        "footer.svg": footer(),
        "fallback-art.svg": fallback_art(),
        "hero-fallback.svg": cards.build_hero("day", FONT_M),
        "stats-sample.svg": cards.build_stats(cards.SAMPLE_STATS, FONT_M),
    }
    for theme in ("light", "dark"):
        for slug, zh, en, icon in SECTIONS:
            outputs[f"h-{slug}-{theme}.svg"] = section_header(zh, en, icon, theme)
        outputs[f"tags-{theme}.svg"] = focus_tags(theme)
    for i, spec in enumerate(PROJECT_CARDS):
        outputs[f"card-{spec['slug']}.svg"] = project_card(spec, accents[i])
    for old in OUT.glob("*.svg"):
        if old.name not in outputs:
            old.unlink()
            print(f"{old.name:24s} removed")
    for name, svg in outputs.items():
        p = OUT / name
        p.write_text(svg, encoding="utf-8")
        print(f"{name:24s} {len(svg)/1024:8.1f} KiB")
