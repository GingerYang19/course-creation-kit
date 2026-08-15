#!/usr/bin/env python3
"""
课件视频合成脚本：幻灯片图片 + 讲稿文本 → 带配音和转场的课程视频。

用法:
  python3 compose_video.py --slides ./slides --script script.json --output course.mp4

依赖:
  - edge-tts (pip3 install edge-tts)
  - ffmpeg (brew install ffmpeg)

script.json 格式:
  [
    {"slide": 1, "narration": "第一页的旁白文本..."},
    {"slide": 2, "narration": "第二页的旁白文本..."}
  ]
  slide 编号从1开始，对应 slides 目录中按文件名排序的第N张图片。
"""

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def check_dependencies():
    """检查 edge-tts 和 ffmpeg 是否可用。"""
    missing = []
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        missing.append("edge-tts (pip3 install edge-tts)")
    if subprocess.run(["which", "ffmpeg"], capture_output=True).returncode != 0:
        missing.append("ffmpeg (brew install ffmpeg)")
    if missing:
        print("缺少依赖:", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        sys.exit(1)


def get_slide_images(slides_dir: str) -> list[Path]:
    """获取排序后的幻灯片图片列表。"""
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    images = sorted(
        p for p in Path(slides_dir).iterdir()
        if p.suffix.lower() in exts
    )
    if not images:
        print(f"错误: {slides_dir} 中未找到图片文件", file=sys.stderr)
        sys.exit(1)
    return images


def get_audio_duration(audio_path: str) -> float:
    """用 ffprobe 获取音频时长(秒)。"""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "csv=p=0",
        audio_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


async def synthesize_speech(text: str, output_path: str, voice: str):
    """调用 edge-tts 合成语音。"""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def create_segment(image_path: Path, audio_path: str, output_path: str,
                   resolution: str, fade_duration: float = 0.5):
    """将单张图片+音频合成为带淡入淡出的视频片段。"""
    duration = get_audio_duration(audio_path) + 0.8  # 前后各留0.4s静默
    w, h = resolution.split("x")

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(image_path),
        "-i", audio_path,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-vf", (
            f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=white,"
            f"fade=t=in:st=0:d={fade_duration},"
            f"fade=t=out:st={duration - fade_duration}:d={fade_duration}"
        ),
        "-af", f"adelay=400|400,apad=pad_dur=0.4",
        "-t", str(duration),
        "-shortest",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg 错误 ({image_path.name}): {result.stderr[-500:]}", file=sys.stderr)
        sys.exit(1)


def concatenate_segments(segment_paths: list[str], output_path: str):
    """用 concat demuxer 拼接所有片段。"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for seg in segment_paths:
            f.write(f"file '{seg}'\n")
        concat_file = f.name

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-c", "copy",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    os.unlink(concat_file)
    if result.returncode != 0:
        print(f"拼接错误: {result.stderr[-500:]}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="课件视频合成")
    parser.add_argument("--slides", required=True, help="幻灯片图片目录")
    parser.add_argument("--script", required=True, help="讲稿JSON文件路径")
    parser.add_argument("--output", required=True, help="输出视频路径(.mp4)")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural",
                        help="edge-tts 语音 (默认: zh-CN-XiaoxiaoNeural)")
    parser.add_argument("--resolution", default="1920x1080",
                        help="输出分辨率 (默认: 1920x1080)")
    parser.add_argument("--fade", type=float, default=0.5,
                        help="转场淡入淡出时长/秒 (默认: 0.5)")
    args = parser.parse_args()

    check_dependencies()

    # 加载幻灯片和讲稿
    images = get_slide_images(args.slides)
    with open(args.script, "r", encoding="utf-8") as f:
        script_data = json.load(f)

    print(f"共 {len(images)} 张幻灯片, {len(script_data)} 段讲稿")

    # 创建工作目录
    work_dir = tempfile.mkdtemp(prefix="courseware_video_")
    audio_dir = os.path.join(work_dir, "audio")
    seg_dir = os.path.join(work_dir, "segments")
    os.makedirs(audio_dir)
    os.makedirs(seg_dir)

    # 逐页合成
    segment_paths = []
    for entry in script_data:
        idx = entry["slide"] - 1  # 转为0-based
        if idx >= len(images):
            print(f"警告: 讲稿第{entry['slide']}页超出幻灯片数量，跳过", file=sys.stderr)
            continue

        narration = entry["narration"].strip()
        if not narration:
            print(f"第{entry['slide']}页讲稿为空，跳过")
            continue

        print(f"  [{entry['slide']}/{len(images)}] 合成语音...")
        audio_path = os.path.join(audio_dir, f"slide_{entry['slide']:03d}.mp3")
        asyncio.run(synthesize_speech(narration, audio_path, args.voice))

        print(f"  [{entry['slide']}/{len(images)}] 生成视频片段...")
        seg_path = os.path.join(seg_dir, f"seg_{entry['slide']:03d}.mp4")
        create_segment(images[idx], audio_path, seg_path, args.resolution, args.fade)
        segment_paths.append(seg_path)

    if not segment_paths:
        print("错误: 没有生成任何视频片段", file=sys.stderr)
        sys.exit(1)

    # 拼接最终视频
    print(f"拼接 {len(segment_paths)} 个片段...")
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    concatenate_segments(segment_paths, args.output)

    # 清理临时文件
    import shutil
    shutil.rmtree(work_dir, ignore_errors=True)

    duration = get_audio_duration(args.output)
    print(f"\n完成! 输出: {args.output}")
    print(f"时长: {int(duration // 60)}分{int(duration % 60)}秒")


if __name__ == "__main__":
    main()
