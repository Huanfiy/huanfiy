# -*- coding: utf-8 -*-
"""手绘风 SVG 原语库（Excalidraw 质感 + 水彩晕染 + SMIL 动画）。

所有随机性都来自显式传入的 seed，保证产物可复现。
被 tools/genart.py（静态资产）与 server/cards.py（动态卡片）共用。
"""
import math
import random

from content import PALETTE


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


def stroke(d, color=None, w=2.2, opacity=1.0, dash=None, cls=""):
    color = color or PALETTE["ink"]
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    cls_attr = f' class="{cls}"' if cls else ""
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" '
            f'stroke-linecap="round" stroke-linejoin="round" '
            f'opacity="{opacity}"{dash_attr}{cls_attr}/>')


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


# ================================================================ 水彩质感 ==

def watercolor_blob(cx, cy, r, color, seed=1, opacity=0.16, layers=2,
                    blur_id="wcblur"):
    """多层不规则色斑模拟水彩晕染，配合 feGaussianBlur 滤镜使用。"""
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
    return "".join(parts)


def defs_common():
    """公共 <defs>：水彩模糊、柔光、纸纹噪声。"""
    return """
  <filter id="wcblur" x="-30%" y="-30%" width="160%" height="160%">
    <feGaussianBlur stdDeviation="3"/>
  </filter>
  <filter id="softglow" x="-60%" y="-60%" width="220%" height="220%">
    <feGaussianBlur stdDeviation="2.4" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="bigglow" x="-80%" y="-80%" width="260%" height="260%">
    <feGaussianBlur stdDeviation="6" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="grain">
    <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="2"
      seed="7" stitchTiles="stitch"/>
    <feColorMatrix type="matrix"
      values="0 0 0 0 0.26 0 0 0 0 0.22 0 0 0 0 0.16 0 0 0 0.05 0"/>
  </filter>"""


def grain_rect(w, h):
    """铺满画布的纸纹噪声层（放在最上层）。"""
    return f'<rect width="{w}" height="{h}" filter="url(#grain)"/>'


def paper_bg(w, h, rx=14, color=None, edge=True, seed=5):
    """羊皮纸底 + 手绘描边。"""
    color = color or PALETTE["paper"]
    parts = [f'<rect x="1.5" y="1.5" width="{w-3}" height="{h-3}" rx="{rx}" '
             f'fill="{color}"/>']
    if edge:
        parts.append(sketchy_frame(6, 6, w - 12, h - 12, seed=seed,
                                   color=PALETTE["ink"], sw=2.2))
    return "".join(parts)


# ================================================================ 装饰元素 ==

def sparkle(x, y, s, color=None, dur=None, seed=1, delay=0.0):
    """四芒星光点，呼吸闪烁。"""
    rnd = random.Random(seed)
    color = color or PALETTE["glow"]
    dur = dur or rnd.uniform(1.8, 3.6)
    k = s * 0.22
    d = (f"M {x} {y - s} Q {x + k} {y - k} {x + s} {y} "
         f"Q {x + k} {y + k} {x} {y + s} "
         f"Q {x - k} {y + k} {x - s} {y} "
         f"Q {x - k} {y - k} {x} {y - s} Z")
    lo = rnd.uniform(0.08, 0.25)
    return (f'<path d="{d}" fill="{color}" filter="url(#softglow)">'
            f'<animate attributeName="opacity" values="{lo};1;{lo}" '
            f'dur="{dur:.1f}s" begin="{delay:.1f}s" repeatCount="indefinite"/>'
            f'</path>')


def dot_particle(x, y, r, color, seed=1, rise=14):
    """缓缓上升消散的魔力粒子。"""
    rnd = random.Random(seed)
    dur = rnd.uniform(5.0, 9.0)
    delay = rnd.uniform(0, dur)
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}" opacity="0">'
            f'<animate attributeName="opacity" values="0;0.85;0" dur="{dur:.1f}s" '
            f'begin="{delay:.1f}s" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 0; 0 {-rise}" dur="{dur:.1f}s" begin="{delay:.1f}s" '
            f'repeatCount="indefinite"/></circle>')


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
    rnd = random.Random(seed)
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
          drift=26, dur=42):
    """水彩云团，左右漂移。"""
    rnd = random.Random(seed)
    lobes = []
    spec = [(-1.5, 0.15, 0.62), (-0.6, -0.28, 0.85), (0.4, -0.2, 0.95),
            (1.3, 0.1, 0.7), (0.1, 0.25, 0.8)]
    for i, (dx, dy, rr) in enumerate(spec):
        r = 26 * rr * scale * rnd.uniform(0.9, 1.1)
        d = wobbly_circle_d(cx + dx * 30 * scale, cy + dy * 26 * scale, r,
                            seed=seed * 7 + i, irregular=0.10, n=12)
        lobes.append(f'<path d="{d}" fill="{color}"/>')
    return (f'<g opacity="{opacity}" filter="url(#wcblur)">{"".join(lobes)}'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 0; {drift} 0; 0 0" dur="{dur}s" '
            f'repeatCount="indefinite"/></g>')


def floating_island(cx, cy, w, seed=6, bob=4, dur=7, grass=None, rock="#7a6a55",
                    grass_deep=None, waterfall=False):
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
        stroke(bot_d, PALETTE["ink"], 1.6, opacity=0.5),
        fill_path(top_d, grass),
        stroke(top_d, grass_deep, 1.8, opacity=0.8),
    ]
    # 岩层纹理
    for i in range(3):
        y = cy + depth * (0.22 + 0.2 * i)
        xw = w * (0.36 - 0.09 * i)
        parts.append(stroke(wobbly_line(cx - xw, y, cx + xw, y,
                                        seed=seed * 5 + i, amp=1.2),
                            PALETTE["ink"], 1.0, opacity=0.30))
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


def hills(w, base_y, amp, color, seed=8, opacity=1.0):
    """远景草原丘陵剪影。"""
    rnd = random.Random(seed)
    pts = [(0, base_y + rnd.uniform(-amp, amp))]
    n = 7
    for i in range(1, n + 1):
        pts.append((w * i / n, base_y + rnd.uniform(-amp, amp)))
    d = _smooth_path(pts) + f" L {w} {base_y + 400} L 0 {base_y + 400} Z"
    return fill_path(d, color, opacity)


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


# ================================================================== 文字 ==

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


# ================================================================== 骨架 ==

def svg_doc(w, h, body, font_b64=None, title="", grain=True):
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{title}">')
    font = font_style(font_b64) if font_b64 else ""
    tail = grain_rect(w, h) if grain else ""
    return (f'{head}{font}<defs>{defs_common()}</defs>'
            f'{body}{tail}</svg>')
