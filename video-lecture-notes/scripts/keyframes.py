#!/usr/bin/env python3
"""Step 3 — detect slide/scene changes, save keyframes, OCR them, build contact sheets.

Usage:
  keyframes.py WORKDIR [--sample 2] [--hash-dist 6] [--min-gap 4] [--max-frames 150]
                       [--ocr-langs kor+eng] [--no-ocr]

Writes into WORKDIR:
  frames/f0001_00-01-23.jpg   one JPEG per distinct screen (slide / whiteboard state / scene)
  frames.json                 [{"id","t","file","ocr"}...]
  sheets/sheet_01.jpg         contact sheets (12 thumbnails each, timestamps burned in)
                              -> view these with the Read tool to *see* the slides cheaply

How it works: sample one low-res frame every --sample seconds, compute a perceptual
hash, and keep a frame whenever the hash moves more than --hash-dist bits away from the
last kept frame (and at least --min-gap seconds passed). This catches slide flips and
whiteboard progress while ignoring a talking head that just moves a little.
Tune: lecture with slides -> defaults are fine. Whiteboard / handwriting -> --hash-dist 12
--min-gap 20 (fewer, more meaningful frames). Fast-cut vlog -> --max-frames 60.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import die, ffprobe_duration, find_source, hms, log, need, write_json  # noqa: E402


def sample_frames(media: Path, tmp: Path, every: float, height: int = 360) -> list[Path]:
    need("ffmpeg")
    tmp.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(media),
        "-vf", f"fps=1/{every},scale=-2:{height}", "-q:v", "4",
        str(tmp / "s%06d.jpg")], check=True)
    return sorted(tmp.glob("s*.jpg"))


def select_keyframes(samples: list[Path], every: float, hash_dist: int, min_gap: float, max_frames: int):
    import imagehash
    from PIL import Image

    kept, last, last_t = [], None, -1e9
    for i, p in enumerate(samples):
        t = i * every
        im = Image.open(p)
        h = (imagehash.phash(im), imagehash.dhash(im))
        # distance = the larger of two hash families: phash sees layout/structure changes,
        # dhash sees gradient/text-line changes. Text-only slide flips on an identical
        # layout register weakly on phash alone.
        dist = 0 if last is None else max(h[0] - last[0], h[1] - last[1])
        if last is None or (dist >= hash_dist and t - last_t >= min_gap):
            kept.append((t, p, h))
            last, last_t = h, t
    if len(kept) > max_frames:
        # thin evenly while always keeping first frame
        step = len(kept) / max_frames
        kept = [kept[int(i * step)] for i in range(max_frames)]
        log(f"thinned keyframes to {max_frames}")
    return kept


def grab_fullres(media: Path, t: float, dest: Path) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(media),
                    "-frames:v", "1", "-q:v", "2", str(dest)], check=True)


def ocr(path: Path, langs: str) -> str:
    """Tesseract with --psm 4 (single column, variable block sizes) — on slides this keeps
    titles and bullet lines intact where the default psm 3 often drops headers on coloured bars.
    Falls back to psm 6 when psm 4 finds almost nothing (dense whiteboards)."""
    if not shutil.which("tesseract"):
        return ""

    def _run(psm: str) -> list[str]:
        r = subprocess.run(["tesseract", str(path), "-", "-l", langs, "--psm", psm],
                           capture_output=True, text=True)
        txt = r.stdout if r.returncode == 0 else ""
        return [l.strip() for l in txt.splitlines() if len(l.strip()) >= 2]

    lines = _run("4")
    if len(" ".join(lines)) < 20:
        alt = _run("6")
        if len(" ".join(alt)) > len(" ".join(lines)):
            lines = alt
    return "\n".join(lines)


def contact_sheets(frames: list[dict], workdir: Path, per_sheet: int = 12, cols: int = 3, thumb_w: int = 480):
    from PIL import Image, ImageDraw

    sheets_dir = workdir / "sheets"
    if sheets_dir.exists():
        shutil.rmtree(sheets_dir)
    sheets_dir.mkdir()
    out = []
    for si in range(0, len(frames), per_sheet):
        chunk = frames[si:si + per_sheet]
        thumbs = []
        for f in chunk:
            im = Image.open(workdir / f["file"]).convert("RGB")
            im.thumbnail((thumb_w, thumb_w * 9 // 16))
            thumbs.append(im)
        th = max(t.height for t in thumbs) + 22
        rows = (len(thumbs) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * (thumb_w + 8) + 8, rows * (th + 8) + 8), "white")
        d = ImageDraw.Draw(sheet)
        for i, (f, im) in enumerate(zip(chunk, thumbs)):
            x = 8 + (i % cols) * (thumb_w + 8)
            y = 8 + (i // cols) * (th + 8)
            sheet.paste(im, (x, y + 20))
            d.text((x, y + 2), f"#{f['id']}  {hms(f['t'])}", fill="black")
        name = f"sheets/sheet_{si // per_sheet + 1:02d}.jpg"
        sheet.save(workdir / name, quality=85)
        out.append(name)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workdir")
    ap.add_argument("--sample", type=float, default=2.0, help="seconds between sampled frames")
    ap.add_argument("--hash-dist", type=int, default=6, help="hash bit distance (max of phash/dhash) that counts as a new screen (0-64)")
    ap.add_argument("--min-gap", type=float, default=4.0, help="min seconds between kept frames")
    ap.add_argument("--max-frames", type=int, default=150)
    ap.add_argument("--ocr-langs", default="kor+eng")
    ap.add_argument("--no-ocr", action="store_true")
    a = ap.parse_args()

    wd = Path(a.workdir)
    media = find_source(wd)
    if not media:
        die("no source.* in workdir — run fetch.py first")
    if media.suffix.lower() in (".m4a", ".mp3", ".wav", ".aac", ".flac", ".ogg"):
        log("audio-only source: writing empty frames.json")
        write_json(wd / "frames.json", [])
        return

    dur = ffprobe_duration(media)
    log(f"sampling every {a.sample}s over {hms(dur)}")
    tmp = wd / "_samples"
    samples = sample_frames(media, tmp, a.sample)
    kept = select_keyframes(samples, a.sample, a.hash_dist, a.min_gap, a.max_frames)
    log(f"{len(samples)} samples -> {len(kept)} keyframes")

    frames_dir = wd / "frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir()
    frames = []
    for i, (t, _p, _h) in enumerate(kept, 1):
        fname = f"frames/f{i:04d}_{hms(t).replace(':', '-')}.jpg"
        # a change detected at sample t happened somewhere in (t - sample, t]; grabbing a little
        # after t makes sure we are past the flip (and past any fade transition).
        grab_fullres(media, min(t + a.sample * 0.5, max(dur - 0.1, t)), wd / fname)
        text = "" if a.no_ocr else ocr(wd / fname, a.ocr_langs)
        frames.append({"id": i, "t": round(t, 2), "file": fname, "ocr": text})
        if i % 20 == 0:
            log(f"  frame {i}/{len(kept)}")
    shutil.rmtree(tmp, ignore_errors=True)

    sheets = contact_sheets(frames, wd) if frames else []
    write_json(wd / "frames.json", frames)
    write_json(wd / "sheets.json", sheets)
    log(f"done: {len(frames)} frames, {len(sheets)} contact sheets")
    print(str(wd / "frames.json"))


if __name__ == "__main__":
    main()
