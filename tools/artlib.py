# -*- coding: utf-8 -*-
"""手绘风 SVG 原语库（Excalidraw 质感 + 水彩晕染 + SMIL 动画）。

所有随机性都来自显式传入的 seed，保证产物可复现。
被 tools/genart.py（静态资产）与 server/cards.py（动态卡片）共用。
"""
import itertools
import json
import math
import random
from pathlib import Path

from content import PALETTE

_uid = itertools.count(1)


def uid(prefix="g"):
    """文档内唯一 id（渐变 / 裁剪用）。"""
    return f"{prefix}{next(_uid)}"


# ================================================================ 基础路径 ==

def _jitter_points(pts, seed, amp):
    rnd = random.Random(seed)
    out = []
    for i, (x, y) in enumerate(pts):
        if i == 0 or i == len(pts) - 1:
            k = 0.4  # 端点少抖一点
        else:
            k = 1.0
        out.append((x + rnd.uniform(-amp, amp) * k,
                    y + rnd.uniform(-amp, amp) * k))
    return out


def _smooth_path(pts, closed=False):
    """经过中点的二次贝塞尔，产生柔和的手绘曲线。"""
    if closed:
        pts = list(pts) + [pts[0], pts[1]]
    d = [f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"]
    for i in range(1, len(pts) - 1):
        mx = (pts[i][0] + pts[i + 1][0]) / 2
        my = (pts[i][1] + pts[i + 1][1]) / 2
        d.append(f"Q {pts[i][0]:.1f} {pts[i][1]:.1f} {mx:.1f} {my:.1f}")
    if closed:
        d.append("Z")
    else:
        d.append(f"L {pts[-1][0]:.1f} {pts[-1][1]:.1f}")
    return " ".join(d)


def _subdivide(x1, y1, x2, y2, seg):
    return [(x1 + (x2 - x1) * i / seg, y1 + (y2 - y1) * i / seg)
            for i in range(seg + 1)]


def wobbly_line(x1, y1, x2, y2, seed=1, amp=1.6, seg=None):
    """手绘直线 path d。"""
    length = math.hypot(x2 - x1, y2 - y1)
    seg = seg or max(3, int(length / 45))
    pts = _jitter_points(_subdivide(x1, y1, x2, y2, seg), seed, amp)
    return _smooth_path(pts)


def wobbly_circle_d(cx, cy, r, seed=1, irregular=0.03, n=None):
    """手绘圆 path d；irregular 为半径抖动比例。"""
    rnd = random.Random(seed)
    n = n or max(10, int(r / 4))
    pts = []
    phase = rnd.uniform(0, math.tau)
    for i in range(n):
        a = phase + math.tau * i / n
        rr = r * (1 + rnd.uniform(-irregular, irregular))
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return _smooth_path(pts, closed=True)


def wobbly_rect_d(x, y, w, h, seed=1, amp=1.6):
    """手绘矩形（四边独立抖动，转角轻微错位）。"""
    rnd = random.Random(seed)
    o = lambda: rnd.uniform(-amp, amp)
    corners = [(x + o(), y + o()), (x + w + o(), y + o()),
               (x + w + o(), y + h + o()), (x + o(), y + h + o())]
    d = []
    for i in range(4):
        x1, y1 = corners[i]
        x2, y2 = corners[(i + 1) % 4]
        d.append(wobbly_line(x1, y1, x2, y2, seed=seed * 31 + i, amp=amp * 0.7))
    return " ".join(d)


def wobbly_rounded_rect_d(x, y, w, h, r, seed=1, amp=0.9):
    """手绘圆角矩形（闭合单路径，可填充可描边）。"""
    rnd = random.Random(seed)
    pts = []

    def edge(x1, y1, x2, y2):
        n = max(2, int(math.hypot(x2 - x1, y2 - y1) / 30))
        for i in range(n):
            t = i / n
            pts.append((x1 + (x2 - x1) * t + rnd.uniform(-amp, amp),
                        y1 + (y2 - y1) * t + rnd.uniform(-amp, amp)))

    def arc(cx, cy, a0):
        for i in range(1, 3):
            a = a0 + math.pi / 2 * i / 3
            pts.append((cx + r * math.cos(a) + rnd.uniform(-amp, amp) * 0.4,
                        cy + r * math.sin(a) + rnd.uniform(-amp, amp) * 0.4))

    edge(x + r, y, x + w - r, y)
    arc(x + w - r, y + r, -math.pi / 2)
    edge(x + w, y + r, x + w, y + h - r)
    arc(x + w - r, y + h - r, 0)
    edge(x + w - r, y + h, x + r, y + h)
    arc(x + r, y + h - r, math.pi / 2)
    edge(x, y + h - r, x, y + r)
    arc(x + r, y + r, math.pi)
    return _smooth_path(pts, closed=True)


def rounded_rect_d(x, y, w, h, r):
    """规整圆角矩形 path d（填充用）。"""
    return (f"M {x + r:.1f} {y:.1f} h {w - 2 * r:.1f} a {r} {r} 0 0 1 {r} {r} "
            f"v {h - 2 * r:.1f} a {r} {r} 0 0 1 {-r} {r} h {-(w - 2 * r):.1f} "
            f"a {r} {r} 0 0 1 {-r} {-r} v {-(h - 2 * r):.1f} "
            f"a {r} {r} 0 0 1 {r} {-r} Z")


def stroke(d, color=None, w=2.2, opacity=1.0, dash=None, cls="", extra=""):
    color = color or PALETTE["ink"]
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    cls_attr = f' class="{cls}"' if cls else ""
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" '
            f'stroke-linecap="round" stroke-linejoin="round" '
            f'opacity="{opacity}"{dash_attr}{cls_attr} {extra}/>')


