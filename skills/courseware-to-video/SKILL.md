---
name: courseware-to-video
description: 从PPT/PDF课件文件自动生成课程视频（幻灯片+AI配音+转场动画→1080p MP4）。当用户提到"课件生成视频""PPT转视频""课件录播""自动生成课程视频""courseware to video"或上传课件要求生成教学视频时使用。
version: 1.0.0
---

# 课件自动生成课程视频

将 PPT/PDF 课件转为带 AI 配音和淡入淡出转场的 1080p MP4 课程视频。

## 依赖检查

执行前确认以下工具可用，缺失则安装：

```bash
# 检查并安装
which ffmpeg || brew install ffmpeg
python3 -c "import edge_tts" 2>/dev/null || pip3 install edge-tts
python3 -c "import fitz" 2>/dev/null || pip3 install PyMuPDF
# PPT转图片需要 LibreOffice（仅PPT输入时需要）
which soffice || brew install --cask libreoffice
```

## 工作流程

### Step 1: 课件转幻灯片图片

在工作目录下创建 `slides/` 文件夹存放图片。

**PDF 输入**（PyMuPDF 直接渲染）:

```python
import fitz
doc = fitz.open("课件.pdf")
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=200)
    pix.save(f"slides/slide_{i+1:03d}.png")
```

**PPT 输入**（先转PDF再渲染）:

```bash
soffice --headless --convert-to pdf --outdir ./slides "课件.pptx"
```

然后用 PyMuPDF 将生成的 PDF 逐页渲染为 PNG（同上）。

注意：图片按文件名排序即为幻灯片顺序，命名用零填充编号（slide_001.png）。

### Step 2: 生成讲稿

讲稿为 JSON 文件，每页一条记录：

```json
[
  {"slide": 1, "narration": "大家好，欢迎来到今天的课程..."},
  {"slide": 2, "narration": "首先我们来看第一个概念..."}
]
```

**方式A — 自动生成（默认）：**

调用 `courseware-to-lecture-script` skill 生成逐字稿（Markdown），然后将 Markdown 按页拆分转为上述 JSON 格式。拆分规则：逐字稿中 `## 第N页` 或 `## Slide N` 标题下的内容即为该页 narration。

**方式B — 用户提供：**

用户直接提供讲稿文件（JSON/Markdown/纯文本），解析后转为 JSON 格式。

### Step 3: 合成视频

运行合成脚本：

```bash
python3 ~/.qoderwork/skills/courseware-to-video/scripts/compose_video.py \
  --slides ./slides \
  --script ./script.json \
  --output ./output/课程视频.mp4 \
  --voice zh-CN-XiaoxiaoNeural \
  --resolution 1920x1080 \
  --fade 0.5
```

**可选参数：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --voice | zh-CN-XiaoxiaoNeural | TTS音色 |
| --resolution | 1920x1080 | 输出分辨率 |
| --fade | 0.5 | 转场淡入淡出时长(秒) |

**推荐音色（edge-tts）：**

- `zh-CN-XiaoxiaoNeural` — 女声，温和自然（默认）
- `zh-CN-YunxiNeural` — 男声，沉稳
- `zh-CN-XiaoyiNeural` — 女声，活泼
- `zh-CN-YunjianNeural` — 男声，播音风格

可用 `edge-tts --list-voices | grep zh-CN` 查看全部中文音色。

### Step 4: 交付

将生成的 MP4 文件复制到输出目录，用 present_files 呈现给用户。报告视频时长和文件大小。

## 注意事项

- 每页 narration 建议 100-300 字（对应约 30-90 秒语音），过长会导致单页停留太久
- 若某页无需配音（如纯过渡页），narration 留空字符串即可跳过
- 合成耗时约为视频总时长的 1/3~1/2（主要是 TTS 合成时间）
- PPT 转图片依赖 LibreOffice 渲染，复杂动画/视频元素会被静态化
- 输出视频为白底居中适配，原始比例不变形
