---
name: subtitled-courseware-video
description: 把课件（强烈建议用 PowerPoint 导出的 PDF）生成带烧录中文字幕的 1080p 课程视频。字体高保真（PDF 300dpi 渲染）、配音音色由用户指定、字幕用 PIL 逐条烧录（本机 ffmpeg 无 libass 时的必需方案）、词级时间戳短句字幕、语气词与错别字清洗。当用户要"带字幕的课程视频""课件转视频并嵌字幕""给录播视频加字幕""字幕版课程视频"或在已跑过讲稿/配音后要合成带字幕成片时使用。无字幕的简单场景用 courseware-to-video。
version: 1.1.0
---

# 带字幕课程视频合成

把课件 + 分页讲稿 → 生成**烧录字幕**的 1080p 课程视频。相比 `courseware-to-video`，本技能专攻三件它做不好的事：**字体高保真**、**PIL 烧录字幕**（本机 ffmpeg 常无 libass，drawtext/subtitles 滤镜不可用）、**词级时间戳短句字幕 + 文本清洗**。

这是 `course-creation-workflow` 的 Stage 4（也可单独用）。前置卡点：**用户先在 PowerPoint 里导出 PDF**（保证字体和用户所见一致），再交给本技能。

## 触发条件

用户要生成"带字幕"的课程视频，或已经有了讲稿/配音、要合成字幕成片。

## 前置依赖

- `ffmpeg`/`ffprobe`：合成与转码。缺失见 `install-skill-dependency`。
- `PyMuPDF`（fitz）：PDF→PNG。`python3 -c "import fitz" || pip3 install PyMuPDF`
- `Pillow`：PIL 烧字幕。`python3 -c "import PIL" || pip3 install Pillow`
- `bl` CLI（百炼）：配音 TTS（`bl speech synthesize`）+ 字幕词级时间戳（`bl speech recognize`，默认模型 `qwen-audio-3.0-asr-flash-filetrans`）。规范见 `bailian-gen`，鉴权/报错见 `bailian-protocol`。
- 字幕字体 ttf：默认钉钉进步体 `~/Library/Fonts/DingTalk JinBuTi.ttf`（缺则让用户提供或换字体路径）。

⚠️ **不要用 edge-tts**：本机代理会拦截（403）。配音走 `bl speech synthesize` 或复用已生成的音频。

约定工作目录：`slides/`（幻灯片 PNG）、`audio/`（每页 mp3）、`asr_pages/`（每页词级 ASR json）、`subs_img/`（字幕合成中间件）、成片到用户工作目录 `outputs/`。

## 关键决策：音色

**配音音色不写死，每次由用户指定。** 开工前先问/确认用户要哪个音色（除非用户已明确，或本次是"只改了 PPT、复用上次音频"）。
- **先查用户的配音音色库** `~/.qoderwork/voice_library/voices.json`（编号音色：E 系 edge、B 系百炼预置、Q 系 qwen-audio 等；若无此文件，用随包 resources/voice_library/ 初始化），用户常直接说编号。
- 音色是主观选择：用户未定时**先出多版带编号的试听 mp3**（同一段讲稿各合成一小段）供挑选，不要直接定稿；用户反馈常是"某版+微调"。若怀疑成片与试听音色不一致，做**基频比对等客观核查**给出证据，不能只凭配置说没问题。
- 合成通道：cosyvoice 系走 `bl speech synthesize`；qwen-audio 系用音色库 `tools/synth_qwen_audio.py`（voice 参数须带模型前缀全串）。**复刻音色（如 C1）不吐词级时间戳**，字幕必须走 Step 3 ASR 回切；sambert 支持 `word_timestamp_enabled` 可省 ASR。
- 若用户上次已选定并生成过音频（如某个 voice 的 `audio/pNN.mp3`），本次只改了 PPT → **直接复用音频**，不要重新合成（见下方"仅改 PPT"分支）。
- **成片方式先确认**：用户可能选择自己录课（发生过）——那本技能只需交付讲稿/PDF素材，TTS 与合成全部取消，别白跑。

## 工作流程

### Step 1: 课件 → 幻灯片 PNG（字体高保真）

**首选 PDF 输入**（用户从 PowerPoint 导出的 PDF，字体与其所见完全一致）。用 PyMuPDF 按 **300dpi** 渲染：

```python
import fitz
doc=fitz.open("课件.pdf")
for i,page in enumerate(doc):
    page.get_pixmap(dpi=300).save(f"slides/slide_{i+1:03d}.png")
```

为什么 300dpi：150dpi 放大到 1080p 会发虚。渲染后成片用 CRF 18 保清晰度。

