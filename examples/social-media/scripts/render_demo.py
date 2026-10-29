#!/usr/bin/env python3
"""Render the social-media demonstration with a procedurally generated soundtrack."""

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = Path(__file__).resolve().parent
ASSETS = SCRIPT_DIR.parent
ROOT = ASSETS.parents[1]


def main():
    """Render the demonstration or save a preview contact sheet."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ASSETS / "demo.mp4")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--font", default=os.environ.get("DEMO_FONT"))
    parser.add_argument("--font-index", type=int, default=3)
    args = parser.parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = (
        tempfile.TemporaryDirectory(prefix="pet-demo-")
        if args.work_dir is None
        else None
    )
    out = (args.work_dir or Path(temporary.name)).resolve()
    out.mkdir(parents=True, exist_ok=True)
    font = args.font
    if not font:
        candidates = list(
            Path("/System/Library/AssetsV2/com_apple_MobileAsset_Font8").glob(
                "*/AssetData/PingFang.ttc"
            )
        )
        if not candidates:
            parser.error(
                "Supply --font with a Chinese font file (and --font-index for its face)."
            )
        font = str(candidates[0])
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg and not args.preview:
        parser.error("ffmpeg must be installed and available on PATH")
    width, height = 1080, 1920
    ink = "#243c59"
    muted = "#71859b"
    purple = "#4d78a4"
    card = "#f3f7fb"
    fonts = {
        n: ImageFont.truetype(font, n, index=args.font_index)
        for n in [24, 28, 30, 32, 36, 42, 48, 64, 76, 86]
    }
    checked_glyphs = set()

    def text(im, xy, s, n=36, c=ink, anchor="mm"):
        for ch in s:
            if not ch.isspace() and ch not in checked_glyphs:
                assert (
                    fonts[42].getmask(ch).getbbox() is not None
                ), f"Missing visible glyph: {ch}"
                checked_glyphs.add(ch)
        ImageDraw.Draw(im).text(xy, s, font=fonts[n], fill=c, anchor=anchor)

    def base(chapter):
        im = Image.new("RGB", (width, height), "#edf3f9")
        d = ImageDraw.Draw(im)
        d.ellipse((-250, -210, 480, 520), fill="#dce9f6")
        d.ellipse((850, 1400, 1310, 2020), fill="#dce9f6")
        text(im, (100, 150), "JAEHYUN NEXT DOOR", 32, purple, "lm")
        text(im, (980, 150), chapter, 28, muted, "rm")
        d.line((100, 207, 980, 207), fill="#c6d8e9", width=2)
        text(im, (540, 1740), "隔壁的宰铉 · 非官方 Codex 桌宠", 28, muted)
        return im

    serial = 0
    timeline = []
    samples = []
    manifest = []

    def save(im, duration):
        nonlocal serial
        p = out / f"frame-{serial:04d}.png"
        im.save(p)
        serial += 1
        return (p, duration)

    def add(seq, loops, title):
        start = sum(t for p, t in timeline)
        timeline.extend(seq * loops)
        manifest.append(
            {
                "title": title,
                "start": round(start, 3),
                "duration": round(sum(t for p, t in seq) * loops, 3),
            }
        )
        samples.append(seq[0][0])

    def paste_pet(im, pet, x=252, y=640):
        sprite = pet.convert("RGBA").resize((576, 624), Image.Resampling.LANCZOS)
        im.paste(sprite, (x, y), sprite)

    def panel(im):
        ImageDraw.Draw(im).rounded_rectangle((90, 570, 990, 1325), radius=60, fill=card)

    atlas = Image.open(ROOT / "spritesheet.webp").convert("RGBA")
    animations = json.loads(
        (ROOT / "examples/animations.json").read_text(encoding="utf-8")
    )

    def atlas_cell(row, col):
        return atlas.crop((col * 192, row * 208, (col + 1) * 192, (row + 1) * 208))

    def look_cell(i):
        return atlas_cell(9 + i // 8, i % 8)

    def gif_frames(name):
        # Use unquantized RGBA atlas cells, not palette GIF previews.
        if name == "look-around.gif":
            return [
                (look_cell(i), animations[-1]["preview_duration_ms"] / 1000)
                for i in range(16)
            ]
        a = next(a for a in animations if a["gif"] == name)
        return [
            (atlas_cell(a["row"], i), dur / 1000)
            for i, dur in enumerate(a["durations_ms"])
        ]

    seq = []
    for pet, dur in gif_frames("waving.gif"):
        im = base("完整动作图鉴")
        text(im, (540, 340), "让宰铉来桌面串门", 76)
        text(im, (540, 452), "九种动画 · 十六个视线方向", 36, muted)
        panel(im)
        paste_pet(im, pet)
        text(im, (540, 1450), "明明：开工啦，今天也陪着你～", 42)
        text(im, (540, 1535), "Jaehyun Next Door  /  Codex pet", 30, muted)
        seq.append(save(im, dur))
    add(seq, 4, "开场")
    data = json.loads((ROOT / "examples/animations.json").read_text(encoding="utf-8"))
    labels = [
        ("安静陪伴", "轻轻眨眼，静静呼吸"),
        ("向右走走", "迈着小步向右走"),
        ("向左走走", "换个方向，继续陪你"),
        ("向你挥手", "挥挥手，想让你注意到我"),
        ("开心跳跃", "蹲下、跃起，再轻轻落地"),
        ("有点不好意思", "悄悄低下头，再慢慢恢复"),
        ("歪头等你", "歪歪头，等着你的回应"),
        ("麦克风彩排", "拿起麦克风，跟着节奏动一动"),
        ("认真想一想", "托着下巴，轻轻点头"),
    ]
    for i, (a, (title, desc)) in enumerate(zip(data, labels)):
        seq = []
        for pet, dur in gif_frames(a["gif"]):
            im = base(f"{i+1:02d} / 09")
            text(im, (540, 350), title, 86)
            text(im, (540, 454), a["title"].upper(), 30, muted)
            panel(im)
            paste_pet(im, pet)
            text(im, (540, 1445), desc, 42)
            text(im, (540, 1530), "Jaehyun Next Door  /  Codex pet", 30, muted)
            d = ImageDraw.Draw(im)
            for j in range(9):
                x = 352 + j * 47
                d.rounded_rectangle(
                    (x, 1615, x + 30, 1621),
                    radius=3,
                    fill=purple if i == j else "#d2dfec",
                )
            seq.append(save(im, dur))
        add(seq, [3, 3, 3, 5, 4, 3, 4, 4, 4][i], title)
    seq = []
    for pet, dur in gif_frames("look-around.gif"):
        im = base("视线方向 / 01")
        text(im, (540, 350), "十六种小眼神", 86)
        text(im, (540, 455), "十六个方向 · 顺时针完整预览", 36, muted)
        panel(im)
        paste_pet(im, pet)
        text(im, (540, 1445), "十六个视线方向，一次看全", 42)
        text(im, (540, 1535), "此处为轮播演示；实际触发由应用控制", 30, muted)
        seq.append(save(im, dur))
    add(seq, 2, "十六方向顺时针轮播")
    seq = []
    for i in range(16):
        im = base("视线方向 / 02")
        text(im, (540, 350), "每个方向，都有回应", 64)
        text(im, (540, 454), f"{i+1:02d} / 16  ·  {i*22.5:g}°", 36, muted)
        panel(im)
        paste_pet(im, look_cell(i))
        d = ImageDraw.Draw(im)
        for j in range(16):
            theta = j * math.pi / 8
            x = 540 + 342 * math.sin(theta)
            y = 950 - 342 * math.cos(theta)
            r = 12 if j == i else 5
            d.ellipse(
                (x - r, y - r, x + r, y + r), fill=purple if j == i else "#d2dfec"
            )
        direction = (
            "正上方"
            if i == 0
            else (
                "右上方"
                if i < 4
                else (
                    "正右方"
                    if i == 4
                    else (
                        "右下方"
                        if i < 8
                        else (
                            "正下方"
                            if i == 8
                            else (
                                "左下方"
                                if i < 12
                                else "正左方" if i == 12 else "左上方"
                            )
                        )
                    )
                )
            )
        )
        text(im, (540, 1445), direction, 48)
        text(im, (540, 1535), "从正上方开始，顺时针逐一展示", 30, muted)
        seq.append(save(im, 0.6))
    add(seq, 1, "十六方向逐一展示")
    # Trigger summary based on the locally inspected app overlay implementation.
    im = base("互动小贴士")
    text(im, (540, 340), "小动作触发指南", 76)
    text(im, (540, 435), "互动小贴士 · 可暂停查看", 36, muted)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((85, 510, 995, 1495), radius=38, fill=card)
    text(im, (130, 564), "小动作", 32, purple, "lm")
    text(im, (410, 564), "什么时候会出现", 32, purple, "lm")
    d.line((125, 610, 955, 610), fill="#c6d8e9", width=2)
    rows = [
        ("安静陪伴", "没有活动提醒时"),
        ("左右走动", "按住桌宠，向左或向右拖动"),
        ("开心跳跃", "鼠标悬停在桌宠上"),
        ("向你挥手", "应用触发初次唤醒提醒时"),
        ("麦克风彩排", "活动提醒显示任务进行中"),
        ("歪头等你", "活动提醒显示需要输入时"),
        ("有点不好意思", "活动提醒显示失败或受阻时"),
        ("认真想一想", "活动提醒显示任务完成时"),
        ("视线方向", "快捷聊天输入光标，或"),
    ]
    for i, (name, trigger) in enumerate(rows):
        y = 660 + i * 86
        text(im, (130, y), name, 30, ink, "lm")
        text(im, (410, y), trigger, 30, ink, "lm")
        if i < 8:
            d.line((125, y + 43, 955, y + 43), fill="#dce6f0", width=1)
    text(im, (410, 1392), "Computer Use 的操作光标", 28, ink, "lm")
    text(im, (540, 1555), "普通鼠标移动不会让他轮播全部视线", 30, muted)
    text(im, (540, 1615), "按当前安装版本整理，实际表现以应用为准", 28, muted)
    add([save(im, 7)], 1, "动画触发指南")
    seq = []
    for pet, dur in gif_frames("waving.gif"):
        im = base("JAEHYUN NEXT DOOR")
        text(im, (540, 350), "把陪伴留在桌面", 76)
        text(im, (540, 454), "九种动画 + 十六个视线方向", 36, muted)
        panel(im)
        paste_pet(im, pet)
        text(im, (540, 1445), "Jaehyun Next Door", 48)
        text(im, (540, 1535), "工作的时候，也有一点小陪伴", 36, muted)
        seq.append(save(im, dur))
    add(seq, 4, "结尾")
    # Preserve source frame durations before sampling the combined timeline at 30 fps.
    (out / "manifest.json").write_text(
        json.dumps(
            {
                "width": width,
                "height": height,
                "fps": 30,
                "duration": math.ceil(sum(t for _, t in timeline) * 30) / 30,
                "source_timeline_duration": round(sum(t for _, t in timeline), 3),
                "chapters": manifest,
                "source": "examples/index.html, animations.json and original RGBA spritesheet.webp (alpha composited before encoding)",
                "audio": "Original instrumental soundtrack generated by compose_demo_music.py",
                "timing": "Original source durations; sampled to 30 fps, within one output frame.",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    preview = Image.new("RGB", (270 * 4, 480 * 4), "white")
    for i, p in enumerate(samples):
        im = Image.open(p)
        im.thumbnail((270, 480))
        preview.paste(im, ((i % 4) * 270, (i // 4) * 480))
    preview.save(out / "review.jpg")
    # Keep the existing social-media cover.
    print(json.dumps(manifest, ensure_ascii=False), flush=True)
    if args.preview:
        preview_output = output.with_suffix(".jpg")
        if preview_output != out / "review.jpg":
            shutil.copyfile(out / "review.jpg", preview_output)
        return
    # Sample the exact timeline once at the final frame rate. This avoids accumulating
    # per-image timestamp rounding in the concat demuxer.
    fps = 30
    duration = sum(t for _, t in timeline)
    assert abs(duration - 59.58) < 1e-8, f"Unexpected timeline: {duration}"
    proc = subprocess.Popen(
        [
            ffmpeg,
            "-y",
            "-v",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            "1080x1920",
            "-r",
            str(fps),
            "-i",
            "-",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(out / "Jaehyun-Next-Door_全动画展示_竖屏.mp4"),
        ],
        stdin=subprocess.PIPE,
    )
    idx = 0
    end = timeline[0][1]
    last = None
    pixels = None
    for n in range(math.ceil(duration * fps)):
        t = n / fps
        while t >= end - 1e-9 and idx < len(timeline) - 1:
            idx += 1
            end += timeline[idx][1]
        p = timeline[idx][0]
        if p != last:
            pixels = Image.open(p).convert("RGB").tobytes()
            last = p
        proc.stdin.write(pixels)
    proc.stdin.close()
    returncode = proc.wait()
    if returncode:
        raise subprocess.CalledProcessError(returncode, proc.args)

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_DIR / "compose_demo_music.py"),
            str(out),
        ],
        check=True,
    )
    soundtrack = out / "隔壁的宰铉-original.wav"
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-v",
            "error",
            "-i",
            str(out / "Jaehyun-Next-Door_全动画展示_竖屏.mp4"),
            "-i",
            str(soundtrack),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(output),
        ],
        check=True,
    )
    metadata = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    metadata["audio_provenance"] = json.loads(
        (out / "music-provenance.json").read_text(encoding="utf-8")
    )
    (out / "manifest.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Rendered {output}")


if __name__ == "__main__":
    main()
