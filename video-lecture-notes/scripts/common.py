"""Shared helpers for the video-lecture-notes pipeline."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def log(msg: str) -> None:
    print(f"[vln] {msg}", file=sys.stderr, flush=True)


def die(msg: str, code: int = 1) -> None:
    log(f"ERROR: {msg}")
    sys.exit(code)


def need(binary: str, hint: str = "") -> str:
    path = shutil.which(binary)
    if not path:
        die(f"'{binary}' not found on PATH. {hint}")
    return path


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    log("$ " + " ".join(str(c) for c in cmd))
    return subprocess.run(cmd, check=True, text=True, **kw)


def hms(seconds: float, with_ms: bool = False) -> str:
    seconds = max(0.0, float(seconds))
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    base = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
    if with_ms:
        base += f".{int(round((seconds % 1) * 1000)):03d}"
    return base


def srt_time(seconds: float) -> str:
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    ms = int(round((seconds % 1) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def read_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def ffprobe_duration(media: Path) -> float:
    need("ffprobe", "Install ffmpeg (apt install ffmpeg / brew install ffmpeg / winget install ffmpeg).")
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(media)],
        capture_output=True, text=True, check=True).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return 0.0


YOUTUBE_RE = re.compile(r"(youtube\.com|youtu\.be)", re.I)
URL_RE = re.compile(r"^https?://", re.I)


def is_url(s: str) -> bool:
    return bool(URL_RE.match(s))


def safe_slug(s: str, maxlen: int = 60) -> str:
    s = re.sub(r"[^\w\-가-힣]+", "-", s, flags=re.U).strip("-")
    return s[:maxlen] or "video"


def find_source(workdir: Path) -> Path | None:
    """Return the media file the pipeline should use (video preferred over audio)."""
    for name in ("source.mp4", "source.mkv", "source.webm", "source.mov", "source.m4a", "source.mp3", "source.wav"):
        p = workdir / name
        if p.exists():
            return p
    # any file starting with 'source.'
    for p in sorted(workdir.glob("source.*")):
        return p
    return None
