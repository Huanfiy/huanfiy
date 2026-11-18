"""Bake the invariant filter results of the live stats SVG; never bake account data."""

import base64
import io
import json
import os
import xml.etree.ElementTree as ET

from bake import ASSETS, OUT
from PIL import Image
from playwright.sync_api import sync_playwright
from stat_playback import NS, layers


def main():
    root, fixed = layers((ASSETS / "stats-sample.svg").read_text())
    defs = root.find(NS + "defs")
    width, height = map(int, (root.get("width"), root.get("height")))
    tiles = {}
    with (
        sync_playwright() as pw,
        pw.chromium.launch(executable_path=os.environ.get("CHROME")) as browser,
    ):
        page = browser.new_page(viewport={"width": width, "height": height})
        for _, node in fixed:
            svg = ET.Element(NS + "svg", root.attrib)
            svg.extend([defs, node])
            page.set_content(
                "<style>*{margin:0}svg{display:block}</style>"
                + ET.tostring(svg, encoding="unicode")
            )
            im = Image.open(io.BytesIO(page.screenshot(omit_background=True))).convert(
                "RGBA"
            )
            x, y, r, b = im.getchannel("A").getbbox()
            buf = io.BytesIO()
            im.crop((x, y, r, b)).save(buf, format="WEBP", lossless=True, method=6)
            uri = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
            tiles[ET.tostring(node, encoding="unicode").strip()] = {
                "x": str(x),
                "y": str(y),
                "width": str(r - x),
                "height": str(b - y),
                "href": uri,
            }
    OUT.mkdir(exist_ok=True)
    (OUT / "stats-tiles.json").write_text(
        json.dumps(tiles, ensure_ascii=False, separators=(",", ":")) + "\n"
    )


if __name__ == "__main__":
    main()