> 不要用 LibreOffice(soffice) 渲染 pptx——它会把 PingFang SC 等字体回退成手写体/普惠体，字重也不还原，出来"和用户在 PowerPoint 里看的不一样"。字体保真的唯一可靠路径是**让用户用 PowerPoint 导出 PDF**。

### Step 2: 分页讲稿 → 每页配音 mp3

讲稿来自 `video-to-paged-lecture-script`（或用户提供），**每页一段、页数与幻灯片一致**。

- **提页时必须丢弃整行「## 第 N 页：…」标题**——只按 `^##` 切分会把标题后缀留进正文被念进配音（踩过）。同理讲稿里的 ⚑ 标记、时间戳注记都要清掉。
- **讲稿里别写"1、2、3、4、5"数字串**：TTS 念汉字、ASR 回写数字，后续对齐会整段漂移（详见字幕规则）。定稿前先扫一遍改成文字表述。
- 逐页用 `bl speech synthesize`（用户选定的音色）合成 `audio/p01.mp3`…`audio/pNN.mp3`。
- **按讲稿自然段落分段合成、段间插 0.45s 静音**：讲课呼吸感更好，也给字幕断句提供清晰停顿信号。
- **qwen-audio 系注意**：`instruction` 生效、`instruct` 被忽略；语速指令会压低音色约 8% 并过度强调，**成片建议不传**（与试听一致）；同指令下语速波动大（257–339 字/分），语速要归一时用 `ffmpeg atempo` 按字数精确调、不变调，别靠重摇。
- **时长对账**：按 250 字/分估各页时长（中文讲课通用约 260 字/分），与目标时长对账，异常页（过快/过慢）单独检查。
- 页数必须 == 幻灯片数。校验：`ls audio/p*.mp3 | wc -l` 应等于 `ls slides/slide_*.png | wc -l`。

**分支——讲稿只改了部分页（最常见的返工场景）**：未变页**回退措辞**复用旧配音，只重配改动页与新增页（省额度）；改动页重跑 ASR，未变页的 asr json 直接复用。

**分支——仅改了 PPT、音频全复用**：跳过本步，直接用既有 `audio/pNN.mp3`（务必确认页数仍一致），进入 Step 4 重合成即可，无需重配音、也无需重跑 ASR（字幕时间轴不变）。

**分支——PPT 内嵌视频/宣传片**：该页 PDF 无文字，须解包 pptx 的 `ppt/media/*.mp4` + `ffprobe` 查时长；片段用 ffmpeg 归一（分辨率/帧率/音频采样与主片一致）后按位置插入 concat 序列（如插在 seg_02 与 seg_03 之间），该页不配音。

### Step 3: 每页配音 → 词级时间戳（qwen-audio-3.0-asr-flash-filetrans）

字幕要"短句、勤切换"，必须用**词级**时间戳，不能用整句（整句会两行溢出）。逐页对配音跑 ASR：

```bash
mkdir -p asr_pages
for f in audio/p*.mp3; do
  n=$(basename "$f" .mp3)
  bl speech recognize --url "$f" --model qwen-audio-3.0-asr-flash-filetrans --language zh --out "asr_pages/$n.json"
done
```

结果需含 `transcripts[0].sentences[].words[].{begin_time,end_time,text}`（毫秒）。合成脚本据此按停顿/字数切短句。

**模型选型（已实测）**：`qwen-audio-3.0-asr-flash-filetrans` 与 `fun-asr` 同一套异步文件转写 API、同一 JSON 结构，词级时间戳中位偏差仅 17ms（p90 40ms），可直接替换；且它尚有 36K 秒免费额度（fun-asr 的免费额度已过期，按 0.00022 元/秒计费）。免费额度用尽或模型不可用时再回落 `fun-asr`。
**不要用 paraformer 系**：句内词时间戳是按字数线性插值（相邻词间隙 100% 为 0），与真实发音中位偏差 225ms、p90 近 1 秒，长句字幕必漂移。`fun-asr-flash` 不支持文件转写（报 Model not exist），也不能用。

### Step 4: 准备文本清洗配置

字幕文本会做清洗（产品名替换 + 去语气词 + 错别字修正 + 术语大小写）。这些**随课程而变**，放外部 JSON，不写死。参考 `assets/subtitle_config.example.json`：

```json
{
  "product_replace": [["旧品牌","新品牌"],["OldBrand","NewBrand"]],
  "fillers": "呃嗯啊唉哦",
  "corrections": [["识别错别字","正确写法"]],
  "term_case": {"agent":"Agent","skill":"Skill"},
  "protect": ["新品牌","关键术语","得到"]
}
```

