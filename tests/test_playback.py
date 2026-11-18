"""Release checks, stdlib only (no Chromium needed to verify checked-in media)."""

import struct
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import cards
import stat_playback as sp

OUT = ROOT / "assets/playback"


def chunks(data):
    assert data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    assert int.from_bytes(data[4:8], "little") + 8 == len(data)
    p = 12
    while p < len(data):
        kind, size = struct.unpack_from("<4sI", data, p)
        p += 8
        yield kind, data[p : p + size]
        p += size + (size & 1)


class PlaybackTests(unittest.TestCase):
    def test_animated_assets_and_delivery_budget(self):
        published = {p.stem for p in OUT.glob("*.webp")}
        expected = {
            p.stem
            for p in (ROOT / "assets").glob("*.svg")
            if not p.stem.startswith(("hero-", "stats-", "tags-"))
        }
        self.assertEqual(
            published,
            expected | {"hero-" + p for p in ("dawn", "day", "dusk", "night")},
        )
        for stem in published:
            with self.subTest(stem=stem):
                data = (OUT / (stem + ".webp")).read_bytes()
                self.assertLess(len(data), 5_000_000)
                anim = list(chunks(data))
                frames = [p for k, p in anim if k == b"ANMF"]
                self.assertEqual(next(p for k, p in anim if k == b"ANIM")[4:6], b"\0\0")
                self.assertGreater(len(set(frames)), 8)
                self.assertGreaterEqual(
                    sum(int.from_bytes(p[12:15], "little") for p in frames), 7000
                )

    def test_stats_keep_live_values_and_motion(self):
        tiles = sp.load_tiles(OUT)
        for avatar in ("", "iVBORw0KGgo="):
            data = dict(cards.SAMPLE_STATS, stars=98765, avatar_b64=avatar)
            orig = cards.build_stats(data, "")
            root, filtered = sp.layers(orig)
            self.assertGreater(len(filtered), 0)
            self.assertTrue(
                all(
                    ET.tostring(e, encoding="unicode").strip() in tiles
                    for _, e in filtered
                )
            )
            lite = sp.optimize(orig, tiles)
            compiled = ET.fromstring(lite)
            self.assertEqual(
                [n.text for n in root.iter(sp.NS + "text")],
                [n.text for n in compiled.iter(sp.NS + "text")],
            )
            self.assertIn("98765", lite)
            for tag in ("animate", "animateTransform"):
                clocks = list(compiled.iter(sp.NS + tag))
                self.assertEqual(len(clocks), len(list(root.iter(sp.NS + tag))))
                self.assertTrue(all(n.get("calcMode") == "discrete" for n in clocks))
            self.assertFalse(sp.layers(lite)[1])
