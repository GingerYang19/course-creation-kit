# 配音音色库（模板）

课程配音的音色登记表。清单在 `voices.json`，合成与字幕工具在 `tools/`。**通用包只预置公共系统音色作示例，不含任何复刻音色与试听样本**——请按下面说明登记你自己的音色，试听 mp3 自建放进 `samples/`。

## 三条 TTS 通道

- **edge-tts**（`tools/synth_edge.py`）：微软公共音色，**免费不限量**，而且直接吐词级时间戳，字幕不用再跑一遍 ASR。首选。
- **百炼 cosyvoice**（`tools/synth_bailian.py`）：基础音色 + **声音复刻**。要讲师本人出声就走 cosyvoice 复刻自己的声音（准备 10–20 秒干净人声样本）。复刻音色按量计费且不吐词级时间戳，字幕要另跑 ASR。
- **百炼 qwen-audio-3.0-tts**（`tools/synth_qwen_audio.py`）：qwen-audio 系基础音色，走 workspace HTTP 端点。

配速参考：edge-tts 中文原速约 290 字/分，`rate="-15%"` 约 246 字/分。挑一个基准配速贴合你的课程节奏。

## edge-tts 调用

```python
import asyncio, edge_tts

async def synth(text, voice="zh-CN-YunyangNeural", rate="-15%"):
    comm = edge_tts.Communicate(text, voice, rate=rate,
                                boundary="WordBoundary")   # 中文默认只给整句，必须显式指定
    sm, marks, buf = edge_tts.SubMaker(), [], bytearray()
    async for ch in comm.stream():
        if ch["type"] == "audio":
            buf += ch["data"]
        elif ch["type"] == "WordBoundary":
            sm.feed(ch)
            marks.append({"text": ch["text"],
                          "start": ch["offset"] / 1e7,      # 单位 100 纳秒
                          "dur": ch["duration"] / 1e7})
    return bytes(buf), marks
```

`tools/synth_edge.py` 是带退避重试的完整版，批量跑整门课直接用它。

> **公司/受限网络注意**：若你的网络对 HTTPS 做中间人代理，`import edge_tts` 前需先 `truststore.inject_into_ssl()` 注入系统根证书，否则报 `CERTIFICATE_VERIFY_FAILED`；某些网关还需要给 `speech.platform.bing.com` 域名加白，并对 WSS 握手做重试。普通网络无需这些。

## cosyvoice 调用

只有 WebSocket 通道，HTTP 直调会报 `current user api does not support http call`，必须走 dashscope SDK。`format` 是必填的，不传报 InputRequired。

```python
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer, AudioFormat

s = SpeechSynthesizer(model="cosyvoice-v1", voice="longshu",
                      format=AudioFormat.MP3_48000HZ_MONO_256KBPS)
audio = s.call(text)
```

受限网络需把系统钥匙串导出成 `ca_bundle.pem`（通用包不随带，自行生成），运行时设 `SSL_CERT_FILE` 指向它。`dashscope.base_http_api_url` 要带你自己的业务空间 ID，形如 `https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com/api/v1`。

`tools/synth_bailian.py` 会按标点切段、失败退避重试、多段用 ffmpeg 拼接：

```bash
python3 tools/synth_bailian.py --list
python3 tools/synth_bailian.py --voice B01 --file 讲稿.txt --out 第一讲.mp3
```

计费：控制台能选的复刻模型（cosyvoice v2/v3/v3.5、qwen3-tts-vc）都没有免费额度，但单价低（约 1.5 元/万字符，一节 3000 字约 0.45 元）。有免费额度的 cosyvoice-v1（10000 字符）和 qwen-audio-3.0-tts-flash 在控制台下拉里选不到，只能走 API。两个硬约束：`voice_id` 与合成 `model` 必须严格配对，换模型得重新复刻；单个音色一年内没被调用会被系统自动删除。

## 字幕

`tools/make_subs.py` 把词级时间戳合并成短句字幕。断句是三级的：先按句号感叹号问号切完整句，句子超长再在逗号顿号处细分，还超长才按词边界近似均分，最后把不足 6 字的碎片并回前一条。单条上限 18 字。

```bash
python3 make_subs.py all <样本目录>       # 批量
python3 make_subs.py <样本名> <样本目录>   # 单个，并打印断句预览
```

相比先 TTS 再用 ASR 反推时间戳，这条路的字幕文本直接来自原始讲稿，不存在识别误差，错字从源头就不会出现。

## 音色池子有多大

edge-tts 的 zh-CN 只有 8 个音色，男声四个（云健、云扬、云希、云夏），女声两个（晓晓、晓伊），外加东北话小北和陕西话小妮。池子很浅。女声不够用时可以借多语种音色说中文，`en-US-AvaMultilingualNeural`、`en-US-EmmaMultilingualNeural`、`fr-FR-VivienneMultilingualNeural`、`de-DE-SeraphinaMultilingualNeural`、`pt-BR-ThalitaMultilingualNeural` 这五个都能出中文且照常给词级时间戳，只是可能带口音。

百炼基础音色有近 600 个，选择面大得多，但音色和模型严格绑定，混用会报 `[cosyvoice]Engine error 411`。

## 声音复刻

创建入口在百炼控制台：左侧「语音模型」→ 右上切「语音合成」→ 卡片「声音复刻」→ tab「复刻声音」。支持浏览器实时录音或直接上传本地文件，**不需要**像 API 那样先把音频传到公网 URL。上传规格：wav/mp3/m4a、单双声道均可、16KHz 以上采样率、10s 以上（建议 15–20s）、小于 10MB。

界面上的音色 ID 是截断显示的，别照抄，用 API 取完整值：

```python
from dashscope.audio.tts_v2 import VoiceEnrollmentService
svc = VoiceEnrollmentService()
print(svc.list_voices(page_index=0, page_size=50))
```

复刻音色不给词级时间戳，需要合成后用 fun-asr 回切对轴（有免费额度）。回切时用讲稿原文做校正——ASR 会把「Skill」听成「scale」、「Prompt」听成「promoter」这类。

## 登记你自己的音色

1. 复刻/选定音色后，在 `voices.json` 的 `voices` 数组追加一条（参考现有条目结构与占位条 `C1`）。
2. 生成一段试听 mp3 放进 `samples/`（自建目录），把 `sample` 字段填成相对路径。
3. 男女声都备一个，方便按课程切换。