- `corrections` 要**先跑一遍预览、把 ASR 错别字挑出来再逐条填**（见 Step 6 QA），常见如"连立了在一起→连接在一起""白化之日→白桦汁"。
- ⚠️ `corrections` 在**空白压缩之后**跑，且**只在单条字幕行内**生效：英文术语误识要写成无空格串（如 `PromptEngineer→Prompt Engineer`）；跨行短语（如"信息安全、管理"被切在两条字幕）corrections 改不动，须直接改该页 ASR json 的词级 `punctuation` 再重合成。
- ASR 会把中文数词逆归一成阿拉伯数字（"一万八千"→"18000"），脚本已加数字串保护防止硬断落在数字中间；但字幕文本里出现的数字写法以 ASR 回写为准，若要还原汉字写法用 `corrections`。
- 可加 `"protect": ["新品牌", "关键术语"]` 列表保护品牌词/关键术语不被硬断劈开（`product_replace` 的目标词自动纳入）；`LEADWEAK`（的地得了）遇 protect 词不回拉，新增"得到"类词记得进 `protect`。
- `term_case`：英文术语统一大小写，按**词边界环绕匹配**（字母 lookaround），`\b` 对 CJK 失效（"的"是 `\w`），脚本已用 `(?<![A-Za-z])...(?![A-Za-z])`。
- **改了 config 或时间轴后，必须先 `rm subs_img/pNN_*.png` 再重合成**：字幕 PNG 有缓存，不删的话修正不会生效（真实返工教训）。

### Step 5: 先出 10s 预览

正式合成前，用 `ONLY` 只跑一页看字幕清晰度/是否溢出/术语拼写：

```bash
ONLY=8 python3 ~/.qoderwork/skills/subtitled-courseware-video/scripts/compose_subtitled_video.py \
  --slides slides --audio audio --asr asr_pages \
  --font "$HOME/Library/Fonts/DingTalk JinBuTi.ttf" \
  --config subtitle_config.json --out outputs/预览.mp4
```

抽帧 Read 核对后再跑全量。

### Step 6: 合成全片

```bash
python3 ~/.qoderwork/skills/subtitled-courseware-video/scripts/compose_subtitled_video.py \
  --slides slides --audio audio --asr asr_pages \
  --font "$HOME/Library/Fonts/DingTalk JinBuTi.ttf" \
  --config subtitle_config.json \
  --out "outputs/课程视频_字幕.mp4"
```

脚本行为：PDF 图适配 1920×1080 白底居中；字幕底部居中半透明圆角黑条 + 白字描边；每页 `--lead` 前置静音与字幕时间轴对齐；页间 `--fade` 淡入淡出；CRF 18 保清晰度；自动按 `audio/p*.mp3` 数量确定页数。可调参数：`--fs` 字号、`--gap/--minlen/--maxlen` 断句、`--mindur` 最短停留。

### Step 7: 交付

复制成片到用户工作目录，`present_files` 呈现，报告时长与大小。

## 字幕规则（脚本已内置，勿破坏）

