"""SVG 回归检查。运行：python3 -m unittest discover -s tests -v"""
import itertools
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import artlib as A
import cards
import genart
from content import HERO_TITLE, HERO_MOTTO, HERO_SUB, SKY

NS = "{http://www.w3.org/2000/svg}"
FONT = (ROOT / "tools/fonts/wenkai-medium.b64").read_text().strip()


class ArtworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # CLI 在新进程中从 1 分配 id；隔离全局计数，避免测试顺序影响结果。
        with patch.object(A, "_uid", itertools.count(1)):
            cls.assets = genart.build_assets(FONT)

    def assert_valid_svg(self, svg):
        root = ET.fromstring(svg)
        self.assertEqual(root.tag, NS + "svg")
        self.assertEqual(root.get("role"), "img")
        self.assertTrue(root.get("aria-label"))
        w, h = float(root.get("width")), float(root.get("height"))
        self.assertGreater(w, 0)
        self.assertGreater(h, 0)
        self.assertEqual(list(map(float, root.get("viewBox").split())), [0, 0, w, h])
        ids = [node.get("id") for node in root.iter() if node.get("id")]
        self.assertEqual(len(ids), len(set(ids)), "SVG 内有重复 id")
        for node in root.iter():
            self.assertNotIn(node.tag, (NS + "script", NS + "foreignObject"))
            for attr, value in node.attrib.items():
                for ref in re.findall(r"url\(#([^)]+)\)", value):
                    self.assertIn(ref, ids, f"缺失 SVG 定义：{ref}")
                if attr in ("href", "{http://www.w3.org/1999/xlink}href"):
                    self.assertTrue(value.startswith(("#", "data:")),
                                    "图片资源必须自包含")
                    if value.startswith("#"):
                        self.assertIn(value[1:], ids)
        # 包含内嵌字体也保持轻量，避免精细化无节制地扩大 README 图片。
        self.assertLess(len(svg.encode("utf-8")), 200 * 1024)
        return root

    def test_static_svg_structure_and_references(self):
        for name, svg in self.assets.items():
            with self.subTest(asset=name):
                self.assert_valid_svg(svg)

    def test_committed_assets_match_generator(self):
        paths = {p.name: p for p in (ROOT / "assets").glob("*.svg")}
        self.assertEqual(set(paths), set(self.assets))
        for name, svg in self.assets.items():
            with self.subTest(asset=name):
                self.assertTrue(paths[name].read_text(encoding="utf-8") == svg,
                                f"{name} 需要重新生成")

    def test_generation_is_reproducible(self):
        with patch.object(A, "_uid", itertools.count(1)):
            regenerated = genart.build_assets(FONT)
        self.assertEqual(self.assets, regenerated)

    def test_all_hero_phases(self):
        for phase, sky_colors in SKY.items():
            with self.subTest(phase=phase):
                svg = cards.build_hero(phase, FONT)
                root = self.assert_valid_svg(svg)
                sky = root.find(f".//{NS}linearGradient[@id='sky']")
                self.assertIsNotNone(sky)
                self.assertEqual(tuple(stop.get("stop-color") for stop in sky), sky_colors)
                texts = [node.text for node in root.iter(NS + "text")]
                for label in (HERO_TITLE, HERO_MOTTO, HERO_SUB):
                    self.assertIn(label, texts)
                self.assertEqual(root.get("viewBox"), "0 0 1000 340")
                self.assertIn("#ffd994" if phase == "night" else "#a9d6d4", svg)

    def test_scene_primitive_variants(self):
        for night in (False, True):
            for landmark in ("cottage", "arch"):
                for waterfall in (False, True):
                    with self.subTest(night=night, landmark=landmark, waterfall=waterfall):
                        body = A.floating_island(150, 130, 160, seed=11,
                                                 night=night, landmark=landmark,
                                                 waterfall=waterfall)
                        self.assert_valid_svg(A.svg_doc(300, 300, body,
                                                       title="Floating island"))

    def test_readme_local_images_exist(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        images = re.findall(r'(?:src|srcset)="(\./[^\"]+)"', readme)
        self.assertTrue(images)
        for src in images:
            with self.subTest(src=src):
                self.assertTrue((ROOT / src).is_file())


if __name__ == "__main__":
    unittest.main()
