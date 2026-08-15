# course-creation-kit

一套把**一份文字稿**做成**一讲完整视频课**的 Agent 技能包：文字稿 → PPT 课件 → 逐页讲稿 → AI 配音 → 带烧录字幕的 1080p 成片。总编排技能是 `course-creation-workflow`，其余为它调度的子技能与资源。机器活之间夹**人工卡点**（需求澄清、手动优化 PPT、逐页过稿、挑音色、预览确认），每个决策点都会停下来等你。

> **这是通用版**：不含任何品牌模板 / logo / 吉祥物 / 复刻音色。请自备【课程模板】【品牌 logo 等素材】【个人音色库】后使用——每处该放什么、放哪里，下面和各技能的 README 里都写了。

*A skill kit that turns **a script** into **a full video lesson**: script → slides → per-page lecture notes → AI voiceover → 1080p video with burned-in subtitles. Orchestrated by `course-creation-workflow`, with human checkpoints between each automated stage. **This is the generic edition** — it ships **no** brand template, logo, mascot, or cloned voice; plug in your own (see below).*

## 包内容 / Contents

```
course-creation-kit/
├── skills/                                  8 个技能（源码目录，非 zip）
│   ├── course-creation-workflow/              总编排器（从零制课流水线）
│   │   └── assets/ppt-template/               ← 放你自己的课程 PPT 模板（默认空）
│   ├── courseware-brand-styling/              课件品牌化 + 套模板方法论（通用）
│   │   └── assets/                            ← 放你自己的 logo / 吉祥物（默认空）
│   ├── course-outline-to-ppt/                 大纲→PPT（内置通用模板，无品牌）
│   ├── courseware-to-lecture-script/          课件→口语化逐页讲稿
│   ├── subtitled-courseware-video/            课件+配音→带烧录字幕视频（主出片路径）
│   ├── courseware-to-video/                   课件→无字幕视频（简单场景）
│   ├── bailian-gen/                           阿里云百炼生成入口（TTS/ASR/图/视频）
│   └── bailian-protocol/                      bl CLI 家族共享协议（鉴权/安装/错误处理）
└── resources/
    └── voice_library/                         音色库模板（复制到 ~/.qoderwork/voice_library/）
        ├── voices.json                        音色登记表（只含公共示例音色，无复刻音色）
        ├── README.md                          三条 TTS 通道 / 复刻 / 字幕指南
        └── tools/                             合成与字幕工具脚本
```

## 你需要自备的三样东西 / What you must supply

| 要素 | 放哪里 | 说明 |
|---|---|---|
| **课程 PPT 模板** | `skills/course-creation-workflow/assets/ppt-template/` | 你的占位版式模板（10×5.625in）；没有就走 `course-outline-to-ppt` 内置通用模板 |
| **品牌 logo / 吉祥物** | `skills/courseware-brand-styling/assets/logo/` 与 `assets/mascot/` | 你的品牌资产；没有吉祥物就跳过相关步骤 |
| **个人音色库** | `~/.qoderwork/voice_library/`（从 `resources/voice_library/` 复制后登记） | 你的音色；通用包只预置公共系统音色作示例 |

每个目录里都有 `README.md` 说明该放什么、怎么在技能里引用。

## 安装 / Install

见 [INSTALL.md](./INSTALL.md)。简版：把 `skills/` 下每个目录拷进 `~/.qoderwork/skills/`，把 `resources/voice_library/` 拷进 `~/.qoderwork/voice_library/`，装好 `bl` CLI 与本机依赖，然后自备上表三样素材。

*See [INSTALL.md](./INSTALL.md). TL;DR: copy each dir under `skills/` into `~/.qoderwork/skills/`, copy `resources/voice_library/` into `~/.qoderwork/voice_library/`, install the `bl` CLI and local deps, then supply the three assets above.*

## 开始使用 / Usage

对你的 Agent 说：**"根据这篇文字稿做课程视频"** 并附上 .md 文字稿。编排器会按「需求澄清 → PPT → 讲稿 → 配音 → 带字幕成片」推进，每个人工决策点停下等你。

## 依赖 / Dependencies

- Python3 + `pip install python-pptx pymupdf pillow jieba`
- ffmpeg（`brew install ffmpeg`）
- LibreOffice（`brew install --cask libreoffice`，PPT 自检拼版用）
- 配音/ASR：`bl` CLI（阿里云百炼，消耗你自己账号额度）或 edge-tts（免费）

## 注意事项 / Notes

- 出片必须用 **PowerPoint 导出的 PDF**（soffice 渲染 pptx 会字体回退失真）。
- 讲稿里避免数字串（写"三到五份"别写"3-5份"），否则字幕对轴会出错。
- 一讲之内只用一套 PPT 模板，不混用。
- 配音默认走 edge-tts（免费、吐词级时间戳）或百炼复刻音色（更贴讲师本人、按量计费）。

## License

[MIT](./LICENSE)