def fill_path(d, color, opacity=1.0, extra=""):
    return f'<path d="{d}" fill="{color}" opacity="{opacity}" {extra}/>'


def sketchy_frame(x, y, w, h, seed=1, color=None, sw=2.4, double=True):
    """双线手绘边框：一条实、一条淡，Excalidraw 质感。"""
    color = color or PALETTE["ink"]
    parts = [stroke(wobbly_rect_d(x, y, w, h, seed=seed), color, sw)]
    if double:
        parts.append(stroke(wobbly_rect_d(x, y, w, h, seed=seed + 97, amp=2.4),
                            color, sw * 0.55, opacity=0.35))
    return "".join(parts)


def fade_line(x1, y, x2, color, w=1.4, opacity=0.8, seed=1, amp=1.2,
              fade_in=0.0, fade_out=0.35):
    """两端渐隐的手绘横线（渐变描边）。fade_* 为渐隐区占比。"""
    gid = uid("fl")
    stops = [f'<stop offset="0" stop-color="{color}" stop-opacity="0"/>'
             if fade_in > 0 else
             f'<stop offset="0" stop-color="{color}" stop-opacity="1"/>']
    if fade_in > 0:
        stops.append(f'<stop offset="{fade_in}" stop-color="{color}" '
                     f'stop-opacity="1"/>')
    if fade_out > 0:
        stops.append(f'<stop offset="{1 - fade_out}" stop-color="{color}" '
                     f'stop-opacity="1"/>')
        stops.append(f'<stop offset="1" stop-color="{color}" '
                     f'stop-opacity="0"/>')
    else:
        stops.append(f'<stop offset="1" stop-color="{color}" '
                     f'stop-opacity="1"/>')
    grad = (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" '
            f'x1="{x1}" y1="0" x2="{x2}" y2="0">{"".join(stops)}'
            f'</linearGradient>')
    return grad + stroke(wobbly_line(x1, y, x2, y, seed=seed, amp=amp),
                         f"url(#{gid})", w, opacity=opacity)


# ================================================================ 水彩质感 ==

