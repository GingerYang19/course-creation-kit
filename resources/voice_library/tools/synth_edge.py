# -*- coding: utf-8 -*-
"""edge-tts 合成工具（带重试）。

用法：
    from synth_edge import synth, synth_file
    audio, marks = asyncio.run(synth("文本", "zh-CN-YunyangNeural", "-15%"))

受限网络（可选）：
  若你的网络对 HTTPS 做中间人代理，需在 import edge_tts 前用 truststore 注入系统根证书，
  否则报 CERTIFICATE_VERIFY_FAILED；某些网关还需给 speech.platform.bing.com 域名加白，
  并对 WSS 握手做重试（脚本已内置退避重试）。普通网络下 truststore 缺失也能正常跑。
"""
try:
    import truststore
    truststore.inject_into_ssl()   # 受限网络注入系统根证书；未安装则跳过
except ImportError:
    pass

import asyncio
import json

import edge_tts

RETRY = 5


async def synth(text, voice="zh-CN-YunyangNeural", rate="+0%", volume="+0%"):
    """返回 (mp3_bytes, marks)；marks 为词级时间戳，单位秒。"""
    last = None
    for attempt in range(1, RETRY + 1):
        try:
            comm = edge_tts.Communicate(text, voice, rate=rate, volume=volume,
                                        boundary="WordBoundary")
            marks, buf = [], bytearray()
            async for ch in comm.stream():
                if ch["type"] == "audio":
                    buf += ch["data"]
                elif ch["type"] == "WordBoundary":
                    marks.append({"text": ch["text"],
                                  "start": round(ch["offset"] / 1e7, 3),
                                  "dur": round(ch["duration"] / 1e7, 3)})
            if not buf:
                raise RuntimeError("返回空音频")
            return bytes(buf), marks
        except Exception as e:
            last = e
            await asyncio.sleep(2 * attempt)   # 线性退避
    raise RuntimeError(f"{voice} 重试 {RETRY} 次仍失败：{last}")


async def synth_file(text, out_mp3, voice="zh-CN-YunyangNeural", rate="+0%",
                     marks_json=None):
    """合成并落盘；可选把词级时间戳写成 json。"""
    audio, marks = await synth(text, voice, rate)
    with open(out_mp3, "wb") as f:
        f.write(audio)
    if marks_json:
        with open(marks_json, "w", encoding="utf-8") as f:
            json.dump(marks, f, ensure_ascii=False, indent=1)
    return marks


if __name__ == "__main__":
    import sys

    txt = sys.argv[1] if len(sys.argv) > 1 else "这是一段配音测试。"
    voice = sys.argv[2] if len(sys.argv) > 2 else "zh-CN-YunyangNeural"
    rate = sys.argv[3] if len(sys.argv) > 3 else "-15%"
    m = asyncio.run(synth_file(txt, "out.mp3", voice, rate, "out_marks.json"))
    print(f"out.mp3 已生成，词级时间戳 {len(m)} 条")
