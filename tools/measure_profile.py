#!/usr/bin/env python3
"""Measure an actual public profile in an isolated stock Firefox (no existing tabs/extensions)."""

import argparse
import base64
import io
import itertools
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

import psutil
import websocket


def measure(args):
    with tempfile.TemporaryDirectory(prefix="profile-cpu-") as tmp:
        d = Path(tmp)
        (d / "user.js").write_text(
            f'user_pref("layout.css.prefers-color-scheme.content-override", {0 if args.dark else 1});\n'
        )
        with (d / "firefox.log").open("w") as log:
            browser = subprocess.Popen(
                [
                    "firefox",
                    "--no-remote",
                    "--headless",
                    "--profile",
                    tmp,
                    "--remote-debugging-port",
                    "0",
                    "about:blank",
                ],
                stdout=log,
                stderr=log,
            )
        try:
            for _ in range(100):
                m = re.search(
                    r"listening on (ws://127\.0\.0\.1:\d+)",
                    (d / "firefox.log").read_text(),
                )
                if m:
                    break
                time.sleep(0.1)
            if not m:
                raise RuntimeError("Firefox BiDi did not start")
            ws = websocket.create_connection(
                m[1] + "/session", suppress_origin=True, timeout=60
            )
            ids = itertools.count(1)

            def call(method, **params):
                i = next(ids)
                ws.send(json.dumps({"id": i, "method": method, "params": params}))
                while True:
                    msg = json.loads(ws.recv())
                    if msg.get("id") != i:
                        continue
                    if msg["type"] != "success":
                        raise RuntimeError(msg)
                    return msg["result"]

            session = call("session.new", capabilities={})
            ctx = call("browsingContext.getTree")["contexts"][0]["context"]
            call(
                "browsingContext.setViewport",
                context=ctx,
                viewport={"width": 1400, "height": 900},
            )

            def js(expr):
                res = call(
                    "script.evaluate",
                    expression=expr,
                    target={"context": ctx},
                    awaitPromise=True,
                )
                if res["type"] != "success":
                    raise RuntimeError(res)
                return res["result"].get("value")

            call("browsingContext.navigate", context=ctx, url=args.url, wait="complete")
            # Scroll through once to prime lazy images, then measure without any DOM changes.
            js('document.querySelector("article").scrollIntoView({block:"end"}); true')
            time.sleep(2)
            js("window.scrollTo(0,0); true")
            for _ in range(60):
                ok = js(
                    'document.querySelectorAll("article img").length===13 && [...document.querySelectorAll("article img")].every(e=>e.complete&&e.naturalWidth>0)'
                )
                if ok:
                    break
                time.sleep(1)
            if not ok:
                raise RuntimeError("not all 13 README images loaded")
            detail = json.loads(
                js(
                    'JSON.stringify([...document.querySelectorAll("article img")].map(e=>({source:e.dataset.canonicalSrc||e.currentSrc,width:e.naturalWidth})))'
                )
            )
            if args.expect and args.expect not in detail[0]["source"]:
                raise RuntimeError(detail[0])
            dark = js('matchMedia("(prefers-color-scheme:dark)").matches')
            assert dark == args.dark
            print(
                json.dumps(
                    {
                        "version": session["capabilities"]["browserVersion"],
                        "dark": dark,
                        "images": detail,
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
            proc = psutil.Process(browser.pid)

            def snapshot():
                times = {}
                for p in [proc] + proc.children(recursive=True):
                    try:
                        t = p.cpu_times()
                        times[p.pid] = t.user + t.system
                    except psutil.Error:
                        pass
                return times

            for label, idx in [("top", None), ("projects", 5), ("stats-footer", 10)]:
                js(
                    "window.scrollTo(0,0);true"
                    if idx is None
                    else f'document.querySelectorAll("article img")[{idx}].scrollIntoView();true'
                )
                time.sleep(4)
                vals = []
                for _ in range(3):
                    t = time.monotonic()
                    old = snapshot()
                    time.sleep(3)
                    new = snapshot()
                    vals.append(
                        round(
                            100
                            * sum(new[k] - old[k] for k in new.keys() & old.keys())
                            / (time.monotonic() - t),
                            1,
                        )
                    )
                print(label, "CPU%", vals, flush=True)
                if args.shots:
                    args.shots.mkdir(parents=True, exist_ok=True)
                    for frame in (1, 2):
                        data = call("browsingContext.captureScreenshot", context=ctx)[
                            "data"
                        ]
                        (args.shots / f"{label}-{frame}.png").write_bytes(
                            base64.b64decode(data)
                        )
                        time.sleep(0.65)
            if args.check_media:
                from PIL import Image

                served = json.loads(
                    js(
                        'JSON.stringify([...document.querySelectorAll("article img")].map(e=>e.currentSrc))'
                    )
                )
                for url in served:
                    with urlopen(url, timeout=30) as response:
                        if response.headers.get_content_type() != "image/webp":
                            continue
                        payload = response.read()
                    if int.from_bytes(payload[4:8], "little") + 8 != len(payload):
                        raise ValueError(f"truncated WebP from {url}")
                    with Image.open(io.BytesIO(payload)) as image:
                        image.seek(image.n_frames - 1)
                        image.load()
                        print(
                            "verified through final frame:",
                            image.n_frames,
                            url[:72],
                            flush=True,
                        )
            call("session.end")
            ws.close()
        finally:
            browser.terminate()
            browser.wait(timeout=15)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default="https://github.com/Huanfiy")
    ap.add_argument("--expect")
    ap.add_argument("--dark", action="store_true")
    ap.add_argument(
        "--check-media",
        action="store_true",
        help="decode the actual CDN/Camo WebPs through their final frame",
    )
    ap.add_argument("--shots", type=Path)
    measure(ap.parse_args())
