#!/usr/bin/env python3
"""Recovered synthesiser; pad and bass settings reconstructed from archive gap."""

import argparse
import json
import wave
from pathlib import Path

import numpy as np


def compose(output_dir):
    """Synthesise the instrumental score in the requested directory."""
    OUT = Path(output_dir)
    OUT.mkdir(parents=True, exist_ok=True)
    SR = 48000
    duration = 59.6
    bpm = 100
    beat = 60 / bpm
    mix = np.zeros((round(SR * duration), 2), np.float64)
    rng = np.random.default_rng(925)

    def note(midi, start, length, volume=0.08, pan=0, kind="pluck"):
        n = round((length + 1.1) * SR)
        t = np.arange(n) / SR
        freq = 440 * 2 ** ((midi - 69) / 12)
        if kind == "pluck":
            env = (1 - np.exp(-t / 0.007)) * np.exp(-t / (0.45 + length * 0.42))
            sig = sum(
                a * np.sin(2 * np.pi * freq * h * t) * np.exp(-t * 0.3 * h)
                for h, a in [(1, 1), (2, 0.23), (3, 0.085), (4, 0.018)]
            )
        elif kind == "pad":
            env = np.minimum(t / 0.3, 1) * np.minimum(
                np.maximum(length + 0.8 - t, 0) / 0.8, 1
            )
            sig = (
                np.sin(2 * np.pi * freq * t)
                + 0.18 * np.sin(2 * np.pi * freq * 1.0015 * t)
            ) * 0.7
        else:
            env = (1 - np.exp(-t / 0.022)) * np.exp(-t / 0.85)
            sig = np.sin(2 * np.pi * freq * t) + 0.13 * np.sin(4 * np.pi * freq * t)
        env *= np.minimum(np.maximum(length + 1.1 - t, 0) / 0.1, 1)
        sig *= env * volume
        at = round(start * SR)
        end = min(at + n, len(mix))
        if end <= at:
            return
        sig = sig[: end - at]
        mix[at:end, 0] += sig * np.sqrt((1 - pan) / 2)
        mix[at:end, 1] += sig * np.sqrt((1 + pan) / 2)

    # Newly written F-major score. Synthesized oscillators only; no external recordings.
    chords = [
        ([60, 65, 69, 72], 41),
        ([60, 64, 65, 69], 38),
        ([58, 62, 65, 69], 34),
        ([60, 62, 67, 72], 36),
        ([60, 65, 69, 74], 41),
        ([60, 64, 67, 69], 38),
        ([58, 62, 65, 72], 34),
        ([60, 64, 67, 74], 36),
    ]
    melody = [
        [(0, 69, 0.5), (0.75, 72, 0.5), (1.5, 77, 1), (3, 76, 0.5)],
        [(0.25, 74, 0.75), (1.5, 72, 0.5), (2.5, 69, 1)],
        [(0, 70, 0.5), (1, 74, 0.5), (1.75, 77, 0.75), (3, 74, 0.5)],
        [(0.5, 76, 1), (2, 74, 0.5), (3, 72, 0.5)],
        [(0, 77, 0.75), (1.25, 79, 0.5), (2, 81, 0.75), (3.25, 77, 0.5)],
        [(0.5, 76, 0.5), (1.5, 74, 0.5), (2.5, 72, 1)],
        [(0, 74, 0.75), (1.25, 77, 0.5), (2, 74, 0.5), (3, 70, 0.5)],
        [(0, 72, 0.75), (1.5, 76, 0.5), (2.5, 74, 0.5), (3.25, 72, 0.5)],
    ]
    for bar in range(24):
        start = 0.25 + bar * 4 * beat
        ch, bass = chords[bar % 8]
        if bar == 23:
            ch, bass = [60, 65, 69, 72], 41
        # Lighten the arrangement during the readable trigger table.
        gain = 0.75 if 49.5 <= start < 56.8 else 1
        for k, m in enumerate(ch):
            note(m, start, 2.1, 0.02 * gain, (k - 1.5) * 0.3, "pad")
        note(bass, start, 1.6, 0.10 * gain, 0, "bass")
        if bar < 23:
            note(bass + 12, start + 2 * beat, 0.7, 0.045 * gain, 0, "bass")
        for j, k in enumerate([0, 2, 1, 3, 1, 2, 0, 3]):
            if bar == 23 and j > 3:
                break
            note(
                ch[k] + 12,
                start + j * 0.5 * beat,
                0.35,
                0.027 * gain,
                0.32 if j % 2 else -0.32,
            )
        phrase = melody[bar % 8]
        if bar == 22:
            phrase = [(0, 74, 0.75), (1.25, 72, 0.5), (2, 76, 1)]
        if bar == 23:
            phrase = [(0, 77, 2.1)]
        for off, m, length in phrase:
            note(m, start + off * beat, length * beat, 0.08 * gain, -0.08)
        # Very soft synthesized shaker; no sampled percussion.
        if bar < 22:
            for j in range(8):
                at = round((start + j * 0.5 * beat) * SR)
                n = round(0.055 * SR)
                noise = rng.normal(0, 1, n)
                noise = np.concatenate(([0], np.diff(noise)))
                noise *= np.exp(-np.arange(n) / (SR * 0.013)) * 0.0025
                mix[at : at + n, 0] += noise
                mix[at : at + n, 1] += noise * 0.85
    base = mix.copy()
    for delay, gain in [(0.071, 0.12), (0.143, 0.08), (0.261, 0.035)]:
        n = round(delay * SR)
        mix[n:] += base[:-n, ::-1] * gain
    fade = np.ones(len(mix))
    n = round(0.7 * SR)
    fade[:n] = np.linspace(0, 1, n)
    n = round(2.1 * SR)
    fade[-n:] = np.linspace(1, 0, n)
    mix *= fade[:, None]
    rms = np.sqrt(np.mean(mix**2))
    mix *= min(0.095 / rms, 0.7 / np.max(np.abs(mix)))
    with wave.open(str(OUT / "隔壁的宰铉-original.wav"), "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes((mix * 32767).astype("<i2").tobytes())
    provenance = {
        "title": "隔壁的宰铉 · 桌面小步舞",
        "type": "New original instrumental composition and procedural synthesis",
        "tempo_bpm": bpm,
        "key": "F major",
        "duration_seconds": duration,
        "samples": "None; oscillators and synthesized noise only",
        "artist_music": "No Jaehyun or BOYNEXTDOOR recordings or melodies used",
        "sample_rate": SR,
        "peak_dbfs": float(20 * np.log10(np.max(np.abs(mix)))),
        "rms_dbfs": float(20 * np.log10(np.sqrt(np.mean(mix**2)))),
    }
    (OUT / "music-provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(provenance, ensure_ascii=False))


def main():
    """Generate the instrumental score used by the demonstration video."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    compose(args.output_dir)


if __name__ == "__main__":
    main()