def watercolor_blob(cx, cy, r, color, seed=1, opacity=0.16, layers=2,
                    blur_id="wcblur", edge=True):
    """多层不规则色斑模拟水彩晕染：中心淡、边缘微微积色。"""
    rnd = random.Random(seed)
    parts = []
    for i in range(layers):
        rr = r * (1 - 0.18 * i)
        ox = rnd.uniform(-r * 0.12, r * 0.12)
        oy = rnd.uniform(-r * 0.12, r * 0.12)
        d = wobbly_circle_d(cx + ox, cy + oy, rr, seed=seed + i * 13,
                            irregular=0.16, n=14)
        parts.append(f'<path d="{d}" fill="{color}" opacity="{opacity}" '
                     f'filter="url(#{blur_id})"/>')
        if edge and i == 0:
            # 水彩边缘积色线
            parts.append(f'<path d="{d}" fill="none" stroke="{color}" '
                         f'stroke-width="{max(1.0, r * 0.03):.1f}" '
                         f'opacity="{opacity * 0.9:.3f}" '
                         f'filter="url(#{blur_id})"/>')
    return "".join(parts)


def defs_common():
    """公共 <defs>：水彩模糊、柔光、纸纹噪声、投影。"""
    return """
  <filter id="wcblur" x="-30%" y="-30%" width="160%" height="160%">
    <feGaussianBlur stdDeviation="3"/>
  </filter>
  <filter id="wcblur2" x="-40%" y="-40%" width="180%" height="180%">
    <feGaussianBlur stdDeviation="7"/>
  </filter>
  <filter id="softglow" x="-60%" y="-60%" width="220%" height="220%">
    <feGaussianBlur stdDeviation="2.4" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="bigglow" x="-80%" y="-80%" width="260%" height="260%">
    <feGaussianBlur stdDeviation="6" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="cardshadow" x="-10%" y="-10%" width="120%" height="130%">
    <feDropShadow dx="0" dy="2.5" stdDeviation="3.5" flood-color="#3a2d18"
      flood-opacity="0.16"/>
  </filter>
  <filter id="grain">
    <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="2"
      seed="7" stitchTiles="stitch"/>
    <feColorMatrix type="matrix"
      values="0 0 0 0 0.26 0 0 0 0 0.22 0 0 0 0 0.16 0 0 0 0.05 0"/>
  </filter>"""


def grain_rect(w, h, x=0, y=0, rx=0):
    """纸纹噪声层（放在最上层）；可只覆盖纸面区域。"""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'filter="url(#grain)"/>')


def vignette(w, h, color="#5a4a30", opacity=0.10, rx=14):
    """纸面边缘微暗，增加厚度感。"""
    gid = uid("vg")
    return (f'<radialGradient id="{gid}" cx="50%" cy="45%" r="70%">'
            f'<stop offset="0.55" stop-color="{color}" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="{opacity}"/>'
            f'</radialGradient>'
            f'<rect x="0" y="0" width="{w}" height="{h}" rx="{rx}" '
            f'fill="url(#{gid})"/>')


def paper_bg(w, h, rx=14, color=None, edge=True, seed=5, shadow=True,
             inset=4, sw=1.9, edge_opacity=0.85, vignette_op=0.09):
    """羊皮纸底 + 微暗边缘 + 手绘描边（+ 柔和投影）。"""
    color = color or PALETTE["paper"]
    fx = f' filter="url(#cardshadow)"' if shadow else ""
    parts = [f'<rect x="{inset}" y="{inset}" width="{w - 2 * inset}" '
             f'height="{h - 2 * inset}" rx="{rx}" fill="{color}"{fx}/>']
    if vignette_op > 0:
        parts.append(f'<g transform="translate({inset} {inset})">'
                     + vignette(w - 2 * inset, h - 2 * inset,
                                opacity=vignette_op, rx=rx) + '</g>')
    if edge:
        m = inset + 5
        parts.append(stroke(wobbly_rect_d(m, m, w - 2 * m, h - 2 * m,
                                          seed=seed, amp=1.3),
                            PALETTE["ink"], sw, opacity=edge_opacity))
        parts.append(stroke(wobbly_rect_d(m, m, w - 2 * m, h - 2 * m,
                                          seed=seed + 97, amp=2.0),
                            PALETTE["ink"], sw * 0.5, opacity=0.22))
    return "".join(parts)


