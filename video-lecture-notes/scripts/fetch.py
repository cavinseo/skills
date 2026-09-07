#!/usr/bin/env python3
"""Step 1 — bring the video into a work directory.

Usage:
  fetch.py <youtube-url | local-file> --out WORKDIR [--audio-only] [--sub-langs ko,en]

Produces inside WORKDIR:
  source.<ext>     the media (video, or audio if --audio-only)
  meta.json        title, uploader, duration, url, chapters, description
  subs.<lang>.vtt  official or auto subtitles when YouTube has them (best effort)

YouTube fetching needs yt-dlp and network access to youtube.com. Anthropic's
cloud sandbox blocks YouTube, so on Cowork-cloud run this step on the user's
machine (device_bash) or ask for a local file instead — see SKILL.md.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import die, ffprobe_duration, is_url, log, need, run, write_json  # noqa: E402


def fetch_url(url: str, out: Path, audio_only: bool, sub_langs: str) -> None:
    need("yt-dlp", "pip install yt-dlp")
    fmt = "bestaudio/best" if audio_only else "bv*[height<=720]+ba/b[height<=720]/best"
    cmd = [
        "yt-dlp", "--no-playlist", "--no-warnings",
        "-f", fmt,
        "--merge-output-format", "mp4",
        "-o", str(out / "source.%(ext)s"),
        "--write-info-json",
        "--write-subs", "--write-auto-subs",
        "--sub-langs", sub_langs,
        "--sub-format", "vtt",
        "--convert-subs", "vtt",
        url,
    ]
    if audio_only:
        cmd += ["-x", "--audio-format", "m4a"]
    run(cmd)

    info_path = next(out.glob("source.info.json"), None)
    meta = {"url": url}
    if info_path:
        info = json.loads(info_path.read_text(encoding="utf-8"))
        meta.update({
            "title": info.get("title"),
            "uploader": info.get("uploader") or info.get("channel"),
            "upload_date": info.get("upload_date"),
            "duration": info.get("duration"),
            "description": (info.get("description") or "")[:4000],
            "chapters": [
                {"title": c.get("title"), "start": c.get("start_time"), "end": c.get("end_time")}
                for c in (info.get("chapters") or [])
            ],
            "tags": info.get("tags") or [],
            "webpage_url": info.get("webpage_url"),
        })
        info_path.unlink()
    # normalise subtitle names: source.ko.vtt -> subs.ko.vtt
    for sub in out.glob("source.*.vtt"):
        lang = sub.name.split(".")[1]
        sub.rename(out / f"subs.{lang}.vtt")
        meta.setdefault("subtitles", []).append(lang)
    write_json(out / "meta.json", meta)


def fetch_local(src: Path, out: Path, audio_only: bool) -> None:
    if not src.exists():
        die(f"file not found: {src}")
    ext = src.suffix.lower().lstrip(".") or "mp4"
    if audio_only and ext not in ("m4a", "mp3", "wav", "aac", "flac", "ogg"):
        need("ffmpeg")
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000",
             str(out / "source.wav")])
    else:
        dest = out / f"source.{ext}"
        if dest.resolve() != src.resolve():
            shutil.copy2(src, dest)
    media = next(out.glob("source.*"))
    write_json(out / "meta.json", {
        "title": src.stem,
        "source_path": str(src.resolve()),
        "duration": ffprobe_duration(media),
        "chapters": [],
    })
    # sidecar subtitles (same stem .srt/.vtt) are picked up automatically
    for sc in list(src.parent.glob(src.stem + ".*.vtt")) + list(src.parent.glob(src.stem + ".vtt")) \
            + list(src.parent.glob(src.stem + ".srt")):
        lang = sc.name.split(".")[1] if sc.name.count(".") >= 2 else "und"
        shutil.copy2(sc, out / f"subs.{lang}{sc.suffix}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="YouTube URL or path to a local video/audio file")
    ap.add_argument("--out", required=True, help="work directory (created if missing)")
    ap.add_argument("--audio-only", action="store_true", help="skip video (no keyframes/OCR possible)")
    ap.add_argument("--sub-langs", default="ko,en,ko-orig,en-orig", help="subtitle languages to try")
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if is_url(a.source):
        fetch_url(a.source, out, a.audio_only, a.sub_langs)
    else:
        fetch_local(Path(a.source).expanduser(), out, a.audio_only)
    media = next(out.glob("source.*"))
    log(f"ready: {media}  ({ffprobe_duration(media):.0f}s)")
    print(json.dumps({"workdir": str(out), "media": str(media)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
