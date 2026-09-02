# -*- coding: utf-8 -*-
"""内容与配色单一数据源。

所有出现在 SVG 里的文字都必须定义在这里（或由 ASCII 动态拼出），
subset_font.py 据此收集字符集做字体子集化。
"""

# ---------------------------------------------------------------- palette --
PALETTE = {
    "ink":        "#4a4033",   # 褐墨线条
    "ink_soft":   "#7a6c58",
    "paper":      "#f9f3e6",   # 水彩纸底
    "paper_deep": "#efe4cc",
    "grass":      "#8cba72",
    "grass_deep": "#679458",
    "roxy":       "#4f79b3",   # 主题蓝
    "roxy_deep":  "#2f4f7d",
    "glow":       "#7fd6e8",   # 魔法青
    "gold":       "#e0b263",
    "red":        "#d1786c",
    "lavender":   "#a99bc9",
    "white":      "#fdfbf5",
}

# 透明底资产（章节标题 / 标签条）在浅色与深色主题下的墨色
THEME_INK = {
    "light": {"ink": PALETTE["ink"], "soft": PALETTE["ink_soft"],
              "line": "#a9997f", "chip": "#ffffff"},
    "dark":  {"ink": "#ebe3d2", "soft": "#b3a892",
              "line": "#6d6552", "chip": "#1b2230"},
}

SKY = {
    "dawn":  ("#b4c4df", "#f0dcc8", "#f8e8d2"),
    "day":   ("#86c2e5", "#cbe5f3", "#eef7f1"),
    "dusk":  ("#a591b5", "#e8b898", "#f5dab2"),
    "night": ("#121a33", "#26375c", "#465c86"),
}

# GitHub linguist 近似色，stats 卡语言条用
LANG_COLORS = {
    "Python": "#3572A5", "C": "#8a8a8a", "C++": "#f34b7d",
    "Shell": "#89e051", "Lua": "#000080", "HTML": "#e34c26",
    "CSS": "#663399", "CMake": "#DA3434", "JavaScript": "#f1e05a",
    "Makefile": "#427819", "Dockerfile": "#384d54", "TypeScript": "#3178c6",
    "Assembly": "#6E4C13", "Vim Script": "#199f4b", "Rust": "#dea584",
}
LANG_FALLBACK_COLOR = "#9a8f7d"

# ------------------------------------------------------------------- hero --
HERO_TITLE = "Huanfly"
HERO_MOTTO = "今天也要拿出真本事~"
HERO_SUB = "Embedded · Linux · AI tooling"

# --------------------------------------------------------------- 章节标题 --
# (slug, 中文标题, 英文小字, 图标)
SECTIONS = [
    ("about", "关于我", "About", "quill"),
    ("stack", "技术栈", "Tech Stack", "grimoire"),
    ("works", "精选作品", "Selected Works", "chest"),
    ("stats", "冒险者档案", "Adventurer Profile", "orb"),
]

# --------------------------------------------------------- 关于我 · 标签条 --
FOCUS_TAGS = ["嵌入式", "Linux", "输入法", "AI 工具链"]

# ------------------------------------------------------------ stack panel --
STACK_GROUPS = [
    ("嵌入式", "roxy", ["C", "C++", "STM32", "ESP32", "RTOS", "USB"]),
    ("系统与工具", "grass_deep", ["Linux", "zsh", "Git", "CMake", "Docker", "Neovim"]),
    ("语言与折腾", "gold", ["Python", "Lua", "Shell", "Rime", "FunASR", "AI CLI"]),
]

# ---------------------------------------------------------------- 项目卡片 --
PROJECT_CARDS = [
    {
        "slug": "vocotype",
        "repo": "VocoType-linux",
        "desc": "Linux 离线中文语音输入法",
        "desc2": "FunASR · 约 0.1s 上屏 · IBus / Fcitx5",
        "lang": "Python",
        "doodle": "mic",
    },
    {
        "slug": "rime-lite",
        "repo": "rime-lite",
        "desc": "小而美的 Rime 输入法配置",
        "desc2": "开箱即用 · 简洁词库 · 长期维护",
        "lang": "Shell",
        "doodle": "keyboard",
    },
    {
        "slug": "oh-my-terminal",
        "repo": "oh-my-terminal",
        "desc": "优雅的终端套件配置",
        "desc2": "zsh · tmux · p10k · 一键部署",
        "lang": "Shell",
        "doodle": "terminal",
    },
]

# ------------------------------------------------------------------ 页脚 --
FOOTER_QUOTE = "把手上的事做好，把本事留在作品里。"
FOOTER_SIGN = "— Huanfly"

# -------------------------------------------------------------- stats 卡 --
STATS_LABELS = {
    "repos": "公开仓库",
    "stars": "获星",
    "followers": "关注者",
    "years": "冒险年数",
    "mana": "魔力构成",
    "mana_sub": "Languages",
    "updated": "档案更新于",
}

# --------------------------------------------------------------- charset --
def charset():
    """收集所有 SVG 文字用到的字符 + 全量可打印 ASCII（动态数字/语言名）。"""
    chars = set(chr(c) for c in range(0x20, 0x7F))
    texts = [HERO_TITLE, HERO_MOTTO, HERO_SUB, FOOTER_QUOTE, FOOTER_SIGN]
    texts += FOCUS_TAGS
    texts += list(STATS_LABELS.values())
    for _slug, zh, en, _icon in SECTIONS:
        texts += [zh, en]
    for name, _c, items in STACK_GROUPS:
        texts.append(name)
        texts += items
    for p in PROJECT_CARDS:
        texts += [p["repo"], p["desc"], p["desc2"], p["lang"]]
    texts.append("「」·—。，、：；！？（）年月日时·Lv巡礼中")
    for t in texts:
        chars.update(t)
    chars.discard("\n")
    return "".join(sorted(chars))


if __name__ == "__main__":
    cs = charset()
    print(f"{len(cs)} chars")
    print(cs)