# ================================================================ 装饰元素 ==

def sparkle(x, y, s, color=None, dur=None, seed=1, delay=0.0, lo=None):
    """四芒星光点，呼吸闪烁。"""
    rnd = random.Random(seed)
    color = color or PALETTE["glow"]
    dur = dur or rnd.uniform(1.8, 3.6)
    k = s * 0.22
    d = (f"M {x:.1f} {y - s:.1f} Q {x + k:.1f} {y - k:.1f} {x + s:.1f} {y:.1f} "
         f"Q {x + k:.1f} {y + k:.1f} {x:.1f} {y + s:.1f} "
         f"Q {x - k:.1f} {y + k:.1f} {x - s:.1f} {y:.1f} "
         f"Q {x - k:.1f} {y - k:.1f} {x:.1f} {y - s:.1f} Z")
    lo = lo if lo is not None else rnd.uniform(0.08, 0.25)
    return (f'<path d="{d}" fill="{color}" filter="url(#softglow)">'
            f'<animate attributeName="opacity" values="{lo};1;{lo}" '
            f'dur="{dur:.1f}s" begin="{delay:.1f}s" repeatCount="indefinite"/>'
            f'</path>')


def star_field(w, h, count, seed=1, color="#f6f1d8", y_max=None,
               op_lo=0.25, op_hi=0.8):
    """静态细碎星点（不闪），用于夜空打底。"""
    rnd = random.Random(seed)
    y_max = y_max or h * 0.6
    parts = []
    for _ in range(count):
        x = rnd.uniform(6, w - 6)
        y = rnd.uniform(6, y_max)
        r = rnd.uniform(0.5, 1.3)
        op = rnd.uniform(op_lo, op_hi)
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" '
                     f'fill="{color}" opacity="{op:.2f}"/>')
    return "".join(parts)


def dot_particle(x, y, r, color, seed=1, rise=14, drift=0.0):
    """缓缓上升消散的魔力粒子。"""
    rnd = random.Random(seed)
    dur = rnd.uniform(5.0, 9.0)
    delay = rnd.uniform(0, dur)
    dx = drift if drift else rnd.uniform(-4, 4)
    return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{color}" '
            f'opacity="0">'
            f'<animate attributeName="opacity" values="0;0.85;0" dur="{dur:.1f}s" '
            f'begin="{delay:.1f}s" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 0; {dx:.1f} {-rise:.1f}" dur="{dur:.1f}s" '
            f'begin="{delay:.1f}s" repeatCount="indefinite"/></circle>')


def _rune(cx, cy, s, seed):
    """随机小符文：2~4 笔短划组成的抽象字形。"""
    rnd = random.Random(seed)
    n = rnd.randint(2, 4)
    parts = []
    for _ in range(n):
        x1 = cx + rnd.uniform(-s, s); y1 = cy + rnd.uniform(-s, s)
        x2 = cx + rnd.uniform(-s, s); y2 = cy + rnd.uniform(-s, s)
        parts.append(f"M {x1:.1f} {y1:.1f} L {x2:.1f} {y2:.1f}")
    return " ".join(parts)


