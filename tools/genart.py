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


def _doodle_usb_debugger(cx, cy):
    """USB 调试器：接口 + 芯片 + 多路引脚。"""
    ink, accent = PALETTE["ink"], PALETTE["grass_deep"]
    p = [A.stroke(A.wobbly_rect_d(cx - 22, cy - 17, 44, 34, seed=8, amp=1.0),
                  ink, 2.0),
         A.stroke(A.wobbly_rect_d(cx - 34, cy - 8, 12, 16, seed=9, amp=0.5),
                  ink, 1.7),
         A.stroke(f"M {cx - 30} {cy - 4} L {cx - 26} {cy - 4} "
                  f"M {cx - 30} {cy + 4} L {cx - 26} {cy + 4}",
                  ink, 1.3, opacity=0.65),
         A.stroke(A.wobbly_rect_d(cx - 9, cy - 9, 18, 18, seed=10, amp=0.6),
                  ink, 1.6)]
    for off in (-6, 0, 6):
        p.append(A.stroke(f"M {cx + off} {cy - 9} L {cx + off} {cy - 13} "
                          f"M {cx + off} {cy + 9} L {cx + off} {cy + 13}",
                          ink, 1.1, opacity=0.75))
        p.append(A.stroke(f"M {cx - 13} {cy + off} L {cx - 9} {cy + off} "
                          f"M {cx + 9} {cy + off} L {cx + 13} {cy + off}",
                          ink, 1.1, opacity=0.75))
    for off in (-10, 0, 10):
        p.append(A.stroke(f"M {cx + 22} {cy + off} L {cx + 34} {cy + off}",
                          accent, 1.8))
        p.append(f'<circle cx="{cx + 34}" cy="{cy + off}" r="2.2" '
                 f'fill="{accent}"/>')
    p.append(A.sparkle(cx, cy, 4.5, color=accent, seed=12, dur=2.8, lo=0.4))
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
    body.append(A.watercolor_blob(cx, 71, 48, accent, seed=21, opacity=0.08))
    body.append(f'<circle cx="{cx}" cy="71" r="45" fill="none" '
                f'stroke="{accent}" stroke-width="0.7" opacity="0.25"/>')
    body.append(A.stroke(f"M {cx - 49} 75 A 49 49 0 0 1 {cx - 13} 24 "
                         f"M {cx + 49} 67 A 49 49 0 0 1 {cx + 13} 118",
                         accent, 1.1, opacity=0.4))
    for dx, dy in [(-44, -24), (44, 24)]:
        body.append(A.fill_path(f"M {cx+dx} {71+dy-3} l 3 3 -3 3 -3 -3 Z",
                                PALETTE["gold"], 0.7))
    doodle = {"dashboard": _doodle_dashboard, "usb_debugger": _doodle_usb_debugger,
              "terminal": _doodle_terminal}[spec["doodle"]]
    body.append(f'<g transform="translate({cx} 71) scale(1.25)">'
                f'{doodle(0, 0)}</g>')
    body.append(A.text(cx, 138, spec["repo"], 21, weight="bold"))
    tw = A.text_w(spec["repo"], 21)
    body.append(A.stroke(A.wobbly_line(cx - tw / 2, 148, cx + tw / 2, 148,
                                       seed=31, amp=1.0),
                         accent, 2.0, opacity=0.8))
    body.append(A.text(cx, 172, spec["desc"], 15))
    body.append(A.text(cx, 193, spec["desc2"], 12, color=PALETTE["ink_soft"]))
    body.append(A.fade_line(39, 203, W - 39, accent, w=0.65, opacity=0.25,
                            seed=30, fade_in=0.25, fade_out=0.25))
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
    body.append(A.hills(W, 174, 10, "#78915f", seed=75))
    body.append(A.fill_path("M 738 139 Q 693 148 714 158 Q 734 170 675 178 "
                           "Q 628 185 637 200 H 551 Q 568 183 650 173 "
                           "Q 711 166 698 158 Q 681 149 736 139 Z", "#d1c6a0", 0.72))
    body.append(A.stroke("M 720 153 h 12 M 707 163 h 14 M 665 178 h 22 "
                         "M 610 191 h 25", "#fff0c9", 1, opacity=0.65))
    for px, py, sc in [(53, 165, .36), (69, 164, .55), (92, 166, .41),
                        (859, 163, .4), (877, 165, .58), (901, 166, .48)]:
        body.append(A.pine(px, py, sc, "#667b60", "#52664f"))
    body.append(A.fill_path("M 0 184 Q 220 163 377 181 Q 432 173 535 185 "
                           "L 559 200 H 0 Z M 764 200 Q 886 179 1000 178 V 200 Z",
                           "#57754f"))
    body.append(A.meadow(W, 198, seed=76, color="#3d604b", count=30,
                         flower="#eee2b8", height=18))
    body.append(A.botanical(27, 204, .68, color="#3d604b", flower="#e8dbaa"))
    body.append(A.botanical(976, 207, .82, color="#3d604b", flower="#e8dbaa", flip=True))
    body.append(A.traveler(508, 188, .83, cloak="#3e575a"))
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
    body.append(A.ornament_frame(W, H, "#594838", inset=10, opacity=0.42))
    body.append('</g>')
    return A.svg_doc(W, H, "".join(body), font_b64=FONT_M, title="footer scene")


