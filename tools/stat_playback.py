"""Compile only the live stats card. Keep live text/vector data and original periods."""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://www.w3.org/2000/svg}"
ET.register_namespace("", NS[1:-1])


def layers(svg):
    """Top-level, data-independent filter layers in their original paint order."""
    root = ET.fromstring(svg)
    return root, [
        (i, el)
        for i, el in enumerate(root)
        if el.get("filter") in ("url(#cardshadow)", "url(#wcblur)", "url(#grain)")
    ]


def load_tiles(directory):
    return json.loads((Path(directory) / "stats-tiles.json").read_text())


def optimize(svg, tiles, fps=8):
    root, fixed = layers(svg)
    for idx, node in fixed:
        tile = tiles.get(ET.tostring(node, encoding="unicode").strip())
        if tile is None:  # An edited drawing is still valid before tiles are rebaked.
            continue
        root.remove(node)
        root.insert(idx, ET.Element(NS + "image", tile))
    # All clocks share the same sample grid, including their initial delays.
    # A continuously interpolated SMIL attribute invalidates the entire SVG.
    for tag in ("animate", "animateTransform"):
        for el in root.iter(NS + tag):
            dur = float(el.get("dur")[:-1])
            steps = max(2, round(dur * fps))
            if tag == "animateTransform":
                a, x, y = el.attrib.pop("from").split()
                b = el.attrib.pop("to").split()[0]
                values = [
                    f"{float(a) + (float(b) - float(a)) * i / steps:.2f} {x} {y}"
                    for i in range(steps)
                ]
            else:
                lo, hi, end = map(float, el.get("values").split(";"))
                values = []
                for i in range(steps):
                    phase = 2 * i / steps
                    v = (
                        lo + (hi - lo) * phase
                        if phase < 1
                        else hi + (end - hi) * (phase - 1)
                    )
                    values.append(f"{v:.3f}")
            el.set("calcMode", "discrete")
            el.set("values", ";".join(values))
            el.set("dur", f"{steps / fps:g}s")
            begin = float(el.get("begin", "0s")[:-1])
            el.set("begin", f"{round(begin * fps) / fps:g}s")
    return ET.tostring(root, encoding="unicode")