def magic_circle(cx, cy, r, color=None, seed=3, dur_outer=80, dur_inner=60,
                 opacity=1.0, sw=1.6):
    """三重旋转魔法阵：外环符文顺时针，内环刻度逆时针，中心六芒星。"""
    color = color or PALETTE["glow"]
    g = [f'<g opacity="{opacity}" filter="url(#softglow)">']

    # ---- 外环组（顺时针） ----
    outer = [stroke(wobbly_circle_d(cx, cy, r, seed=seed, irregular=0.012),
                    color, sw),
             stroke(wobbly_circle_d(cx, cy, r * 0.86, seed=seed + 1,
                                    irregular=0.012), color, sw * 0.7)]
    rune_r = r * 0.93
    for i in range(12):
        a = math.tau * i / 12
        rx = cx + rune_r * math.cos(a)
        ry = cy + rune_r * math.sin(a)
        outer.append(stroke(_rune(rx, ry, r * 0.045, seed * 100 + i),
                            color, sw * 0.65, opacity=0.9))
    g.append(f'<g>{"".join(outer)}'
             f'<animateTransform attributeName="transform" type="rotate" '
             f'from="0 {cx} {cy}" to="360 {cx} {cy}" dur="{dur_outer}s" '
             f'repeatCount="indefinite"/></g>')

    # ---- 内环组（逆时针）：刻度圈 + 虚线圈 ----
    inner = [stroke(wobbly_circle_d(cx, cy, r * 0.66, seed=seed + 2,
                                    irregular=0.015), color, sw * 0.8,
                    dash=f"{r*0.05:.1f} {r*0.035:.1f}")]
    for i in range(24):
        a = math.tau * i / 24
        r1, r2 = r * 0.60, r * 0.66
        inner.append(stroke(
            f"M {cx + r1*math.cos(a):.1f} {cy + r1*math.sin(a):.1f} "
            f"L {cx + r2*math.cos(a):.1f} {cy + r2*math.sin(a):.1f}",
            color, sw * 0.55, opacity=0.85))
    g.append(f'<g>{"".join(inner)}'
             f'<animateTransform attributeName="transform" type="rotate" '
             f'from="360 {cx} {cy}" to="0 {cx} {cy}" dur="{dur_inner}s" '
             f'repeatCount="indefinite"/></g>')

    # ---- 中心六芒星（两个错位三角）+ 核心圆 ----
    tris = []
    for j, ph in enumerate((0, math.pi)):
        pts = []
        for i in range(3):
            a = ph + math.tau * i / 3 - math.pi / 2
            pts.append((cx + r * 0.52 * math.cos(a),
                        cy + r * 0.52 * math.sin(a)))
        pts = _jitter_points(pts + [pts[0]], seed + 7 + j, r * 0.012)
        d = "M " + " L ".join(f"{p[0]:.1f} {p[1]:.1f}" for p in pts) + " Z"
        tris.append(stroke(d, color, sw * 0.75, opacity=0.9))
    tris.append(stroke(wobbly_circle_d(cx, cy, r * 0.16, seed=seed + 9,
                                       irregular=0.03), color, sw * 0.8))
    g.append("".join(tris))
    g.append('</g>')
    return "".join(g)


def cloud(cx, cy, scale=1.0, color="#ffffff", opacity=0.75, seed=4,
          drift=26, dur=42, shade=None, blur="wcblur"):
    """水彩云团，左右漂移；shade 给底部一层暗色增加体积感。"""
    rnd = random.Random(seed)
    spec = [(-1.5, 0.15, 0.62), (-0.6, -0.28, 0.85), (0.4, -0.2, 0.95),
            (1.3, 0.1, 0.7), (0.1, 0.25, 0.8)]
    lobes = []
    for i, (dx, dy, rr) in enumerate(spec):
        r = 26 * rr * scale * rnd.uniform(0.9, 1.1)
        lobes.append((cx + dx * 30 * scale, cy + dy * 26 * scale, r, i))
    parts = []
    if shade:
        for (x, y, r, i) in lobes:
            d = wobbly_circle_d(x, y + 5 * scale, r * 1.02,
                                seed=seed * 7 + i, irregular=0.10, n=12)
            parts.append(f'<path d="{d}" fill="{shade}" opacity="0.45"/>')
    for (x, y, r, i) in lobes:
        d = wobbly_circle_d(x, y, r, seed=seed * 7 + i, irregular=0.10, n=12)
        parts.append(f'<path d="{d}" fill="{color}"/>')
    return (f'<g opacity="{opacity}" filter="url(#{blur})">{"".join(parts)}'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 0; {drift} 0; 0 0" dur="{dur}s" '
            f'repeatCount="indefinite" calcMode="spline" '
            f'keySplines="0.45 0 0.55 1; 0.45 0 0.55 1"/></g>')


