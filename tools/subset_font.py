# -*- coding: utf-8 -*-
"""按 content.charset() 子集化霞鹜文楷，输出 base64 woff2 供 SVG 内嵌。

用法: python subset_font.py <input.ttf> <output_prefix>
产物: <output_prefix>.woff2 / <output_prefix>.b64 /
      <output_prefix>.metrics.json（字符 → 字宽/em，供 artlib.text_w 精确排版）
"""
import base64
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from content import charset


def export_metrics(src, chars, out):
    from fontTools.ttLib import TTFont
    f = TTFont(src)
    upem = f["head"].unitsPerEm
    cmap = f.getBestCmap()
    hmtx = f["hmtx"]
    metrics = {}
    for ch in chars:
        g = cmap.get(ord(ch))
        if g is None:
            continue
        metrics[ch] = round(hmtx[g][0] / upem, 4)
    Path(out).write_text(json.dumps(metrics, ensure_ascii=False,
                                    separators=(",", ":")), encoding="utf-8")
    return len(metrics)


def main():
    src, prefix = sys.argv[1], sys.argv[2]
    chars = charset()
    txt = Path(f"{prefix}.chars.txt")
    txt.write_text(chars, encoding="utf-8")
    out = f"{prefix}.woff2"
    subprocess.run([
        sys.executable, "-m", "fontTools.subset", src,
        f"--text-file={txt}",
        "--flavor=woff2",
        f"--output-file={out}",
        "--layout-features=kern",
        "--no-hinting",
        "--desubroutinize",
    ], check=True)
    data = Path(out).read_bytes()
    b64 = base64.b64encode(data).decode()
    Path(f"{prefix}.b64").write_text(b64)
    n = export_metrics(src, chars, f"{prefix}.metrics.json")
    print(f"{len(chars)} chars -> {len(data)/1024:.1f} KiB woff2 "
          f"({len(b64)/1024:.1f} KiB base64), {n} glyph metrics")


if __name__ == "__main__":
    main()