# ======================================================== 素材位回退插画 ==

def fallback_art():
    """原创魔导书插画：铜金星轨、立体书页、织带与植物标本。"""
    W, H = 480, 480
    ink, blue, gold = PALETTE["ink_soft"], PALETTE["roxy"], PALETTE["gold"]
    body = [A.paper_bg(W, H, rx=18, seed=17, sw=1.5)]
    body.append(A.watercolor_blob(240, 221, 147, blue, seed=91, opacity=0.055, layers=3))
    body.append(A.watercolor_blob(135, 375, 83, gold, seed=92, opacity=0.065))
    body.append(A.magic_circle(240, 232, 162, seed=19, opacity=0.2,
                               dur_outer=120, dur_inner=95, color=gold, sw=1.0))
    body.append('<circle cx="240" cy="232" r="143" fill="none" '
                'stroke="#9bafae" stroke-width="0.7" opacity="0.3"/>')
    # 星座微光只放在书页上方，避免背景纹样削弱主体。
    body.append(A.stroke("M 123 142 L 160 111 185 134 M 311 118 L 351 149 335 184",
                         blue, 0.8, opacity=0.36, dash="2 5"))
    for i, (x, y) in enumerate([(123, 142), (160, 111), (185, 134),
                                (311, 118), (351, 149), (335, 184)]):
        body.append(A.sparkle(x, y, 3.5 if i % 2 else 5, color=gold,
                              seed=90+i, delay=i * .5, lo=0.45))
    body.append(A.horizon_glow(240, 369, 119, 14, blue, 0.15))
    body.append(A.botanical(88, 402, 1.23, color="#8a9c80", flower="#fdf7e6"))
    body.append(A.botanical(392, 402, 1.23, color="#8a9c80", flower="#fdf7e6", flip=True))
    body.append(A.stroke("M 116 398 Q 240 427 364 398", gold, 0.8, opacity=0.45))
    body.append(A.sparkle(240, 407, 5, color=gold, seed=80, lo=0.65, dur=5))

    book = [A.horizon_glow(240, 235, 86, 74, "#b1e8df", 0.55)]
    cover = ("M 240 252 Q 186 223 119 233 L 105 302 Q 176 294 240 325 "
             "Q 304 294 375 302 L 361 233 Q 294 223 240 252 Z")
    book += [A.fill_path(cover, "#456880"), A.stroke(cover, "#345368", 1.8),
             A.stroke("M 110 304 Q 184 302 240 330 Q 296 302 370 304", gold, 2.1),
             A.fill_path("M 235 255 Q 218 296 229 348 L 239 342 248 349 "
                         "Q 236 302 247 257 Z", "#b66d63")]
    for sign in (-1, 1):
        # 镜像绘制两翼，书脊向下收束而纸张边缘微微翻卷。
        page = [A.fill_path("M 0 0 Q 51 -28 116 -17 L 128 49 "
                            "Q 57 43 0 72 Z", "#dbceb0")]
        for offset in (8, 5, 2):
            page.append(A.stroke(f"M 1 {61+offset} Q 58 {34+offset} 123 {42+offset}",
                                  "#9c947d", .8, opacity=0.55))
        top = "M 0 -3 Q 56 -33 113 -23 L 124 42 Q 57 35 0 64 Z"
        page += [A.fill_path(top, "#fff9e8"), A.stroke(top, "#a9997f", 1.1),
                 A.fill_path("M 0 -3 Q 7 19 0 64 L 12 55 Q 14 22 8 -7 Z", "#b4a98c", 0.2),
                 A.stroke("M 15 -4 Q 64 -23 106 -16", gold, 0.9, opacity=0.7),
                 A.stroke("M 17 49 Q 69 30 115 34", gold, 0.8, opacity=0.55)]
        # 一页是星图，另一页是细密手稿。
        if sign == -1:
            page.append(A.magic_circle(65, 13, 20, color=blue, seed=13,
                                       opacity=0.6, sw=0.8, dur_outer=110, dur_inner=90))
            page.append(A.stroke("M 26 40 Q 45 32 59 32 M 75 28 Q 90 25 105 28",
                                  ink, 1, opacity=0.5))
        else:
            for i in range(5):
                yy = 1 + i * 7
                end = 96 if i % 2 else 105
                page.append(A.stroke(f"M 25 {yy} Q 66 {yy-15} {end} {yy-9}",
                                      ink, .9, opacity=0.5))
            page.append(A.fill_path("M 89 -18 L 99 -19 103 -1 96 -4 91 1 Z", blue, 0.7))
        page.append(A.stroke("M 105 -20 L 110 -19 112 -10 M 115 35 L 121 36 120 29",
                              gold, 2.2, opacity=0.9))
        book.append(f'<g transform="translate(240 246) scale({sign} 1)">'
                    f'{"".join(page)}</g>')
    book.append(A.stroke("M 240 245 Q 234 274 240 312", "#a99b7d", 1.3))
    # 渐变光球和倾斜轨道，靠轮廓与高光塑造体积。
    book.append('<defs><radialGradient id="book-orb" cx="32%" cy="26%" r="75%">'
                '<stop stop-color="#f7fff3"/><stop offset="0.4" stop-color="#b7eee1"/>'
                '<stop offset="0.78" stop-color="#76bec8"/>'
                '<stop offset="1" stop-color="#6798b7"/></radialGradient></defs>')
    book.append(A.horizon_glow(240, 168, 64, 64, "#9fdeda", 0.35))
    book.append('<circle cx="240" cy="168" r="24" fill="url(#book-orb)"/>')
    book.append('<ellipse cx="240" cy="168" rx="44" ry="12" '
                'transform="rotate(-24 240 168)" fill="none" '
                'stroke="#b99b62" stroke-width="1.2" opacity="0.8"/>')
    book.append(A.stroke("M 226 163 Q 228 153 240 152", "#ffffff", 2.1, opacity=0.85))
    book.append(A.sparkle(274, 151, 5, color=gold, seed=32, dur=4, lo=0.55))
    book.append(A.stroke("M 234 203 Q 216 216 235 230 M 247 207 Q 257 220 246 235",
                         blue, 1, opacity=0.45, dash="2 5"))
    for i in range(5):
        book.append(A.dot_particle(205 + i * 17, 239 - (i % 2) * 14, 1.6,
                                   gold, seed=700+i, rise=24))
    body.append(f'<g>{"".join(book)}'
                '<animateTransform attributeName="transform" type="translate" '
                'values="0 0; 0 -7; 0 0" dur="8s" repeatCount="indefinite" '
                'calcMode="spline" keySplines="0.45 0 0.55 1; 0.45 0 0.55 1"/></g>')
    return A.svg_doc(W, H, "".join(body), title="Floating grimoire and celestial garden",
                     grain=(4, 4, W - 8, H - 8, 18))


# =============================================================== 生成入口 ==

def build_assets(font_b64):
    """统一生成静态资源，供 CLI 与回归测试共用。"""
    global FONT_M
    FONT_M = font_b64
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
    return outputs


if __name__ == "__main__":
    outputs = build_assets(Path(sys.argv[1]).read_text().strip())
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.svg"):
        if old.name not in outputs:
            old.unlink()
            print(f"{old.name:24s} removed")
    for name, svg in outputs.items():
        p = OUT / name
        p.write_text(svg, encoding="utf-8")
        print(f"{name:24s} {len(svg)/1024:8.1f} KiB")
