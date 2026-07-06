# -*- coding: utf-8 -*-
"""内容与配色单一数据源。

所有出现在 SVG 里的文字都必须定义在这里（或由 ASCII 动态拼出），
subset_font.py 据此收集字符集做字体子集化。
"""

# ---------------------------------------------------------------- palette --
PALETTE = {
    "ink":        "#43382b",   # 褐墨线条
    "ink_soft":   "#6b5d4a",
    "paper":      "#f9f1de",   # 水彩纸底
    "paper_deep": "#f1e4c8",
    "grass":      "#8cba72",
    "grass_deep": "#679458",
    "roxy":       "#4f79b3",   # 主题蓝
    "roxy_deep":  "#2f4f7d",
    "glow":       "#7fd6e8",   # 魔法青
    "gold":       "#e5b566",
    "red":        "#cf6a5e",
    "white":      "#fdfbf5",
}

SKY = {
    "dawn":  ("#a9bede", "#f4dfc2", "#e8c9a8"),
    "day":   ("#7fc0e4", "#c8e6f2", "#e9f5ef"),
    "dusk":  ("#d97f56", "#efb98a", "#f2d9a8"),
    "night": ("#141f3a", "#2a3c64", "#41557f"),
}

# GitHub linguist 近似色，stats 卡语言条用
LANG_COLORS = {
    "Python": "#3572A5", "C": "#8a8a8a", "C++": "#f34b7d",
    "Shell": "#89e051", "Lua": "#000080", "HTML": "#e34c26",
    "CSS": "#663399", "CMake": "#DA3434", "JavaScript": "#f1e05a",
    "Makefile": "#427819", "Dockerfile": "#384d54", "TypeScript": "#3178c6",
    "Assembly": "#6E4C13", "Vim Script": "#199f4b",
}
LANG_FALLBACK_COLOR = "#9a8f7d"

# ------------------------------------------------------------------- hero --
HERO_TITLE = "Huanfly"
HERO_MOTTO = "今天也要拿出真本事~"
HERO_SUB = "Embedded · Linux · AI tooling"
HERO_CHIPS = ["嵌入式", "Linux", "AI 工具链", "自动化"]

# ------------------------------------------------------------ stack panel --
STACK_TITLE = "技 术 栈"
STACK_TITLE_SUB = "Grimoire of Craft"
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
STATS_TITLE = "冒险者档案"
STATS_SUB = "Adventurer Profile"
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
    texts = [HERO_TITLE, HERO_MOTTO, HERO_SUB, STACK_TITLE, STACK_TITLE_SUB,
             FOOTER_QUOTE, FOOTER_SIGN, STATS_TITLE, STATS_SUB]
    texts += HERO_CHIPS
    texts += list(STATS_LABELS.values())
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
