#!/usr/bin/env python3
"""Build a small synthetic 'lecture' (slides + TTS narration) for testing the pipeline
without network access. Needs ffmpeg, espeak-ng, Pillow.

Usage: make_test_video.py OUT.mp4 [--lang ko]
"""
from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SLIDES_KO = [
    ("린 스타트업 개론", "1강. 왜 가설 검증인가", "안녕하세요. 오늘은 린 스타트업의 핵심인 가설 검증에 대해 이야기하겠습니다. 대부분의 스타트업은 제품이 아니라 고객이 없어서 실패합니다."),
    ("고객 개발 4단계", "고객 발굴 → 고객 검증 → 고객 창출 → 회사 설립", "스티브 블랭크의 고객 개발 모델은 네 단계로 구성됩니다. 첫 단계인 고객 발굴에서는 문제 가설과 솔루션 가설을 세웁니다."),
    ("MVP의 정의", "최소 기능 제품: 학습을 위한 가장 작은 실험", "MVP는 완성품이 아닙니다. 학습을 극대화하면서 노력을 최소화하는 실험입니다. 랜딩 페이지, 컨시어지 MVP, 오즈의 마법사 방식이 대표적입니다."),
    ("만들기-측정-학습 루프", "Build → Measure → Learn, 핵심은 루프의 속도", "빌드 메저 런 루프에서 중요한 것은 각 반복의 속도입니다. 한 번의 루프가 짧을수록 더 많이 배웁니다. 다음 시간에는 지표 설계를 다루겠습니다."),
]


def render_slide(title: str, body: str, path: Path, idx: int) -> None:
    im = Image.new("RGB", (1280, 720), (245, 247, 250))
    d = ImageDraw.Draw(im)
    try:
        font_t = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf", 56)
        font_b = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothic.ttf", 36)
    except OSError:
        try:
            font_t = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 56)
            font_b = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 36)
        except OSError:
            font_t = font_b = ImageFont.load_default()
    d.rectangle([0, 0, 1280, 120], fill=(20, 60, 110))
    d.text((60, 30), title, font=font_t, fill="white")
    d.text((60, 220), body, font=font_b, fill=(30, 30, 30))
    d.text((1150, 670), f"{idx}/4", font=font_b, fill=(120, 120, 120))
    im.save(path)


SLIDES_EN = [
    ("Lean Startup Basics", "Lecture 1. Why hypothesis testing", "Hello everyone. Today we talk about the core of lean startup, hypothesis testing. Most startups fail not because they lack a product, but because they lack customers."),
    ("Customer Development", "Discovery, Validation, Creation, Company building", "Steve Blank's customer development model has four steps. In the first step, customer discovery, you write down your problem hypothesis and your solution hypothesis."),
    ("What is an MVP", "Minimum viable product: the smallest experiment for learning", "An MVP is not a finished product. It is an experiment that maximizes learning while minimizing effort. Landing pages, concierge MVPs and wizard of oz tests are typical examples."),
    ("Build Measure Learn", "The speed of the loop is what matters", "In the build measure learn loop, what matters is the speed of each iteration. The shorter one loop is, the more you learn. Next time we will cover metric design."),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--lang", default="ko")
    a = ap.parse_args()
    out = Path(a.out)
    slides = SLIDES_EN if a.lang.startswith("en") else SLIDES_KO
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        parts = []
        for i, (title, body, speech) in enumerate(slides, 1):
            png, wav, seg = td / f"s{i}.png", td / f"s{i}.wav", td / f"seg{i}.mp4"
            render_slide(title, body, png, i)
            subprocess.run(["espeak-ng", "-v", a.lang, "-s", "150", "-w", str(wav), speech], check=True)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(png), "-i", str(wav),
                            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-c:a", "aac",
                            "-shortest", "-r", "10", str(seg)], check=True)
            parts.append(seg)
        lst = td / "list.txt"
        lst.write_text("".join(f"file '{p}'\n" for p in parts))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                        "-c", "copy", str(out)], check=True)
    print(out)


if __name__ == "__main__":
    main()
