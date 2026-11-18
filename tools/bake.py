#!/usr/bin/env python3
"""Bake the authored SVGs in Chromium. No browser, JS or encoder on the server."""

import argparse
import base64
import io
import os
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree as ET

import cards
from PIL import Image
from playwright.sync_api import Error, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUT = ASSETS / "playback"
PHASES = ("dawn", "day", "dusk", "night")


def sources():
    font = (ROOT / "tools/fonts/wenkai-medium.b64").read_text().strip()
    for phase in PHASES:
        yield "hero-" + phase, cards.build_hero(phase, font), 24, 24
    for p in sorted(ASSETS.glob("*.svg")):
        if p.stem.startswith(("tags-", "stats-", "hero-")):
            continue
        # Slow decorative details need fewer samples than the full-width scene.
        fps, seconds = (
            (18, 24)
            if p.stem in ("footer", "fallback-art")
            else (12, 16)
            if p.stem == "stack-panel"
            else (12, 8)
            if p.stem.startswith("card-")
            else (8, 7)
        )
        yield p.stem, p.read_text(), fps, seconds


# No jump at the loop boundary: close independent oscillators on whole cycles.
# Staggered particles retain their authored phase offsets. Do not reverse the
# entire clip (that would reverse the waterfall and rising particles).
CLOCK = """seconds => {
  const svg = document.querySelector('svg'); svg.pauseAnimations();
  for (const a of svg.querySelectorAll('animate, animateTransform')) {
    const period = parseFloat(a.getAttribute('dur'));
    const cycles = Math.max(1, Math.round(seconds / period));
    const newPeriod = seconds / cycles;
    a.setAttribute('dur', newPeriod + 's');
    const begin = parseFloat(a.getAttribute('begin') || '0');
    a.setAttribute('begin', (begin / period * newPeriod - seconds * 2) + 's');
  }
  svg.setCurrentTime(0); return document.fonts.ready.then(() => true);
}"""


def bake(browser, name, svg, fps, seconds):
    root = ET.fromstring(svg)
    width, height = (int(root.get(a)) for a in ("width", "height"))
    if name == "fallback-art":  # displayed at 220 CSS px: retain headroom for high-DPI
        width = height = 352
    page = browser.new_page(
        viewport={"width": width, "height": height}, device_scale_factor=1
    )
    try:
        page.set_content(
            '<!doctype html><meta charset="utf-8"><style>*{margin:0}svg{display:block;width:100vw;height:100vh}</style>'
            + svg
        )
        page.evaluate(CLOCK, seconds)
        cdp = page.context.new_cdp_session(page)
        cdp.send(
            "Emulation.setDefaultBackgroundColorOverride",
            {"color": {"r": 0, "g": 0, "b": 0, "a": 0}},
        )

        def frames():
            for n in range(fps * seconds):
                page.evaluate(
                    't => document.querySelector("svg").setCurrentTime(t)',
                    seconds + n / fps,
                )
                for attempt in range(3):
                    try:
                        data = cdp.send(
                            "Page.captureScreenshot",
                            {"format": "png", "optimizeForSpeed": True},
                        )["data"]
                        break
                    except Error as exc:
                        if (
                            "Unable to capture screenshot" not in str(exc)
                            or attempt == 2
                        ):
                            raise
                        time.sleep(0.2)  # renderer may briefly be busy; clock is paused
                yield Image.open(io.BytesIO(base64.b64decode(data))).convert("RGBA")

        seq = frames()
        durations = [
            round((i + 1) * 1000 / fps) - round(i * 1000 / fps)
            for i in range(fps * seconds)
        ]
        OUT.mkdir(exist_ok=True)
        dest = OUT / (name + ".webp")
        with TemporaryDirectory(dir=OUT) as tmp:
            baked = Path(tmp) / dest.name
            crisp = name.startswith(("h-", "card-"))
            next(seq).save(
                baked,
                save_all=True,
                append_images=seq,
                loop=0,
                duration=durations,
                quality=84,
                method=4,
                kmax=0,
                lossless=crisp,
                allow_mixed=not crisp,
            )
            with Image.open(baked) as check:
                if (
                    not check.is_animated
                    or check.n_frames < 2
                    or check.info["loop"] != 0
                ):
                    raise ValueError(f"{name}: static or non-looping output")
            baked.replace(dest)
        print(
            f"{name}: {width}x{height}, {fps} fps, {seconds}s, {dest.stat().st_size:,} bytes",
            flush=True,
        )
    finally:
        page.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("names", nargs="*", help="only build these stems (default: all)")
    ap.add_argument(
        "--chrome",
        default=os.environ.get("CHROME"),
        help="optional system Chromium executable",
    )
    args = ap.parse_args()
    jobs = {n: (s, f, t) for n, s, f, t in sources()}
    with (
        sync_playwright() as pw,
        pw.chromium.launch(executable_path=args.chrome) as browser,
    ):
        for name in args.names or jobs:
            bake(browser, name, *jobs[name])


if __name__ == "__main__":
    main()