- **保留标点**：ASR 的 `words[].punctuation` 必须拼回文本，否则"底层架构、企业价值"会丢顿号变成"底层架构企业价值"。
- **优先在标点处断句**：只靠 `maxlen` 硬断会把词劈开（"而/是"、"PPT/X"、"长/文"）。脚本在任一 `，。、！？；：` 处断句，`maxlen` 只作兜底；中文 `--maxlen 28` 比默认 15 自然得多。
- **不出单字字幕**：可见字数 < `--minchars`(默认4) 的碎片并入邻条，避免屏幕上只有一个"的"。
- **标点不出现在行首**：行首的 `”，。、` 等搬到上一条末尾。
- **不出断头/断尾虚词**：行首的 `的地得了` 往前搬；行尾的 `就也都还是在这那而和与…` 往后搬（两套字符集不重叠，否则会来回搬造成死循环）。以句末标点 `。！？` 结尾的视为完整句，不搬（"…的底气所在。"是对的）。
- **品牌词不被切断**：硬断可能把品牌名劈成两半。config 里加 `protect` 列表（品牌名、关键术语），脚本会把跨边界的残字往后搬；`product_replace` 的目标词自动纳入保护。
- **普通词也不被切断**：`maxlen` 硬断会把"维/度""返/回""获/取""结/果"劈两行。脚本末尾有 `_wordsafe` 用 **jieba** 判断断点是否落在词中间，是则把残头搬到下一条（`pip3 install jieba`，缺失时静默跳过、退化为只保护 `protect` 词）。注意 `LEADWEAK`（的地得了）会把行首的"得"拉回上一行，把"得到"劈开——已用 protect 词表做例外，新增此类词时记得加进 `protect`。
- **前引号不留行尾**：行尾的 `「“（《` 会与后半句分家（"…解决的是「" / "这件事怎么做」"）。`TAILPUNCT` 一律把它们搬到下一条行首。
- **ASR 选型只看时间戳质量，不看识别准确率**（文本反正会被 align_script 用讲稿原文覆盖）：默认用 **`qwen-audio-3.0-asr-flash-filetrans`**——与 fun-asr 同一套异步文件转写 API、同一 JSON 结构，实测 110 秒课程配音上词级时间戳中位偏差 17ms、p90 40ms、最大 120ms，且还有 36K 秒免费额度（到 2026-10-27）。`fun-asr` 免费额度已于 2026-05-11 过期，只在替代模型不可用时回落（0.00022 元/秒，17 分钟音频约 0.23 元）。**paraformer 系只给真实句边界、句内按字数线性插值**（相邻词间隙 100% 为 0），实测中位偏差 225ms、p90 985ms，长句（>8s）中段字幕明显漂移，即使免费也不要用；`fun-asr-flash` 不支持文件转写（报 Model not exist）。
- **短停顿不要闪空**：真实时间戳会让相邻字幕之间出现 0.1–0.4s 的真实停顿，逐帧合成时表现为字幕条闪一下消失。`--holdgap`（默认 0.45s）会把上一条延长到下一条起点。
- **讲稿里别写"1、2、3、4、5"这类数字串**：TTS 读成"一二三四五"、ASR 回写成"12345"，difflib 对齐时数字与汉字对不上，该句时间轴整段偏移；改成"步骤是什么"这类纯文字表述。
- **清洗与整理要交替两轮**：碎片合并发生在 normalize 之后，合并出的新文本吃不到 `corrections`。脚本按 tidy→normalize→tidy→normalize 跑两轮，否则像"…成品出去。这。"这种合并产物修不掉。
- **短句、勤切换**：按词级时间戳，停顿 ≥`gap`(默认0.28s) 即断；一条字幕最好 1 行、最多 2 行。
- **不溢出**：`wrap_text` 只 `return lines[:2]`，`maxw=W*0.86`；因为短句切分，基本单行，不会像"整句合并成一大行"那样冲出屏幕。
- **英文单词不散架**：ASR 词级拼接时会去掉字母间空格（"A G E N T"→"AGENT"），再按 `term_case` 归一成 "Agent"/"Skill"。

## Pitfalls

- **edge-tts 被墙**：本机代理 403，配音一律走 `bl speech synthesize` 或复用既有音频。
- **soffice 字体回退**：PingFang SC 等被换成手写体/普惠体、字重不还原 → 必须用 PowerPoint 导出的 PDF 作输入，别用 soffice 渲染 pptx。
- **本机 ffmpeg 无 libass/freetype**：`subtitles`/`drawtext` 滤镜不可用，字幕只能 PIL 画好 PNG 再 concat（本脚本即如此）。
- **150dpi 发虚**：PDF 按 300dpi 渲染，再 1080p + CRF 18。
- **整句字幕两行溢出**：必须用 `words[]` 词级时间戳切短句，别用 `sentences[].text` 整句。
- **讲稿与 PPT 不符**：合成前务必逐页把讲稿和幻灯片实际内容对一遍。旧课程的讲稿常残留 PPT 上根本没有的说法（发布日期、内部架构、已删掉的图表描述），配了音再发现就得重跑 TTS+ASR+该页合成。渲染完 slides 后先用 Read 看图核对，比返工便宜得多。
- **CJK 边界**：术语大小写/英文空格清理用字母 lookaround，不能用 `\b`。
- **subs_img 缓存不失效**：改了 `subtitle_config.json` 或某页时间轴后直接重合成，字幕仍是旧的——必须先 `rm subs_img/pNN_*.png`（改哪页删哪页，全局改就全删）。这是真实返工原因，重跑前先删缓存。
- **`bl speech recognize` 的 `--out` 是文件路径**（如 `--out asr.json` 即正常落盘），别把它当格式参数传。OSS 上传偶发 `UND_ERR_CONNECT_TIMEOUT`，重试即好。
- **页数错配**：`audio/p*.mp3` 数、`slides/slide_*.png` 数、讲稿页数三者必须一致，否则错位。仅改 PPT 复用音频时尤其要核对页数没变。
- **音色未确认就合成**：除非复用旧音频，合成前先和用户确认音色。

## Verification

1. 页数一致：slides 数 == audio 数 == asr_pages 数 == 讲稿页数。
2. 10s 预览已抽帧核对：字幕不溢出、≤2 行、英文术语拼写与大小写正确、语气词已去除。
3. 抽查修正点（`corrections` 里每条）在成片对应帧已正确显示。
4. 字体与用户 PowerPoint 所见一致（因用 PDF 渲染）。
5. 清晰度达标（300dpi + CRF 18），无发虚。
6. 成片时长≈各页音频总长 + 前置静音；已交付到工作目录并给 file:// 链接。