def floating_island(cx, cy, w, seed=6, bob=4, dur=7, grass=None, rock="#7a6a55",
                    grass_deep=None, waterfall=False, ink_opacity=0.5):
    """浮空岛：草皮圆顶 + 岩石倒锥 + 藤蔓 + 可选瀑布，上下轻浮。"""
    rnd = random.Random(seed)
    grass = grass or PALETTE["grass"]
    grass_deep = grass_deep or PALETTE["grass_deep"]
    h = w * 0.55
    # 草皮顶
    top_pts = [(cx - w / 2, cy)]
    for i in range(1, 6):
        t = i / 6
        top_pts.append((cx - w / 2 + w * t,
                        cy - h * 0.30 * math.sin(math.pi * t)
                        + rnd.uniform(-2, 2)))
    top_pts.append((cx + w / 2, cy))
    top_d = _smooth_path(top_pts) + f" L {cx + w/2:.1f} {cy:.1f} Z"
    # 岩石倒锥
    bot_pts = [(cx + w / 2, cy)]
    depth = h * rnd.uniform(0.9, 1.15)
    for i in range(1, 6):
        t = i / 6
        bx = cx + w / 2 - w * t
        by = cy + depth * math.sin(math.pi * min(t * 0.72 + 0.14, 0.86)) \
            * (1 - 0.25 * abs(0.5 - t)) + rnd.uniform(-3, 3)
        bot_pts.append((bx, by))
    bot_pts.append((cx - w / 2, cy))
    bot_d = _smooth_path(bot_pts) + " Z"
    parts = [
        fill_path(bot_d, rock),
        stroke(bot_d, PALETTE["ink"], 1.5, opacity=ink_opacity),
        fill_path(top_d, grass),
        stroke(top_d, grass_deep, 1.7, opacity=0.8),
    ]
    # 岩层纹理
    for i in range(3):
        y = cy + depth * (0.22 + 0.2 * i)
        xw = w * (0.36 - 0.09 * i)
        parts.append(stroke(wobbly_line(cx - xw, y, cx + xw, y,
                                        seed=seed * 5 + i, amp=1.2),
                            PALETTE["ink"], 1.0, opacity=0.28))
    # 草皮边缘的高光与垂落藤蔓
    parts.append(stroke(wobbly_line(cx - w * 0.42, cy + 2, cx + w * 0.42,
                                    cy + 2, seed=seed + 41, amp=1.5),
                        grass_deep, 1.6, opacity=0.55))
    for i in range(3):
        vx = cx - w * 0.3 + rnd.uniform(0, w * 0.6)
        vlen = rnd.uniform(7, 14)
        parts.append(stroke(f"M {vx:.1f} {cy + 3:.1f} q {rnd.uniform(-3, 3):.1f} "
                            f"{vlen * 0.6:.1f} {rnd.uniform(-2, 2):.1f} {vlen:.1f}",
                            grass_deep, 1.2, opacity=0.6))
    if waterfall:
        wx = cx - w * 0.16
        wy = cy + depth * 0.30
        flen = w * 0.60
        parts.append(
            f'<path d="M {wx:.1f} {wy:.1f} q 2 {flen * 0.5:.1f} -1.5 {flen:.1f}" '
            f'fill="none" stroke="{PALETTE["glow"]}" stroke-width="4.5" '
            f'stroke-linecap="round" opacity="0.55" '
            f'stroke-dasharray="10 7">'
            f'<animate attributeName="stroke-dashoffset" values="0;-34" '
            f'dur="1.6s" repeatCount="indefinite"/></path>'
            f'<path d="M {wx + 3:.1f} {wy + 4:.1f} q 2 {flen * 0.5:.1f} -1 '
            f'{flen * 0.9:.1f}" fill="none" stroke="#ffffff" '
            f'stroke-width="2" stroke-linecap="round" opacity="0.5" '
            f'stroke-dasharray="6 9">'
            f'<animate attributeName="stroke-dashoffset" values="0;-30" '
            f'dur="1.3s" repeatCount="indefinite"/></path>'
            f'<circle cx="{wx - 1:.1f}" cy="{wy + flen + 4:.1f}" r="3.5" '
            f'fill="{PALETTE["glow"]}" opacity="0.35" filter="url(#wcblur)"/>')
    return (f'<g>{"".join(parts)}'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 0; 0 {-bob}; 0 0" dur="{dur}s" '
            f'repeatCount="indefinite" calcMode="spline" '
            f'keySplines="0.45 0 0.55 1; 0.45 0 0.55 1"/></g>')


