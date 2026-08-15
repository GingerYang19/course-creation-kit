# course-outline-to-ppt

从课程大纲自动生成教学 PPT 课件的 Agent Skill。内置 6 套美观视觉模板（科技 / 学术 / 人文 / 商务 / 青瓷 / 高定），支持指定页数、上传参考资料作为内容依据，以及课件内容更新（用户指定方向或自动搜索新材料）。

## 触发场景

- 用户提供课程大纲，要求生成 PPT 课件
- 用户要求更新 / 刷新已有课件内容
- 用户提供参考资料，要求据此生成课件

关键词示例：「大纲生成 PPT」「课程课件」「课件生成」「更新课件」「课件更新」「根据大纲做 PPT」。

## 目录结构

```
course-outline-to-ppt/
├── SKILL.md              # 技能主文档（工作流、生成/更新流程、质量清单）
├── content-density.md    # 每页内容密度与丰富度规范
└── templates/
    ├── themes.json       # 6 套主题的配色 / 字体 / 母题定义
    ├── themes.md         # 主题画廊与选用指南
    └── themes.py         # 生成器调用的主题 API（get_theme / build_pptx_palette）
```

## 内置视觉主题

| id | 名称 | 适用方向 |
|----|------|----------|
| `deep-space` | 深空觉醒 | 科技 / 通用 |
| `scholar-green` | 墨绿学术 | 高校 / 研究 |
| `warm-terracotta` | 暖橙人文 | 人文 / 分享 |
| `executive-slate` | 商务灰金 | 企业汇报 |
| `porcelain-teal` | 青瓷科技 | 科技 / 产品 |
| `aubergine-premium` | 绛紫高定 | 高端 / 品牌 |

所有主题均为实色配色，规避了紫渐变、深蓝霓虹等常见 AI-slop 组合。

## 使用方式

作为 QoderWork / Agent Skill 使用：将本仓库放入技能目录（如 `~/.qoderwork/skills/course-outline-to-ppt/`），Agent 在识别到大纲生成 PPT 的意图时自动调用 `SKILL.md` 中定义的工作流。生成阶段依赖 `pptx` 技能与 `python-pptx`。

## License

MIT
