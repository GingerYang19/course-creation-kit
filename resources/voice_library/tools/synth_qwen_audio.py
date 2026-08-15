#!/usr/bin/env python3
"""百炼 qwen-audio-3.0-tts 系列合成（workspace HTTP 端点，非 dashscope SDK）。

用法:
    python3 synth_qwen_audio.py --voice Q1 --text "要合成的文字" --out a.mp3
    python3 synth_qwen_audio.py --voice Q1 --file script.txt --out a.mp3
    python3 synth_qwen_audio.py --list

要点:
  * 音色与模型严格绑定：plus 的音色换到 flash 会报 [cosyvoice]Engine error 411。
  * 基础音色的 voice 参数是带模型前缀的完整串，
    如 qwen-audio-3.0-tts-plus-longsonglinwang，不可截前缀。
  * 系统音色（如 longanlufeng）直接传短名。
  * 返回的 OSS url 可能是 http://，必须改写成 https:// 再下载（代理拦 80 端口）。
  * 长文本按句末标点切段（单段 <=260 字）分段合成再 ffmpeg 拼接。
  * plus 支持 instruct 指令控制（在文本前加指令或按官方文档传参，具体以官方为准）。
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

LIB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOICES_JSON = os.path.join(LIB, "voices.json")
CFG = os.path.expanduser("~/.bailian/config.json")
MAXLEN = 260
RETRY = 3


def load_cfg():
    cfg = json.load(open(CFG))
    ws = cfg.get("workspace_id") or "ws-xr6vdbo8pfxxo46b"
    api = (f"https://{ws}.cn-beijing.maas.aliyuncs.com/api/v1"
           "/services/audio/tts/SpeechSynthesizer")
    return cfg["api_key"], api


def load_voices():
    data = json.load(open(VOICES_JSON, encoding="utf-8"))
    return {v["id"]: v for v in data.get("voices", [])}


def split_text(text, limit=MAXLEN):
    text = re.sub(r"\s+", "", text)
    parts = re.split(r"(?<=[。！？；])", text)
    chunks, cur = [], ""
    for p in parts:
        if not p:
            continue
        if len(cur) + len(p) > limit and cur:
            chunks.append(cur)
            cur = p
            while len(cur) > limit:  # 单句超长的兜底硬切
                chunks.append(cur[:limit])
                cur = cur[limit:]
        else:
            cur += p
    if cur:
        chunks.append(cur)
    return chunks


def synth(text, model, voice_id, api, key, out):
    payload = json.dumps(
        {"model": model,
         "input": {"text": text, "voice": voice_id,
                   "format": "mp3", "sample_rate": 24000}},
        ensure_ascii=False)
    r = subprocess.run(["curl", "-sS", "-X", "POST", api,
                        "-H", f"Authorization: Bearer {key}",
                        "-H", "Content-Type: application/json",
                        "--data-binary", payload],
                       capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
    except Exception:
        sys.exit(f"bad response: {r.stdout[:400]} {r.stderr[:300]}")
    au = (d.get("output") or {}).get("audio")
    url = au.get("url") if isinstance(au, dict) else None
    if not url:
        sys.exit(f"no audio url: {json.dumps(d, ensure_ascii=False)[:600]}")
    if url.startswith("http://"):
        url = "https://" + url[len("http://"):]
    for attempt in range(RETRY):
        r2 = subprocess.run(["curl", "-sS", "--max-time", "120", "-o", out, url],
                            capture_output=True, text=True)
        if r2.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 3000:
            return
        print(f"  retry download ({attempt+1}/{RETRY}): {r2.stderr.strip()[:120]}")
    sys.exit(f"download failed: {url[:120]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", help="voices.json 里的编号，如 Q1")
    ap.add_argument("--voice-id", help="直接给 voice 参数，跳过音色库")
    ap.add_argument("--model", default="qwen-audio-3.0-tts-plus")
    ap.add_argument("--text")
    ap.add_argument("--file")
    ap.add_argument("--out", default="out.mp3")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    lib = load_voices()
    if args.list:
        for vid, v in lib.items():
            if v.get("provider") == "bailian-qwen-audio-3.0-tts":
                print(f"{vid:5s} {v.get('name','')} [{v.get('model','')}]"
                      f" voice={v.get('voice_id','')}")
        return

    if args.voice_id:
        voice_id, model = args.voice_id, args.model
    else:
        if args.voice not in lib:
            sys.exit(f"音色库里没有 {args.voice}，用 --list 查看")
        v = lib[args.voice]
        voice_id = v["voice_id"]
        model = v.get("model", args.model)

    key, api = load_cfg()
    text = args.text or open(args.file, encoding="utf-8").read()
    chunks = split_text(text)
    print(f"音色 {voice_id}\n模型 {model}\n共 {len(text)} 字，切 {len(chunks)} 段")

    if len(chunks) == 1:
        synth(chunks[0], model, voice_id, api, key, args.out)
    else:
        tmpdir = tempfile.mkdtemp(prefix="qa_tts_")
        lst = os.path.join(tmpdir, "list.txt")
        with open(lst, "w") as f:
            for i, c in enumerate(chunks, 1):
                p = os.path.join(tmpdir, f"p{i:03d}.mp3")
                synth(c, model, voice_id, api, key, p)
                print(f"  [{i}/{len(chunks)}] {len(c):3d}字")
                f.write(f"file '{p}'\n")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat",
                        "-safe", "0", "-i", lst, "-c", "copy", args.out],
                       check=True)
    print(f"已输出 {args.out}")


if __name__ == "__main__":
    main()
