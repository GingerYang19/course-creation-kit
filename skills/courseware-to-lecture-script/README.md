# courseware-to-lecture-script

从 PPT / PDF 课件文件自动生成口语化讲课稿（逐字稿）的 Agent Skill。支持指定总时长自动分配到各页，输出 Markdown 文件。

## 触发场景

用户上传 `.pptx` 或 `.pdf` 课件文件，并要求生成讲课稿 / 逐字稿 / 讲稿 / 备课稿。关键词示例：「生成讲课稿」「课件转讲稿」「写逐字稿」「备课稿」「lecture script」。

## 目录结构

```
courseware-to-lecture-script/
└── SKILL.md    # 技能主文档（工作流、去 AI 味写作规范、验证清单）
```

## 核心特性

- 逐页提取课件标题、要点、备注与图表说明，逐字保留关键术语与金句
- 按总时长与内容密度加权分配每页用时（中文口语约 200-250 字/分钟）
- 严格的「去 AI 味」写作规范：节奏不均匀、禁止机械枚举、过渡语多样化、句子长短交错、不用破折号、不用书面连接词与强调套话、结尾不升华
- 输出结构化 Markdown 讲课稿，每页标注建议用时
- 内置验证清单，确保总字数与指定时长匹配（允许 ±10%）

## 使用方式

作为 QoderWork / Agent Skill 使用：将本仓库放入技能目录（如 `~/.qoderwork/skills/courseware-to-lecture-script/`）。提取课件内容时依赖 `pptx` / `pdf` 技能。

## License

MIT
