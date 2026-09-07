#!/usr/bin/env python3
"""Check the environment for video-lecture-notes and report what will and won't work.
Usage: doctor.py   (exit code 0 even when things are missing — read the report)"""
from __future__ import annotations

import importlib
import shutil
import subprocess
import urllib.request


def can_reach(url: str, timeout: float = 4) -> bool:
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except Exception as e:  # noqa: BLE001
        return "403" not in str(e) and "Forbidden" not in str(e) and getattr(e, "code", None) is not None


def main() -> None:
    rows = []
    for b in ("ffmpeg", "ffprobe", "yt-dlp", "tesseract"):
        rows.append((b, "ok" if shutil.which(b) else "MISSING"))
    for m in ("faster_whisper", "sherpa_onnx", "imagehash", "PIL", "numpy"):
        try:
            importlib.import_module(m)
            rows.append((m, "ok"))
        except ImportError:
            rows.append((m, "MISSING"))
    if shutil.which("tesseract"):
        langs = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True).stdout
        rows.append(("tesseract kor", "ok" if "kor" in langs else "MISSING (apt install tesseract-ocr-kor)"))
    rows.append(("youtube.com reachable", "yes" if can_reach("https://www.youtube.com") else "NO -> fetch on user's machine / attach file"))
    rows.append(("huggingface.co reachable", "yes (faster-whisper)" if can_reach("https://huggingface.co") else "NO -> sherpa-onnx engine (GitHub models)"))
    try:
        import ctranslate2
        rows.append(("CUDA GPUs", str(ctranslate2.get_cuda_device_count())))
    except Exception:
        rows.append(("CUDA GPUs", "0"))
    w = max(len(r[0]) for r in rows)
    for k, v in rows:
        print(f"{k.ljust(w)}  {v}")


if __name__ == "__main__":
    main()
