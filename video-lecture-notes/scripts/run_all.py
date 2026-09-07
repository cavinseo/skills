#!/usr/bin/env python3
"""One-shot pipeline: fetch -> transcribe -> keyframes -> merge.

Usage:
  run_all.py <url-or-file> --out WORKDIR [--model small] [--lang ko] [--engine auto|faster-whisper|sherpa] [--prefer-subs]
             [--audio-only] [--no-ocr] [--hash-dist 8] [--min-gap 4] [--max-frames 150]

Each step is idempotent-ish: pass --skip-existing to reuse artifacts already in WORKDIR
(handy when re-running after tuning keyframe parameters, or after fetching on another machine).
Prints the path to timeline.md at the end.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent


def step(script: str, *args: str) -> None:
    cmd = [sys.executable, str(HERE / script), *args]
    print("[vln] ==> " + " ".join(cmd), file=sys.stderr, flush=True)
    subprocess.run(cmd, check=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="small")
    ap.add_argument("--lang", default=None)
    ap.add_argument("--engine", default="auto", choices=["auto", "faster-whisper", "sherpa"])
    ap.add_argument("--prefer-subs", action="store_true")
    ap.add_argument("--audio-only", action="store_true")
    ap.add_argument("--no-ocr", action="store_true")
    ap.add_argument("--hash-dist", default="8")
    ap.add_argument("--min-gap", default="4")
    ap.add_argument("--max-frames", default="150")
    ap.add_argument("--skip-existing", action="store_true")
    a = ap.parse_args()
    wd = Path(a.out)

    if not (a.skip_existing and list(wd.glob("source.*"))):
        step("fetch.py", a.source, "--out", str(wd), *(["--audio-only"] if a.audio_only else []))
    if not (a.skip_existing and (wd / "transcript.json").exists()):
        args = ["--model", a.model, "--engine", a.engine]
        if a.lang:
            args += ["--lang", a.lang]
        if a.prefer_subs:
            args.append("--prefer-subs")
        step("transcribe.py", str(wd), *args)
    if not (a.skip_existing and (wd / "frames.json").exists()):
        args = ["--hash-dist", a.hash_dist, "--min-gap", a.min_gap, "--max-frames", a.max_frames]
        if a.no_ocr:
            args.append("--no-ocr")
        step("keyframes.py", str(wd), *args)
    step("merge.py", str(wd))


if __name__ == "__main__":
    main()
