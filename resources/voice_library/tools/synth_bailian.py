#!/usr/bin/env python3
"""百炼复刻音色批量合成（CosyVoice v2/v3/v3.5 系列）。

用法:
    python3 synth_bailian.py --voice B10 --text "要合成的文字" --out a.mp3
    python3 synth_bailian.py --voice B10 --file script.txt --out a.mp3
    python3 synth_bailian.py --list

要点:
  * 复刻音色的 target_model 必须与合成时的 model 完全一致，否则失败。
  * 受限网络需 CA 证书时，把系统根证书导出为本库根目录的 ca_bundle.pem，脚本会自动注入（存在才注入，通用包不随带）。
  * format 必须显式传，否则报 InputRequired。
  * 长文本按标点切段合成再用 ffmpeg 拼接，避免单次请求过长。
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time

LIB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CA = os.path.join(LIB, "ca_bundle.pem")
if os.path.exists(CA):
    os.environ.setdefault("SSL_CERT_FILE", CA)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", CA)

import dashscope  # noqa: E402
from dashscope.audio.tts_v2 import AudioFormat, SpeechSynthesizer  # noqa: E402

VOICES_JSON = os.path.join(LIB, "voices.json")
MAX_CHARS = 240   # 单次请求上限，留余量
RETRY = 4


def load_cfg():
    cfg = json.load(open(os.path.expanduser("~/.bailian/config.json")))
    dashscope.api_key = cfg["api_key"]
    ws = cfg.get("workspace_id") or "ws-xr6vdbo8pfxxo46b"
    dashscope.base_http_api_url = f"https://{ws}.cn-beijing.maas.aliyuncs.com/api/v1"


def load_voices():
    if not os.path.exists(VOICES_JSON):
        return {}
    data = json.load(open(VOICES_JSON, encoding="utf-8"))
    out = {}
    for v in data.get("voices", data if isinstance(data, list) else []):
        out[v.get("id")] = v
    return out


def split_text(text, limit=MAX_CHARS):
    """按句末标点切分，单句超长再按逗号切。"""
    text = re.sub(r"\s+", "", text)
    sents = re.findall(r"[^。！？；\n]*[。！？；]|[^。！？；\n]+", text)
    chunks, cur = [], ""
    for s in sents:
        if len(cur) + len(s) <= limit:
            cur += s
            continue
        if cur:
            chunks.append(cur)
        while len(s) > limit:
            cut = max(s.rfind("，", 0, limit), s.rfind("、", 0, limit))
            cut = cut + 1 if cut > limit // 3 else limit
            chunks.append(s[:cut])
            s = s[cut:]
        cur = s
    if cur:
        chunks.append(cur)
    return chunks


def synth_one(text, model, voice_id, fmt):
    last = None
    for attempt in range(RETRY):
        try:
            syn = SpeechSynthesizer(model=model, voice=voice_id, format=fmt)
            audio = syn.call(text)
            if audio:
                return audio
            last = RuntimeError("empty audio returned")
        except Exception as exc:  # noqa: BLE001
            last = exc
        time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"合成失败: {last}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", help="voices.json 里的编号，如 B10")
    ap.add_argument("--voice-id", help="直接给 voice_id，跳过音色库")
    ap.add_argument("--model", help="合成模型，默认取音色库记录的 target_model")
    ap.add_argument("--text")
    ap.add_argument("--file")
    ap.add_argument("--out", default="out.mp3")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    lib = load_voices()
    if args.list:
        for vid, v in lib.items():
            print(f"{vid:5s} {v.get('provider','?'):10s} {v.get('name','')} "
                  f"[{v.get('model') or v.get('target_model','')}]")
        return

    load_cfg()

    if args.voice_id:
        voice_id, model = args.voice_id, args.model
    else:
        if args.voice not in lib:
            sys.exit(f"音色库里没有 {args.voice}，用 --list 查看")
        v = lib[args.voice]
        voice_id = v["voice_id"]
        model = args.model or v.get("model") or v.get("target_model")
    if not model:
        sys.exit("缺少 --model，且音色库未记录 target_model")

    text = args.text or open(args.file, encoding="utf-8").read()
    chunks = split_text(text)
    fmt = AudioFormat.MP3_48000HZ_MONO_256KBPS
    print(f"音色 {voice_id}\n模型 {model}\n共 {len(text)} 字，切 {len(chunks)} 段")

    tmpdir = tempfile.mkdtemp(prefix="bl_tts_")
    parts = []
    for i, c in enumerate(chunks, 1):
        audio = synth_one(c, model, voice_id, fmt)
        p = os.path.join(tmpdir, f"p{i:03d}.mp3")
        with open(p, "wb") as f:
            f.write(audio)
        parts.append(p)
        print(f"  [{i}/{len(chunks)}] {len(c):3d}字 -> {os.path.getsize(p)/1024:.0f}KB")

    if len(parts) == 1:
        os.replace(parts[0], args.out)
    else:
        lst = os.path.join(tmpdir, "list.txt")
        with open(lst, "w") as f:
            for p in parts:
                f.write(f"file '{p}'\n")
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat",
             "-safe", "0", "-i", lst, "-c", "copy", args.out],
            check=True,
        )
    print(f"已输出 {args.out}")


if __name__ == "__main__":
    main()