def hills(w, base_y, amp, color, seed=8, opacity=1.0, n=7, depth=400):
    """远景草原丘陵剪影。"""
    rnd = random.Random(seed)
    pts = [(0, base_y + rnd.uniform(-amp, amp))]
    for i in range(1, n + 1):
        pts.append((w * i / n, base_y + rnd.uniform(-amp, amp)))
    d = _smooth_path(pts) + f" L {w} {base_y + depth} L 0 {base_y + depth} Z"
    return fill_path(d, color, opacity)


def ridge(w, base_y, amp, color, seed=8, opacity=1.0, n=13, depth=400):
    """远山棱线：起伏更密、峰更尖，用于大气透视的最远层。"""
    rnd = random.Random(seed)
    pts = [(0, base_y + rnd.uniform(-amp * 0.3, amp * 0.3))]
    for i in range(1, n + 1):
        peak = amp if i % 2 else amp * 0.35
        pts.append((w * i / n + rnd.uniform(-w / n * 0.25, w / n * 0.25),
                    base_y - rnd.uniform(0, peak)))
    pts.append((w, base_y + rnd.uniform(-amp * 0.3, amp * 0.3)))
    d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts) \
        + f" L {w} {base_y + depth} L 0 {base_y + depth} Z"
    return fill_path(d, color, opacity)


def mist_band(x, y, w, h, color="#ffffff", opacity=0.5, blur="wcblur2"):
    """横向薄雾：上下渐隐的柔色带，用来分隔景深层。"""
    gid = uid("mist")
    return (f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{color}" stop-opacity="0"/>'
            f'<stop offset="0.5" stop-color="{color}" stop-opacity="{opacity}"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="0"/>'
            f'</linearGradient>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
            f'fill="url(#{gid})" filter="url(#{blur})"/>')


def horizon_glow(cx, cy, rx, ry, color, opacity=0.5):
    """地平线柔光（径向渐变椭圆）。"""
    gid = uid("hg")
    return (f'<radialGradient id="{gid}" cx="50%" cy="50%" r="50%">'
            f'<stop offset="0" stop-color="{color}" stop-opacity="{opacity}"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="0"/>'
            f'</radialGradient>'
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" '
            f'fill="url(#{gid})"/>')


def grass_tufts(w, y_base, count, seed=9, color=None, y_jitter=6):
    """近景草叶簇。"""
    rnd = random.Random(seed)
    color = color or PALETTE["grass_deep"]
    parts = []
    for _ in range(count):
        x = rnd.uniform(10, w - 10)
        y = y_base + rnd.uniform(-y_jitter, y_jitter)
        for b in range(rnd.randint(2, 3)):
            dx = rnd.uniform(-4, 4)
            hgt = rnd.uniform(6, 13)
            bend = rnd.uniform(-3, 3)
            parts.append(
                f'<path d="M {x+b*2.4:.1f} {y:.1f} Q {x+b*2.4+bend:.1f} '
                f'{y-hgt*0.6:.1f} {x+b*2.4+dx:.1f} {y-hgt:.1f}" fill="none" '
                f'stroke="{color}" stroke-width="1.3" stroke-linecap="round" '
                f'opacity="0.7"/>')
    return "".join(parts)


