# -*- coding: utf-8 -*-
"""手绘风 SVG 原语库（Excalidraw 质感 + 水彩晕染 + SMIL 动画）。

所有随机性都来自显式传入的 seed，保证产物可复现。
被 tools/genart.py（静态资产）与 tools/cards.py（动态卡片）共用。
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
    """暖白纸面、细金边与圆角内框；轻微抖动保留手绘感。"""
    color = color or PALETTE["paper"]
    fx = ' filter="url(#cardshadow)"' if shadow else ""
    parts = [f'<rect x="{inset}" y="{inset}" width="{w - 2 * inset}" '
             f'height="{h - 2 * inset}" rx="{rx}" fill="{color}"{fx}/>']
    if vignette_op > 0:
        parts.append(f'<g transform="translate({inset} {inset})">'
                     + vignette(w - 2 * inset, h - 2 * inset,
                                opacity=vignette_op * 0.55, rx=rx) + '</g>')
    if edge:
        m = inset + 2
        parts.append(stroke(wobbly_rounded_rect_d(
            m, m, w - 2 * m, h - 2 * m, rx - 2, seed=seed, amp=0.35),
            PALETTE["ink_soft"], sw * 0.55, opacity=edge_opacity * 0.48))
        parts.append(ornament_frame(w, h, PALETTE["gold"], inset=inset + 9,
                                    opacity=0.42, corners=10))
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
    """有清晰轮廓、背光边缘和柔和底影的层叠云，不再整团模糊。"""
    rnd = random.Random(seed)
    sy = rnd.uniform(0.85, 1.12)
    d = ("M -82 14 Q -95 9 -82 3 Q -76 -3 -65 0 "
         "C -69 -19 -48 -28 -35 -17 C -29 -47 9 -49 20 -22 "
         "C 38 -34 57 -21 54 -6 C 71 -13 82 -2 78 7 "
         "Q 97 9 89 16 C 46 22 -36 21 -82 14 Z")
    parts = [fill_path(d, color)]
    if shade:
        parts.append(fill_path(
            "M -80 13 Q -39 18 -25 4 Q -4 20 20 7 Q 44 21 78 10 "
            "Q 95 16 70 18 Q -20 26 -80 13 Z", shade, 0.24))
    parts.append(stroke("M -62 -2 Q -52 -15 -38 -10 M -25 -25 "
                        "Q -5 -39 10 -24 M 28 -15 Q 42 -20 48 -8",
                        "#ffffff", 1.5, opacity=0.48))
    parts.append(stroke("M -102 24 Q -60 28 -31 24 M 37 29 Q 74 31 111 26",
                        color, 2.2, opacity=0.45))
    return (f'<g opacity="{opacity}"><g transform="translate({cx} {cy}) '
            f'scale({scale} {scale * sy:.3f})">{"".join(parts)}</g>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 0; {drift} 0; 0 0" dur="{dur}s" '
            f'repeatCount="indefinite" calcMode="spline" '
            f'keySplines="0.45 0 0.55 1; 0.45 0 0.55 1"/></g>')


def floating_island(cx, cy, w, seed=6, bob=4, dur=7, grass=None, rock="#8b8976",
                    grass_deep=None, waterfall=False, ink_opacity=0.5,
                    landmark="cottage", night=False):
    """微缩浮岛：切面岩层、苔藓、垂藤、小屋 / 遗迹和渐隐水流。"""
    rnd = random.Random(seed)
    grass = grass or PALETTE["grass"]
    grass_deep = grass_deep or PALETTE["grass_deep"]
    ink = "#39493e" if not night else "#15283b"
    stone = ("#c2bbaa", "#aaa793", "#666f62") if not night else (
        "#748595", "#5d7181", "#344858")
    outline = "M -80 0 L -64 24 -49 29 -38 53 -18 59 -3 83 12 64 30 53 44 27 65 20 80 0 Z"
    parts = [fill_path(outline, rock),
             fill_path("M -80 0 L -31 7 -38 53 -49 29 -64 24 Z", stone[0]),
             fill_path("M -31 7 L 4 14 -3 83 -18 59 -38 53 Z", stone[1]),
             fill_path("M 4 14 L 47 3 30 53 12 64 -3 83 Z", stone[2]),
             stroke(outline, ink, 1.0, opacity=ink_opacity)]
    parts.append(stroke("M -62 15 L -39 21 -33 33 M -24 18 L -13 34 -19 46 "
                        "M 20 22 L 12 38 16 48 M 45 15 L 36 22 "
                        "M -35 42 L -23 45 M -9 56 L -3 66",
                        ink, 1.1, opacity=0.3))
    parts.append(fill_path("M -81 0 Q -69 -9 -47 -8 Q -30 -20 -9 -14 "
                           "Q 16 -21 33 -13 Q 66 -13 81 0 L 69 6 48 4 "
                           "31 11 9 7 -8 12 -27 6 -44 9 -62 4 Z", grass))
    parts.append(fill_path("M -80 0 Q -27 -5 1 3 Q 45 -1 80 0 L 69 6 48 4 "
                           "31 11 9 7 -8 12 -27 6 -44 9 -62 4 Z", grass_deep, 0.7))
    parts.append(stroke("M -68 -3 Q -38 -12 -19 -9 M 29 -8 Q 47 -10 64 -4",
                        "#e4e7bc" if not night else "#99b7b1", 1.6, opacity=0.65))
    # 远侧小树与建筑；都与岛体一起轻浮。
    parts.append(pine(-53, -7, 0.55, grass_deep, ink))
    parts.append(pine(49, -8, 0.8, grass_deep, ink))
    if landmark == "cottage":
        wall, roof = ("#f1e7cb", "#a26d56") if not night else ("#9cacae", "#555d76")
        parts += [fill_path("M -27 -12 L -27 -40 -3 -54 22 -39 22 -12 Z", wall),
                  fill_path("M -3 -54 L 22 -39 22 -12 -3 -17 Z", ink, 0.13),
                  fill_path("M -34 -39 L -7 -60 1 -60 30 -38 23 -35 -3 -53 -27 -35 Z", roof),
                  stroke("M -34 -39 L -7 -60 1 -60 30 -38 M -27 -35 L -27 -12 "
                         "22 -12 22 -35", ink, 1.1, opacity=0.65),
                  fill_path("M 9 -52 L 9 -65 15 -65 15 -47 Z", wall),
                  stroke("M 8 -65 L 16 -65", ink, 1.5),
                  fill_path("M -9 -13 V -28 Q -3 -35 3 -28 V -13 Z", "#4c665d"),
                  f'<rect x="10" y="-32" width="7" height="9" rx="1" '
                  f'fill="{"#ffd994" if night else "#a9d6d4"}"/>',
                  stroke("M 13.5 -32 V -23 M 10 -27.5 H 17", wall, 0.9),
                  stroke("M -22 -40 L -5 -53 M 2 -50 L 20 -38", wall, 0.7, opacity=0.5),
                  stroke("M -3 -10 Q -12 -3 -20 1", "#e9dfba", 3.5, opacity=0.7)]
        parts.append(stroke("M 12 -71 Q 4 -77 14 -83 Q 22 -88 15 -95",
                            "#fff5dc", 2.8, opacity=0.4))
    elif landmark == "arch":
        arch = "M -22 -10 V -44 Q -21 -66 0 -67 Q 21 -66 22 -44 V -10 H 12 V -44 Q 11 -56 0 -57 Q -11 -56 -12 -44 V -10 Z"
        parts += [fill_path(arch, stone[0]), stroke(arch, ink, 1.0, opacity=0.55),
                  stroke("M -22 -22 H -12 M -22 -36 H -12 M 12 -29 H 22 "
                         "M 12 -43 H 22 M -16 -58 L -9 -51 M 0 -67 V -57 "
                         "M 15 -59 L 9 -52", ink, 0.8, opacity=0.35),
                  stroke("M -18 -56 Q -27 -42 -18 -30 Q -13 -25 -17 -16",
                         grass_deep, 2.4, opacity=0.85)]
    for i in range(7):
        vx = -66 + i * 20 + rnd.uniform(-4, 4)
        length = rnd.uniform(12, 33)
        parts.append(stroke(f"M {vx:.1f} 5 q -5 10 -1 {length:.1f}",
                            grass_deep, 1.5, opacity=0.95))
        for j in range(3):
            vy = 9 + j * (length - 6) / 3
            parts.append(fill_path(
                f"M {vx-2:.1f} {vy:.1f} q -8 -3 -5 4 q 5 3 5 -4 Z", grass_deep))
    for x, y, size in [(-55, 45, 5), (42, 57, 4), (19, 85, 3)]:
        parts.append(fill_path(f"M {x} {y} l {size} -2 2 {size} -3 {size+3} Z", rock))
    if waterfall:
        gid = uid("fall")
        parts.append(f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
                     '<stop stop-color="#e5ffff" stop-opacity="0.85"/>'
                     '<stop offset="0.65" stop-color="#a3dde1" stop-opacity="0.55"/>'
                     '<stop offset="1" stop-color="#e5ffff" stop-opacity="0"/>'
                     '</linearGradient>')
        parts.append(fill_path("M -25 3 Q -20 14 -23 44 Q -25 83 -19 117 "
                               "L -12 117 Q -19 73 -15 42 Q -11 12 -17 3 Z",
                               f"url(#{gid})"))
        parts.append('<path d="M -20 8 Q -16 46 -20 70 M -18 84 L -17 101" '
                     'fill="none" stroke="#f1ffff" stroke-width="1.2" '
                     'opacity="0.75" stroke-dasharray="13 8">'
                     '<animate attributeName="stroke-dashoffset" values="0;-42" '
                     'dur="3s" repeatCount="indefinite"/></path>')
        parts.append(horizon_glow(-16, 111, 23, 7, "#d9efeb", 0.4))
    return (f'<g><g transform="translate({cx} {cy}) scale({w / 160:.4f})">'
            f'{"".join(parts)}</g>'
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


# ========================================================== 精细场景与花饰 ==

def ornament_frame(w, h, color, inset=12, opacity=0.55, corners=16):
    """地图式细内框；角线与菱形保持克制，不压住内容。"""
    x, y, r = inset, inset, corners
    parts = [f'<rect x="{x}" y="{y}" width="{w-2*x}" height="{h-2*y}" '
             f'rx="{r}" fill="none" stroke="{color}" stroke-width="0.7" '
             f'opacity="{opacity * 0.5}"/>']
    for px, py, sx, sy in ((x, y, 1, 1), (w-x, y, -1, 1),
                            (x, h-y, 1, -1), (w-x, h-y, -1, -1)):
        parts.append(f'<g transform="translate({px} {py}) scale({sx} {sy})" '
                     f'opacity="{opacity}">'
                     + stroke(f"M 0 {r+10} V {r} Q 0 0 {r} 0 H {r+10}", color, 1.1)
                     + fill_path("M 6 2 L 9 6 6 10 3 6 Z", color)
                     + '</g>')
    return "".join(parts)


def pine(x, y, scale=1.0, color="#668567", trunk="#586550"):
    """分层针叶树，原点在树根，标准高度约 62。"""
    return (f'<g transform="translate({x} {y}) scale({scale})">'
            + stroke("M 0 0 Q 1 -30 0 -59", trunk, 2.1)
            + fill_path("M 0 -64 Q -3 -48 -10 -41 L -5 -42 Q -10 -29 -17 -24 "
                        "L -10 -25 Q -15 -13 -22 -8 Q -9 -5 0 -9 Q 13 -4 21 -8 "
                        "Q 11 -16 10 -25 L 16 -23 Q 7 -36 5 -43 L 10 -40 "
                        "Q 3 -53 0 -64 Z", color)
            + stroke("M 0 -51 V -8 M 0 -34 L -7 -29 M 0 -24 L 10 -18 "
                     "M 0 -17 L -12 -12", trunk, 0.9, opacity=0.35)
            + stroke("M -2 -47 L -5 -41 M -7 -31 L -12 -25 M -12 -16 L -17 -11",
                     "#eef0cf", 1.0, opacity=0.24) + '</g>')


def botanical(x, y, scale=1.0, color="#628066", flower="#f8efd5", flip=False):
    """羽状枝叶与野花，适合前景角落和纸面装饰。"""
    sx = -scale if flip else scale
    parts = [stroke("M 0 0 Q -3 -28 -23 -62 M -1 -12 Q 12 -33 21 -39",
                    color, 1.4)]
    for lx, ly, turn in [(-4, -19, -25), (-7, -29, -40), (-11, -39, -50),
                          (-17, -50, -55), (8, -27, 40), (15, -34, 45)]:
        parts.append(f'<g transform="translate({lx} {ly}) rotate({turn})">'
                     + fill_path("M 0 0 Q -18 -4 -15 -13 Q -4 -12 0 0 Z", color, 0.85)
                     + fill_path("M 0 0 Q 15 -3 13 -12 Q 3 -11 0 0 Z", color, 0.68)
                     + stroke("M -12 -10 L 0 0 10 -9", flower, 0.45, opacity=0.35)
                     + '</g>')
    parts.append(stroke("M 5 0 Q 21 -9 30 -27 M 13 -10 Q 32 -5 40 -13",
                        color, 1.1))
    for fx, fy, s in [(30, -29, 1), (41, -15, 0.75)]:
        for i in range(5):
            a = math.tau * i / 5
            px, py = fx + math.cos(a) * 2.5 * s, fy + math.sin(a) * 2.5 * s
            parts.append(f'<ellipse cx="{px:.2f}" cy="{py:.2f}" rx="{2.6*s}" '
                         f'ry="{1.6*s}" transform="rotate({i*72} {px:.2f} {py:.2f})" '
                         f'fill="{flower}"/>')
        parts.append(f'<circle cx="{fx}" cy="{fy}" r="{1.4*s}" fill="{PALETTE["gold"]}"/>')
    return f'<g transform="translate({x} {y}) scale({sx} {scale})">{"".join(parts)}</g>'


def meadow(w, y, seed=9, color="#55745a", flower="#f5eace", count=22, height=25):
    """疏密有致的草穗、叶片与细小花头。"""
    rnd = random.Random(seed)
    parts = []
    for i in range(count):
        x = rnd.uniform(20, w - 20)
        by = y + rnd.uniform(-5, 6)
        h = rnd.uniform(height * 0.3, height)
        dx = rnd.uniform(-6, 6)
        parts.append(stroke(f"M {x:.1f} {by:.1f} q {dx:.1f} {-h*0.6:.1f} "
                            f"{dx:.1f} {-h:.1f}", color, 1.0, opacity=0.85))
        parts.append(fill_path(f"M {x:.1f} {by-3:.1f} q -9 -2 -8 -8 q 7 1 8 8 Z",
                               color, 0.7))
        if i % 3 == 0:
            for ox, oy in [(-1.8, 0), (1.8, 0), (0, -2)]:
                parts.append(f'<circle cx="{x+dx+ox:.1f}" cy="{by-h+oy:.1f}" '
                             f'r="1.8" fill="{flower}" opacity="0.88"/>')
            parts.append(f'<circle cx="{x+dx:.1f}" cy="{by-h:.1f}" r="0.9" '
                         f'fill="{PALETTE["gold"]}"/>')
    return "".join(parts)


def traveler(x, y, scale=1.0, cloak="#40596a", light="#c2eee5"):
    """侧背面的原创旅人：宽檐帽、披风褶皱、挎包和木杖。"""
    ink = "#344239"
    parts = [fill_path("M -6 -10 L -8 -1 -3 0 0 -10 M 5 -10 L 8 0 13 0 10 -12 Z", ink),
             fill_path("M -5 -43 Q -15 -33 -17 -13 Q -4 -6 14 -13 "
                       "L 10 -36 4 -44 Z", cloak),
             fill_path("M 3 -40 Q 3 -23 14 -13 L 5 -11 Q -1 -22 -3 -38 Z", ink, 0.3),
             stroke("M -8 -31 L -11 -16 M -3 -26 L -5 -13", "#dbe6cc", 0.7, opacity=0.35),
             fill_path("M -5 -45 Q -10 -57 0 -60 Q 11 -59 7 -47 L 3 -42 Z", "#d8c7a2"),
             fill_path("M -17 -53 Q -8 -56 -6 -62 L 0 -76 Q 8 -71 10 -58 "
                       "Q 18 -56 18 -53 Q 0 -49 -17 -53 Z", cloak),
             stroke("M -8 -57 Q 1 -53 10 -56", "#bba071", 1.8),
             fill_path("M -8 -44 Q 1 -39 9 -44 L 10 -39 Q 20 -34 23 -27 "
                       "Q 13 -31 6 -37 L -8 -39 Z", "#bc8064"),
             stroke("M -10 -40 L 8 -19", "#bcab84", 1.8),
             fill_path("M -13 -23 Q -19 -20 -16 -11 L -7 -11 -5 -21 Z", "#917859"),
             stroke("M 20 0 L 23 -57 Q 30 -64 24 -69 Q 18 -72 18 -65", "#715e48", 2.2),
             stroke("M 8 -32 Q 15 -27 21 -31", cloak, 5),
             f'<circle cx="21" cy="-31" r="2.2" fill="#d8c7a2"/>',
             f'<circle cx="23" cy="-64" r="3.2" fill="{light}" filter="url(#bigglow)"/>',
             sparkle(23, -64, 3.2, color=light, seed=41, dur=4.8, lo=0.5)]
    return f'<g transform="translate({x} {y}) scale({scale})">{"".join(parts)}</g>'


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
