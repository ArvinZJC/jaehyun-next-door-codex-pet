#!/usr/bin/env python3
"""Build the Jaehyun desktop-radio demonstration from the edited recording and pet artwork."""

import argparse
from contextlib import ExitStack
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ASSETS = Path(__file__).resolve().parents[1]
ROOT = ASSETS.parents[1]
WIDTH, HEIGHT, FPS = 1080, 1920, 30
INTRO_DURATION = 7.0
MUSIC_START = 4
SCENES = [
    ("tune", 5.0, "接通陪伴"),
    ("walk", 6.0, "跟着你走"),
    ("work", 8.0, "状态播报"),
    ("look", 8.0, "视线调频"),
    ("guide", 7.0, "互动指南"),
    ("end", 4.0, "陪伴持续在线"),
]
DURATION = INTRO_DURATION + sum(duration for _, duration, _ in SCENES)
INK, MUTED, YELLOW = "#f5f1e5", "#a8becd", "#f6cf62"


def run(command):
    """Run an encoder command and propagate failures."""
    subprocess.run(command, check=True)


class RadioStation:
    """Compose broadcast-style layouts using the original transparent sprites."""

    def __init__(self, font_path, font_index):
        self.fonts = {
            size: ImageFont.truetype(font_path, size, index=font_index)
            for size in (24, 26, 28, 30, 32, 36, 40, 44, 48, 56, 64, 72, 84, 100)
        }
        self.animations = json.loads(
            (ROOT / "examples/animations.json").read_text(encoding="utf-8")
        )
        with Image.open(ROOT / "spritesheet.webp") as source:
            self.atlas = source.convert("RGBA")
        self.sprites = {}
        gradient = np.linspace(0, 1, HEIGHT)[:, None, None]
        colour = np.array([16, 34, 54]) + gradient * np.array([9, 12, 14])
        self.background = Image.fromarray(
            np.repeat(colour, WIDTH, axis=1).astype("uint8")
        )
        self.layouts = {}

    def text(self, im, xy, value, size=36, colour=INK, anchor="mm"):
        ImageDraw.Draw(im).text(
            xy, value, font=self.fonts[size], fill=colour, anchor=anchor
        )

    def base(self, section, title, subtitle):
        im = self.background.copy()
        d = ImageDraw.Draw(im)
        d.ellipse((65, 90, 85, 110), fill=YELLOW)
        self.text(im, (105, 100), "JAEHYUN NEXT DOOR", 30, YELLOW, "lm")
        self.text(im, (1000, 100), section, 26, MUTED, "rm")
        self.text(im, (72, 235), title, 64, INK, "lm")
        self.text(im, (75, 340), subtitle, 30, MUTED, "lm")
        d.line((75, 1720, 1005, 1720), fill="#36516a", width=2)
        self.text(im, (1005, 1790), "隔壁的宰铉 · 非官方 Codex 桌宠", 26, MUTED, "rm")
        return im

    def sprite(self, row, col, size):
        key = row, col, size
        if key not in self.sprites:
            self.sprites[key] = self.atlas.crop(
                (col * 192, row * 208, (col + 1) * 192, (row + 1) * 208)
            ).resize(size, Image.Resampling.LANCZOS)
        return self.sprites[key]

    def pose(self, row, time):
        durations = self.animations[row]["durations_ms"]
        elapsed = (time * 1000) % sum(durations)
        for col, duration in enumerate(durations):
            elapsed -= duration
            if elapsed < 0:
                return col
        return len(durations) - 1

    def pet(self, im, row, col, xy, size):
        sprite = self.sprite(row, col, size)
        im.paste(sprite, xy, sprite)

    def dial(self, im):
        d = ImageDraw.Draw(im)
        d.ellipse((165, 575, 915, 1325), fill="#24435b", outline="#486477", width=3)
        d.ellipse((195, 605, 885, 1295), outline="#36566d", width=2)
        d.ellipse((240, 650, 840, 1250), fill="#31546b")
        for i in range(48):
            a = i * math.tau / 48
            radius = 390
            x, y = 540 + radius * math.sin(a), 950 - radius * math.cos(a)
            d.line(
                (x, y, x + 12 * math.sin(a), y - 12 * math.cos(a)),
                fill="#688298",
                width=2,
            )

    def layout(self, scene):
        if scene in self.layouts:
            return self.layouts[scene].copy()
        if scene == "tune":
            im = self.base(
                "01 / 接通陪伴", "隔壁的宰铉，已上线", "安静待着，也会热情回应。"
            )
            self.dial(im)
        elif scene == "walk":
            im = self.base(
                "02 / 跟着你走", "换个位置，继续陪你", "按住桌宠，向左或向右拖动。"
            )
            d = ImageDraw.Draw(im)
            d.rectangle((0, 1090, WIDTH, 1220), fill="#2c485e")
            for x in range(30, WIDTH, 100):
                d.line((x, 1150, x + 52, 1150), fill="#638096", width=4)
            d.polygon([(100, 1100), (145, 1070), (145, 1130)], fill=YELLOW)
            d.polygon([(980, 1100), (935, 1070), (935, 1130)], fill=YELLOW)
        elif scene == "work":
            im = self.base(
                "03 / 状态播报", "你的进度，他都在意", "不同的任务状态，不同的小回应。"
            )
            self.dial(im)
        elif scene == "look":
            im = self.base(
                "04 / 视线调频",
                "十六个方向，逐一接通",
                "顺时针逐一展示 · 实际视线由应用控制",
            )
            d = ImageDraw.Draw(im)
            d.ellipse((200, 590, 880, 1270), fill="#28495f", outline="#48677c", width=3)
            self.text(im, (540, 1560), "每一个方向，都认真看向你。", 30, MUTED)
        elif scene == "guide":
            im = self.base(
                "便签 / 互动指南",
                "这些信号，他会回应",
                "可暂停阅读 · 2026 年 9 月版本行为参考",
            )
            rows = [
                ("悬停", "开心跳跃"),
                ("向左 / 右拖动", "左右走动"),
                ("初次唤醒提醒", "向你挥手"),
                ("任务进行中", "麦克风彩排"),
                ("需要输入", "歪头等你"),
                ("失败或受阻", "有点不好意思"),
                ("任务完成", "认真想一想"),
                ("没有活动提醒", "安静陪伴"),
            ]
            d = ImageDraw.Draw(im)
            for i, (trigger, reaction) in enumerate(rows):
                x, y = 75 + (i % 2) * 490, 495 + (i // 2) * 240
                d.line((x, y, x + 405, y), fill="#527087", width=2)
                self.text(im, (x, y + 54), f"{i+1:02d} / {trigger}", 28, MUTED, "lm")
                self.text(im, (x, y + 128), reaction, 40, YELLOW, "lm")
            self.text(im, (75, 1530), "视线：快捷聊天输入光标，或", 30, INK, "lm")
            self.text(
                im, (75, 1580), "Computer Use 操作光标；不是普通鼠标。", 30, INK, "lm"
            )
            self.text(im, (75, 1650), "实际表现以你安装的应用版本为准", 26, MUTED, "lm")
        else:
            im = self.base(
                "陪伴 / 持续在线",
                "今天，也有宰铉陪着你",
                "不抢你的注意，只添一点热闹。",
            )
            self.dial(im)
            self.text(im, (540, 1460), "九种动画 · 十六个视线方向", 36, YELLOW)
            self.text(im, (540, 1560), "隔壁的宰铉，随时来串门。", 32, INK)
        self.layouts[scene] = im
        return im.copy()

    def signal(self, im, time, label, number, total):
        d = ImageDraw.Draw(im)
        self.text(im, (540, 1400), label, 48, YELLOW)
        for i in range(total):
            x = 540 + (i - (total - 1) / 2) * 160
            d.rounded_rectangle(
                (x - 55, 1490, x + 55, 1497),
                radius=3,
                fill=YELLOW if i == number else "#3b586d",
            )
        for i in range(29):
            height = 10 + int(30 * (0.5 + 0.5 * math.sin(time * 4 + i * 0.65)))
            x = 260 + i * 20
            d.line((x, 1605 - height, x, 1605 + height), fill="#6d879b", width=6)

    def frame(self, scene, time):
        im = self.layout(scene)
        if scene == "tune":
            index = 0 if time < 1.8 else 1 if time < 3.4 else 2
            row = [0, 3, 4][index]
            local = time - [0, 1.8, 3.4][index]
            self.pet(im, row, self.pose(row, local), (252, 620), (576, 624))
            self.signal(im, time, ["安静陪伴", "向你挥手", "开心跳跃"][index], index, 3)
        elif scene == "walk":
            index = 0 if time < 3 else 1
            progress = (time % 3) / 3
            x = int(570 - 490 * progress) if index == 0 else int(80 + 490 * progress)
            row = 2 if index == 0 else 1
            self.pet(im, row, self.pose(row, time % 3), (x, 635), (432, 468))
            self.signal(im, time, ["向左走走", "向右走走"][index], index, 2)
        elif scene == "work":
            index = min(int(time / 2), 3)
            row = [7, 6, 5, 8][index]
            self.pet(im, row, self.pose(row, time % 2), (252, 620), (576, 624))
            self.signal(
                im,
                time,
                ["麦克风彩排", "歪头等你", "有点不好意思", "认真想一想"][index],
                index,
                4,
            )
        elif scene == "look":
            index = min(int(time * 2), 15)
            self.pet(im, 9 + index // 8, index % 8, (300, 670), (480, 520))
            d = ImageDraw.Draw(im)
            for i in range(16):
                angle = i * math.tau / 16
                x, y = 540 + 410 * math.sin(angle), 930 - 410 * math.cos(angle)
                d.ellipse(
                    (x - 25, y - 25, x + 25, y + 25),
                    fill=YELLOW if i == index else "#36586e",
                )
                self.text(
                    im, (x, y), f"{i+1:02d}", 24, "#12273d" if i == index else INK
                )
            self.text(
                im,
                (540, 1440),
                f"{index+1:02d} / 16    ·    {index*22.5:g}°",
                40,
                YELLOW,
            )
        elif scene == "end":
            self.pet(im, 3, self.pose(3, time), (252, 620), (576, 624))
        return im


def encode_body(book, ffmpeg, out):
    command = [
        ffmpeg,
        "-y",
        "-v",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{WIDTH}x{HEIGHT}",
        "-r",
        str(FPS),
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
        "-video_track_timescale",
        "15360",
        str(out / "body.mp4"),
    ]
    with subprocess.Popen(command, stdin=subprocess.PIPE) as proc:
        try:
            for scene, duration, _ in SCENES:
                for n in range(round(duration * FPS)):
                    proc.stdin.write(book.frame(scene, n / FPS).tobytes())
        finally:
            proc.stdin.close()
        result = proc.wait()
        if result:
            raise subprocess.CalledProcessError(result, command)


def render(args, out, ffmpeg):
    book = RadioStation(args.font, args.font_index)
    intro = out / "screen-recording-edited.mp4"
    source = ASSETS / "screen-recording-edited.mp4"
    if intro != source:
        shutil.copyfile(source, intro)
    run(
        [
            ffmpeg,
            "-y",
            "-v",
            "error",
            "-ss",
            "1",
            "-i",
            str(intro),
            "-frames:v",
            "1",
            str(out / "intro.png"),
        ]
    )
    with Image.open(out / "intro.png") as source:
        previews = [source.convert("RGB")]
    previews.extend(book.frame(scene, 1) for scene, _, _ in SCENES)
    sheet = Image.new("RGB", (270 * 4, 480 * 2), "#102236")
    for i, frame in enumerate(previews):
        sheet.paste(
            frame.resize((270, 480), Image.Resampling.LANCZOS),
            ((i % 4) * 270, (i // 4) * 480),
        )
    sheet.save(out / "review.jpg", quality=95)
    chapters = [{"title": "桌面实录", "start": 0, "duration": INTRO_DURATION}]
    at = INTRO_DURATION
    for _, duration, title in SCENES:
        chapters.append({"title": title, "start": round(at, 3), "duration": duration})
        at += duration
    (out / "manifest.json").write_text(
        json.dumps(
            {
                "width": WIDTH,
                "height": HEIGHT,
                "fps": FPS,
                "duration": DURATION,
                "chapters": chapters,
                "music": {
                    "title": "Fig Leaf Rag",
                    "artist": "Kevin MacLeod",
                    "licence": "CC BY 4.0",
                    "start": MUSIC_START,
                    "duration": DURATION,
                },
                "recording": {
                    "source": "screen-recording-edited.mp4",
                    "duration": INTRO_DURATION,
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    if args.preview:
        target = args.output.with_suffix(".jpg")
        if target != out / "review.jpg":
            shutil.copyfile(out / "review.jpg", target)
        return
    encode_body(book, ffmpeg, out)
    (out / "segments.txt").write_text(
        "file 'screen-recording-edited.mp4'\nfile 'body.mp4'\n", encoding="utf-8"
    )
    final = out / "final.mp4"
    run(
        [
            ffmpeg,
            "-y",
            "-v",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(out / "segments.txt"),
            "-ss",
            str(MUSIC_START),
            "-i",
            str(ASSETS / "fig-leaf-rag.mp3"),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-af",
            f"atrim=duration={DURATION},asetpts=PTS-STARTPTS,volume=0.75,afade=t=in:d=0.7,afade=t=out:st={DURATION-2.5}:d=2.5",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-t",
            str(DURATION),
            "-movflags",
            "+faststart",
            str(final),
        ]
    )
    if final != args.output:
        shutil.copyfile(final, args.output)
    print(f"Rendered {args.output} ({DURATION:g} seconds)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ASSETS / "demo.mp4")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--font", default=os.environ.get("DEMO_FONT"))
    parser.add_argument("--font-index", type=int, default=3)
    args = parser.parse_args()
    if not args.font:
        fonts = sorted(
            Path("/System/Library/AssetsV2/com_apple_MobileAsset_Font8").glob(
                "*/AssetData/PingFang.ttc"
            )
        )
        if not fonts:
            parser.error(
                "Supply --font with a Chinese font file and --font-index for its face."
            )
        args.font = str(fonts[0])
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        parser.error("ffmpeg must be installed and available on PATH")
    args.output = args.output.resolve()
    if not args.preview and args.output in {
        (ASSETS / "screen-recording-edited.mp4").resolve(),
        (ASSETS / "fig-leaf-rag.mp3").resolve(),
    }:
        parser.error("--output must not overwrite a source recording")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with ExitStack() as stack:
        out = (
            args.work_dir.resolve()
            if args.work_dir
            else Path(
                stack.enter_context(tempfile.TemporaryDirectory(prefix="jaehyun-demo-"))
            )
        )
        out.mkdir(parents=True, exist_ok=True)
        render(args, out, ffmpeg)


if __name__ == "__main__":
    main()
