# gh-cards 动态卡片服务

为 profile README 提供动态 SVG 的小服务，跑在 `huanfly.com`（systemd 常驻，
`127.0.0.1:8321`，nginx `location ^~ /gh/` 反代）。仅用 Python 3 stdlib。

## 端点

| 端点 | 说明 | 缓存 |
| --- | --- | --- |
| `/gh/hero.svg` | 手绘横幅，按北京时间切换黎明(5-8)/白天(8-17)/黄昏(17-20)/夜晚 | 15 min |
| `/gh/stats.svg` | GitHub 公开统计卡，后台每 30 min 刷新，失败保留旧值 | 30 min |
| `/gh/keyart` | 关于我的素材位：`official/` 目录有图返回最新一张，否则回退原创插画 | 60 min |
| `/gh/health` | 健康检查 | — |

## 部署 / 更新

仓库根目录执行（本机需有 `ubuntu@huanfly.com` 的 SSH 公钥与免密 sudo）：

```bash
bash server/deploy.sh
```

脚本会同步 `tools/{artlib,cards,content}.py`、字体子集、`server.py`、
回退插画到 `/home/ubuntu/apps/gh-cards/`，安装并重启 systemd 服务
`gh-cards`，最后做健康检查。

## 素材位换图

把图片（png/jpg/webp/gif/svg）丢进 VPS 的
`/home/ubuntu/apps/gh-cards/official/` 即可，文件名任意，取 mtime 最新的一张；
删掉所有图则回退到原创插画。GitHub camo 有缓存，换图后最长约 1 小时生效。

```bash
scp keyart.jpg ubuntu@huanfly.com:/home/ubuntu/apps/gh-cards/official/
```

## 静态资产再生成

改了 `tools/content.py`（文案/配色/项目卡）后：

```bash
python3 -m venv .venv && .venv/bin/pip install fonttools brotli   # 首次
.venv/bin/python tools/subset_font.py <LXGWWenKai-Medium.ttf> tools/fonts/wenkai-medium
cd tools && ../.venv/bin/python genart.py fonts/wenkai-medium.b64
```

字体子集来自[霞鹜文楷](https://github.com/lxgw/LxgwWenKai)（OFL，
许可见 `tools/fonts/OFL.txt`）。改了文字记得先重跑子集化再生成资产，
并执行一次 `server/deploy.sh` 让动态卡同步新字体/文案。

## 运维排查

```bash
ssh ubuntu@huanfly.com systemctl status gh-cards
ssh ubuntu@huanfly.com journalctl -u gh-cards -n 50 --no-pager
curl -s https://huanfly.com/gh/health
```
