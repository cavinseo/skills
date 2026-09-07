#!/usr/bin/env python3
"""Step 4 — align transcript with keyframes into one readable timeline.

Usage:
  merge.py WORKDIR [--window 180]

Writes:
  timeline.md    the analysis packet Claude reads to write the notes:
                 metadata + chapters, then one section per screen (keyframe) containing
                 the OCR text of that screen and everything that was said while it was up.
                 If no keyframes exist (audio-only), sections are fixed --window second chunks.
  timeline.json  same, machine-readable.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import die, hms, read_json, write_json  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workdir")
    ap.add_argument("--window", type=float, default=180, help="chunk seconds when no keyframes")
    ap.add_argument("--max-ocr-chars", type=int, default=1200)
    ap.add_argument("--chunk-minutes", type=float, default=10, help="chunk length for chunks/chunk_NN.md")
    a = ap.parse_args()
    wd = Path(a.workdir)

    meta = read_json(wd / "meta.json", {})
    tr = read_json(wd / "transcript.json")
    if not tr:
        die("transcript.json missing — run transcribe.py first")
    segs = tr["segments"]
    frames = read_json(wd / "frames.json", []) or []
    duration = float(meta.get("duration") or (segs[-1]["end"] if segs else 0))

    # section boundaries
    if frames:
        bounds = [(f["t"], f) for f in frames]
        if bounds[0][0] > 0:
            bounds.insert(0, (0.0, None))
    else:
        bounds = [(t, None) for t in [i * a.window for i in range(int(duration // a.window) + 1)]]

    # Assign speech to sections by time overlap. A transcript segment that straddles a
    # slide flip is split by words in proportion to the time it spends on each side, so
    # long segments (VAD-chunked engines) don't dump a whole paragraph onto one slide.
    spoken = [[] for _ in bounds]
    counts = [0] * len(bounds)
    for s in segs:
        s0, s1 = s["start"], max(s["end"], s["start"] + 0.01)
        words = s["text"].split()
        shares = []
        for i, (b0, _f) in enumerate(bounds):
            b1 = bounds[i + 1][0] if i + 1 < len(bounds) else duration + 1
            ov = max(0.0, min(s1, b1) - max(s0, b0))
            shares.append(ov / (s1 - s0))
        if sum(shares) == 0:
            continue
        pos = 0
        for i, sh in enumerate(shares):
            if sh <= 0:
                continue
            take = len(words) - pos if sh >= 0.999 or i == len(shares) - 1 else int(round(len(words) * sh))
            if take > 0:
                spoken[i].append(" ".join(words[pos:pos + take]))
                counts[i] += 1
                pos += take
            if pos >= len(words):
                break

    sections = []
    for i, (start, frame) in enumerate(bounds):
        end = bounds[i + 1][0] if i + 1 < len(bounds) else duration + 1
        sections.append({
            "index": i + 1, "start": start, "end": end,
            "frame": frame["file"] if frame else None,
            "frame_id": frame["id"] if frame else None,
            "ocr": (frame["ocr"] if frame else "")[: a.max_ocr_chars],
            "speech": " ".join(spoken[i]),
            "n_segments": counts[i],
        })

    # ---- markdown ----
    md = [f"# Analysis packet: {meta.get('title', wd.name)}", ""]
    md.append(f"- Source: {meta.get('webpage_url') or meta.get('url') or meta.get('source_path', '')}")
    if meta.get("uploader"):
        md.append(f"- Uploader: {meta['uploader']}  (uploaded {meta.get('upload_date', '?')})")
    md.append(f"- Duration: {hms(duration)}   Transcript: {len(segs)} segments via {tr.get('source')} "
              f"(lang={tr.get('language')})   Screens: {len(frames)}")
    if meta.get("chapters"):
        md.append("\n## Creator chapters")
        for c in meta["chapters"]:
            md.append(f"- [{hms(c['start'] or 0)}] {c['title']}")
    if meta.get("description"):
        md.append("\n## Description (first lines)")
        md.append("\n".join(meta["description"].splitlines()[:12]))

    md.append("\n## Timeline (screen by screen)\n")
    for s in sections:
        head = f"### {s['index']}. [{hms(s['start'])} – {hms(s['end'])}]"
        if s["frame"]:
            head += f"  frame #{s['frame_id']} `{s['frame']}`"
        md.append(head)
        if s["ocr"].strip():
            md.append("**On screen (OCR, may contain errors):**")
            md.append("```\n" + s["ocr"].strip() + "\n```")
        md.append("**Spoken:** " + (s["speech"] or "_(silence / no speech)_"))
        md.append("")

    (wd / "timeline.md").write_text("\n".join(md), encoding="utf-8")
    write_json(wd / "timeline.json", {"meta": meta, "transcript_source": tr.get("source"),
                                       "language": tr.get("language"), "duration": duration,
                                       "sections": sections})
    words = sum(len(s["text"].split()) for s in segs)

    # ---- chunks: anti "lost in the middle" ----
    # Long videos are split into fixed-length chunk files that are each read and summarised
    # on their own before anything global is written. Every chunk gets the same treatment
    # regardless of position, and a note budget proportional to how much was actually said.
    chunks = write_chunks(wd, sections, duration, a.chunk_minutes, meta.get("title", wd.name))
    print(f"{wd / 'timeline.md'}  sections={len(sections)} words={words} chunks={len(chunks)}")


def write_chunks(wd: Path, sections: list[dict], duration: float, chunk_minutes: float, title: str) -> list[dict]:
    import shutil

    cdir = wd / "chunks"
    if cdir.exists():
        shutil.rmtree(cdir)
    cdir.mkdir()
    size = chunk_minutes * 60
    n = max(1, int(-(-duration // size)))  # ceil
    total_words = sum(len(s["speech"].split()) for s in sections) or 1
    chunks = []
    for k in range(n):
        c0, c1 = k * size, min((k + 1) * size, duration)
        mine = [s for s in sections if s["start"] < c1 and s["end"] > c0]
        words = sum(len(s["speech"].split()) for s in mine)
        share = words / total_words
        # ~40 note lines per hour-long video, scaled by this chunk's share of the speech,
        # and never more than one line per ~25 spoken words (short chunks stay short)
        budget = max(3, min(round(40 * share * n), max(3, words // 25)))
        lines = [f"# {title} — chunk {k + 1}/{n}  [{hms(c0)} – {hms(c1)}]",
                 "",
                 f"발화량: {words} words ({share:.0%} of the video). 이 청크의 요약 분량 예산: 약 {budget}줄.",
                 "이 청크만 보고 `chunks/chunk_%02d.notes.md` 를 쓴다. 다른 청크 내용을 미리 가정하지 말 것." % (k + 1),
                 ""]
        for s in mine:
            head = f"### {s['index']}. [{hms(s['start'])} – {hms(s['end'])}]"
            if s["frame"]:
                head += f"  frame #{s['frame_id']} `{s['frame']}`"
            lines.append(head)
            if s["ocr"].strip():
                lines.append("**On screen (OCR):**\n```\n" + s["ocr"].strip() + "\n```")
            lines.append("**Spoken:** " + (s["speech"] or "_(silence)_"))
            lines.append("")
        path = cdir / f"chunk_{k + 1:02d}.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        chunks.append({"id": k + 1, "file": f"chunks/{path.name}", "start": c0, "end": c1,
                       "words": words, "share": round(share, 3), "budget_lines": budget,
                       "sections": [s["index"] for s in mine]})
    write_json(wd / "chunks.json", chunks)
    return chunks


if __name__ == "__main__":
    main()
