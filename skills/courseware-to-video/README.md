# courseware-to-video

从 PPT / PDF 课件文件自动生成课程视频的 Agent Skill：幻灯片 + AI 配音 + 淡入淡出转场，合成为 1080p MP4。

## 触发场景

用户上传课件并要求生成视频。关键词示例：「课件生成视频」「PPT 转视频」「课件录播」「自动生成课程视频」「courseware to video」。

## 目录结构

```
courseware-to-video/
├── SKILL.md                    # 技能主文档（依赖检查、工作流、参数说明）
└── scripts/
    └── compose_video.py        # 视频合成脚本（图片序列 + TTS + 转场 → MP4）
```

## 工作流程

1. 课件转幻灯片图片：PDF 用 PyMuPDF 直接渲染；PPT 先经 LibreOffice 转 PDF 再渲染
2. 生成讲稿 JSON（每页一条 narration），可自动调用 `courseware-to-lecture-script` 生成，或由用户提供
3. 运行 `compose_video.py` 合成：TTS 配音 + 淡入淡出转场 + 白底居中适配
4. 交付 MP4，报告时长与文件大小

## 依赖

- `ffmpeg`（视频/音频合成）
- `edge-tts`（TTS 配音）
- `PyMuPDF`（PDF 渲染）
- `LibreOffice`（PPT 转 PDF，仅 PPT 输入时需要）

## 合成脚本用法

```bash
python3 scripts/compose_video.py \
  --slides ./slides \
  --script ./script.json \
  --output ./output/课程视频.mp4 \
  --voice zh-CN-XiaoxiaoNeural \
  --resolution 1920x1080 \
  --fade 0.5
```

## 使用方式

作为 QoderWork / Agent Skill 使用：将本仓库放入技能目录（如 `~/.qoderwork/skills/courseware-to-video/`）。

## License

MIT
