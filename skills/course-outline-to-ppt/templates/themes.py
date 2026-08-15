# -*- coding: utf-8 -*-
"""
course-outline-to-ppt 视觉主题库（生成器可直接 import）。

用法（在 generate.py 里）：
    import sys, os
    sys.path.insert(0, os.path.expanduser(
        "~/.qoderwork/skills/course-outline-to-ppt/templates"))
    from themes import get_theme, build_pptx_palette

    THEME = get_theme("deep-space")          # 或用户选定的其它主题 id
    PALETTE = build_pptx_palette(THEME)      # dict[str, RGBColor]
    FONT_HEAD, FONT_BODY = THEME["fonts"]["head"], THEME["fonts"]["body"]
    FONT_HEAD_EA, FONT_BODY_EA = THEME["fonts"]["headEa"], THEME["fonts"]["bodyEa"]

本模块不依赖 python-pptx（配色以十六进制字符串存储），
build_pptx_palette 负责把 hex 转成 RGBColor，供生成器使用。
主题定义与 templates/themes.json 保持一致（此处为单一事实来源的 Python 镜像）。
"""

THEMES = {
    "deep-space": {
        "name": "深空觉醒", "temperature": "冷",
        "fonts": {"head": "PingFang SC", "body": "PingFang SC",
                  "headEa": "PingFang SC", "bodyEa": "PingFang SC"},
        "palette": {"dominant": "#161B3A", "deep": "#0E122B", "support1": "#C7D0E8",
                    "support2": "#F4F6FB", "panel": "#222952", "row_alt": "#EAEEF8",
                    "accent": "#F6A821", "accent2": "#37C9C4", "ink": "#23273A",
                    "muted": "#6B7085", "white": "#FFFFFF"},
    },
    "scholar-green": {
        "name": "墨绿学术", "temperature": "中性偏冷",
        "fonts": {"head": "Songti SC", "body": "PingFang SC",
                  "headEa": "Songti SC", "bodyEa": "PingFang SC"},
        "palette": {"dominant": "#14342B", "deep": "#0C241D", "support1": "#C9D6CB",
                    "support2": "#F5F1E8", "panel": "#1E4A3C", "row_alt": "#EAEFE6",
                    "accent": "#C8A45C", "accent2": "#6B8F71", "ink": "#23302A",
                    "muted": "#6E7A72", "white": "#FFFFFF"},
    },
    "warm-terracotta": {
        "name": "暖橙人文", "temperature": "暖",
        "fonts": {"head": "PingFang SC", "body": "PingFang SC",
                  "headEa": "PingFang SC", "bodyEa": "PingFang SC"},
        "palette": {"dominant": "#3A2E2A", "deep": "#2A201D", "support1": "#E3D2C6",
                    "support2": "#FBF6F1", "panel": "#4A3A33", "row_alt": "#F3E9E1",
                    "accent": "#C0562B", "accent2": "#D9A441", "ink": "#332925",
                    "muted": "#8A7A70", "white": "#FFFFFF"},
    },
    "executive-slate": {
        "name": "商务灰金", "temperature": "中性",
        "fonts": {"head": "PingFang SC", "body": "PingFang SC",
                  "headEa": "PingFang SC", "bodyEa": "PingFang SC"},
        "palette": {"dominant": "#1F2733", "deep": "#161C26", "support1": "#CDD4DE",
                    "support2": "#F3F4F6", "panel": "#2C3644", "row_alt": "#E9ECF0",
                    "accent": "#BFA06A", "accent2": "#5B7C99", "ink": "#232A33",
                    "muted": "#6C7580", "white": "#FFFFFF"},
    },
    "porcelain-teal": {
        "name": "青瓷科技", "temperature": "冷",
        "fonts": {"head": "PingFang SC", "body": "PingFang SC",
                  "headEa": "PingFang SC", "bodyEa": "PingFang SC"},
        "palette": {"dominant": "#0F3B3A", "deep": "#0A2A29", "support1": "#C4DAD7",
                    "support2": "#F2F7F6", "panel": "#175250", "row_alt": "#E5F0EE",
                    "accent": "#FF7A5C", "accent2": "#2FB7A6", "ink": "#1F2D2C",
                    "muted": "#6E817F", "white": "#FFFFFF"},
    },
    "aubergine-premium": {
        "name": "绛紫高定", "temperature": "中性偏暖",
        "fonts": {"head": "PingFang SC", "body": "PingFang SC",
                  "headEa": "PingFang SC", "bodyEa": "PingFang SC"},
        "palette": {"dominant": "#2A1A33", "deep": "#1E1226", "support1": "#D6C9DD",
                    "support2": "#F7F3F6", "panel": "#3A2747", "row_alt": "#EFE7F0",
                    "accent": "#C98A6B", "accent2": "#8A6BA3", "ink": "#2C2233",
                    "muted": "#7A6E82", "white": "#FFFFFF"},
    },
}

DEFAULT_THEME = "deep-space"


def list_themes():
    """返回 [(id, 中文名, 温度)]，供选择时展示。"""
    return [(tid, t["name"], t["temperature"]) for tid, t in THEMES.items()]


def get_theme(theme_id=None):
    """按 id 取主题；未知 id 回退到默认主题。"""
    return THEMES.get(theme_id or DEFAULT_THEME, THEMES[DEFAULT_THEME])


def build_pptx_palette(theme):
    """把主题的 hex 配色转成 python-pptx 的 RGBColor dict。"""
    from pptx.dml.color import RGBColor

    def _hex(h):
        h = h.lstrip("#")
        return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    return {k: _hex(v) for k, v in theme["palette"].items()}


if __name__ == "__main__":
    for tid, name, temp in list_themes():
        print(f"{tid:20s} {name}  ({temp})")