def birds(specs, color, sw=1.5, opacity=0.8):
    """远处飞鸟：一组小 V 形。specs = [(x, y, scale), ...]"""
    parts = []
    for i, (bx, by, s) in enumerate(specs):
        parts.append(stroke(
            f"M {bx - 7 * s:.1f} {by:.1f} Q {bx - 3 * s:.1f} {by - 5 * s:.1f} "
            f"{bx:.1f} {by - 1.5 * s:.1f} Q {bx + 3 * s:.1f} {by - 5 * s:.1f} "
            f"{bx + 7 * s:.1f} {by:.1f}",
            color, sw * s, opacity=max(0.2, opacity - i * 0.12)))
    return "".join(parts)


# ================================================================== 文字 ==

_METRICS = None


def _metrics():
    """字符 → 字宽/em；来自 subset_font.py 导出的 metrics.json。"""
    global _METRICS
    if _METRICS is None:
        _METRICS = {}
        here = Path(__file__).resolve().parent
        for p in (here / "fonts" / "wenkai-medium.metrics.json",
                  here / "wenkai-medium.metrics.json"):
            if p.exists():
                _METRICS = json.loads(p.read_text(encoding="utf-8"))
                break
    return _METRICS


def text_w(s, size, spacing=0.0):
    """估算文本渲染宽度（有字宽表时精确，否则按 CJK 1em / 拉丁 0.56em）。"""
    m = _metrics()
    w = 0.0
    for ch in s:
        adv = m.get(ch)
        if adv is None:
            adv = 1.0 if ord(ch) > 0x2E7F else (0.3 if ch == " " else 0.56)
        w += adv * size
    return w + spacing * len(s)


def font_style(font_b64):
    """内嵌子集化字体的 <style> 块。"""
    return (f'<style>@font-face{{font-family:"LXGWWK";'
            f'src:url(data:font/woff2;base64,{font_b64}) format("woff2");}}'
            f'text{{font-family:"LXGWWK","Kaiti SC","STKaiti","KaiTi",serif;}}'
            f'</style>')


def text(x, y, s, size, color=None, anchor="middle", weight=None,
         spacing=None, opacity=1.0, extra=""):
    color = color or PALETTE["ink"]
    w = f' font-weight="{weight}"' if weight else ""
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    s = (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
            f'text-anchor="{anchor}" opacity="{opacity}"{w}{ls} {extra}>'
            f'{s}</text>')


def chip(x, y, label, size, ink, accent, seed=1, pad=13, h=None,
         fill="#ffffff", fill_opacity=0.55, tint_opacity=0.12, sw=1.3,
         edge_opacity=0.6):
    """自适应宽度的手绘标签。返回 (svg, width)。"""
    h = h or size * 2.2
    w = text_w(label, size) + pad * 2
    d = wobbly_rounded_rect_d(x, y, w, h, 8, seed=seed, amp=0.8)
    parts = [fill_path(d, fill, fill_opacity),
             fill_path(d, accent, tint_opacity),
             stroke(d, ink, sw, opacity=edge_opacity),
             text(x + w / 2, y + h / 2 + size * 0.36, label, size, color=ink)]
    return "".join(parts), w


# ================================================================== 骨架 ==

def svg_doc(w, h, body, font_b64=None, title="", grain=True, defs_extra=""):
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{title}">')
    font = font_style(font_b64) if font_b64 else ""
    if grain is True:
        tail = grain_rect(w, h)
    elif grain:  # (x, y, w, h, rx)
        gx, gy, gw, gh, grx = grain
        tail = grain_rect(gw, gh, gx, gy, grx)
    else:
        tail = ""
    return (f'{head}{font}<defs>{defs_common()}{defs_extra}</defs>'
            f'{body}{tail}</svg>')
