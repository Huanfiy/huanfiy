# gh-cards 动态卡片服务

为 profile README 提供动态 SVG 的小服务，跑在 `huanfly.com`（systemd 常驻，
`127.0.0.1:8321`，nginx `location ^~ /gh/` 反代）。仅用 Python 3 stdlib。

## 端点

| 端点 | 说明 | 缓存 |
| --- | --- | --- |
| `/gh/hero.svg` | 手绘横幅，按北京时间切换黎明(5-8)/白天(8-17)/黄昏(17-20)/夜晚 | 15 min |
| `/gh/stats.svg` | GitHub 公开统计卡，后台每 30 min 刷新，失败保留旧值 | 30 min |
| `/gh/keyart` | 关于我的素材位：`official/` 目录有图返回最新一张，否则回退原创插画（480×480） | 60 min |
| `/gh/health` | 健康检查 | — |

## 部署 / 更新

仓库根目录执行（本机需有 `ubuntu@huanfly.com` 的 SSH 公钥与免密 sudo）：

```bash
bash server/deploy.sh
```

脚本会同步 `tools/{artlib,cards,content}.py`、字体子集（`.b64` 与
`.metrics.json` 字宽表）、`server.py`、回退插画到
`/home/ubuntu/apps/gh-cards/`，安装并重启 systemd 服务 `gh-cards`，
最后做健康检查。

## 素材位换图

把图片（png/jpg/webp/gif/svg）丢进 VPS 的
`/home/ubuntu/apps/gh-cards/official/` 即可，文件名任意，取 mtime 最新的一张；
删掉所有图则回退到原创插画。GitHub camo 有缓存，换图后最长约 1 小时生效。
README 里该图以 220px 宽浮动在「关于我」右侧，建议用接近正方形的图，
过高会在文字下方留白。

```bash
scp keyart.jpg ubuntu@huanfly.com:/home/ubuntu/apps/gh-cards/official/
```

## 静态资产再生成

只调整插画、配色或布局时，在仓库根目录执行（Python 3 标准库即可，无需重新处理字体）：

```bash
python3 tools/genart.py tools/fonts/wenkai-medium.b64
python3 -m unittest discover -s tests -v
```

插画原语位于 `tools/artlib.py`，昼夜横幅和统计卡位于 `tools/cards.py`，
其余静态卡片位于 `tools/genart.py`。横幅包含浮岛小屋、遗迹、山谷溪流与
前景植物；页脚和魔导书插画沿用相同的细线、纸纹与淡金装饰。
测试覆盖静态 SVG、四种昼夜横幅、内部引用及生成结果的一致性。

README 的横幅、统计卡和素材位仍指向线上端点，仅再生成本地 `assets/`
不会更新它们；确认效果后需执行 `bash server/deploy.sh` 同步动态服务。
`official/` 中已有图片时，素材位会继续优先展示该图片，而非魔导书回退图。

如果改了 `tools/content.py` 中的文案或新增字符，先更新字体子集：

```bash
python3 -m venv .venv && .venv/bin/pip install fonttools brotli   # 首次
.venv/bin/python tools/subset_font.py <LXGWWenKai-Medium.ttf> tools/fonts/wenkai-medium
cd tools && ../.venv/bin/python genart.py fonts/wenkai-medium.b64
```

字体子集来自[霞鹜文楷](https://github.com/lxgw/LxgwWenKai)（OFL，
许可见 `tools/fonts/OFL.txt`；源字体 `LXGWWenKai-Medium.ttf` 从其
Releases 下载，不入库）。`subset_font.py` 同时导出
`wenkai-medium.metrics.json`（字符 → 字宽/em），`artlib.text_w()` 用它做
自适应宽度的标签与下划线排版。改了文字记得先重跑子集化再生成资产，
并执行一次 `server/deploy.sh` 让动态卡同步新字体/文案。

静态资产一览（`genart.py` 会删除不再生成的旧文件）：

| 文件 | 用途 |
| --- | --- |
| `h-{about,stack,works,stats}-{light,dark}.svg` | 透明底章节标题，README 用 `<picture>` 按主题切换 |
| `tags-{light,dark}.svg` | 关于我下方的领域标签条 |
| `stack-panel.svg` | 技术栈面板 |
| `card-*.svg` | 精选作品竖版卡（320×236，三张并排各 32%） |
| `footer.svg` | 页脚暮色场景 |
| `fallback-art.svg` | 素材位回退插画（同步到服务端） |
| `hero-fallback.svg` / `stats-sample.svg` | 动态卡的静态样张，便于本地预览 |

## 运维排查

```bash
ssh ubuntu@huanfly.com systemctl status gh-cards
ssh ubuntu@huanfly.com journalctl -u gh-cards -n 50 --no-pager
curl -s https://huanfly.com/gh/health
```
