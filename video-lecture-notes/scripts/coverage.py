#!/usr/bin/env python3
"""Coverage check — did the notes actually cover the WHOLE video, or just its ends?

Usage:
  coverage.py WORKDIR [--notes WORKDIR/notes.md] [--bin 10] [--min-bin-ratio 0.35] [--ledger]

Reads every timestamp cited in the notes ([mm:ss], [h:mm:ss], ?t=123, "12:34") and compares
where they fall against where the speech actually is:

  * per-bin table: for each --bin minute window, words spoken vs. citations in the notes
  * thirds check: citation density (citations per 1000 spoken words) for the first, middle and
    last third — the classic failure is a middle third far below the other two
  * uncovered bins: windows with substantial speech (>= 40% of average) but zero citations

Exit code 1 when the notes fail (any uncovered bin, or middle-third density below
--min-bin-ratio of the mean). Fix by going back to the corresponding chunks/chunk_NN.md,
not by sprinkling timestamps.

--ledger additionally builds ledger.md: proper nouns, numbers and OCR slide titles found in
the timeline that do NOT appear in the notes — a checklist of possible omissions
(noisy on purpose; the reader decides what matters).
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import die, hms, read_json  # noqa: E402

TS_PATTERNS = [
    re.compile(r"\[(\d{1,2}):(\d{2}):(\d{2})\]"),
    re.compile(r"\[(\d{1,2}):(\d{2})\]"),
    re.compile(r"[?&]t=(\d+)"),
    re.compile(r"(?<![\d:])(\d{1,2}):(\d{2}):(\d{2})(?![\d:])"),
    re.compile(r"(?<![\d:])(\d{1,2}):(\d{2})(?![\d:])"),
]


def extract_timestamps(text: str) -> list[float]:
    out, taken = [], []
    for pat in TS_PATTERNS:
        for m in pat.finditer(text):
            if any(m.start() < e and m.end() > b for b, e in taken):
                continue  # same characters already matched by a more specific pattern
            taken.append((m.start(), m.end()))
            g = m.groups()
            if len(g) == 1:
                out.append(float(g[0]))
            elif len(g) == 2:
                out.append(int(g[0]) * 60 + int(g[1]))
            else:
                out.append(int(g[0]) * 3600 + int(g[1]) * 60 + int(g[2]))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workdir")
    ap.add_argument("--notes", default=None)
    ap.add_argument("--bin", type=float, default=10, help="minutes per bin")
    ap.add_argument("--min-bin-ratio", type=float, default=0.35,
                    help="middle-third citation density must be >= this × overall density")
    ap.add_argument("--ledger", action="store_true")
    a = ap.parse_args()

    wd = Path(a.workdir)
    tl = read_json(wd / "timeline.json")
    if not tl:
        die("timeline.json missing — run merge.py first")
    notes_path = Path(a.notes) if a.notes else wd / "notes.md"
    if not notes_path.exists():
        die(f"notes not found: {notes_path}")
    notes = notes_path.read_text(encoding="utf-8")
    duration = float(tl["duration"]) or 1.0
    sections = tl["sections"]

    stamps = sorted(t for t in extract_timestamps(notes) if 0 <= t <= duration + 5)
    bin_s = a.bin * 60
    nbins = max(1, int(-(-duration // bin_s)))
    words = [0] * nbins
    for s in sections:
        # spread section words over the bins it overlaps
        n = len(s["speech"].split())
        s0, s1 = s["start"], max(s["end"], s["start"] + 0.01)
        for b in range(nbins):
            b0, b1 = b * bin_s, (b + 1) * bin_s
            ov = max(0.0, min(s1, b1) - max(s0, b0))
            words[b] += n * ov / (s1 - s0)
    cites = [0] * nbins
    for t in stamps:
        cites[min(nbins - 1, int(t // bin_s))] += 1

    total_words = sum(words) or 1
    avg_words = total_words / nbins
    print(f"notes: {notes_path.name}   video: {hms(duration)}   citations found: {len(stamps)}\n")
    print(f"{'bin':>12} {'spoken words':>13} {'citations':>10}  bar")
    uncovered = []
    for b in range(nbins):
        label = f"{hms(b * bin_s)}-{hms(min(duration, (b + 1) * bin_s))}"
        bar = "#" * cites[b]
        flag = ""
        if cites[b] == 0 and words[b] >= 0.4 * avg_words:
            flag = "   <-- UNCOVERED"
            uncovered.append(label)
        print(f"{label:>12} {int(words[b]):>13} {cites[b]:>10}  {bar}{flag}")

    # thirds
    def density(lo: float, hi: float) -> float:
        w = sum(len(s["speech"].split()) * max(0.0, min(s["end"], hi) - max(s["start"], lo)) / max(0.01, s["end"] - s["start"])
                for s in sections)
        c = sum(1 for t in stamps if lo <= t < hi)
        return (c / w * 1000) if w else 0.0

    thirds = [density(i * duration / 3, (i + 1) * duration / 3) for i in range(3)]
    overall = len(stamps) / total_words * 1000
    print("\ncitations per 1000 spoken words —  first third: %.1f   middle: %.1f   last: %.1f   (overall %.1f)"
          % (thirds[0], thirds[1], thirds[2], overall))

    failed = False
    if uncovered:
        failed = True
        print(f"\nFAIL: {len(uncovered)} bin(s) with real speech but no citation: {', '.join(uncovered)}")
    if overall > 0 and thirds[1] < a.min_bin_ratio * overall:
        failed = True
        print(f"FAIL: middle third density {thirds[1]:.1f} < {a.min_bin_ratio:.0%} of overall {overall:.1f} — "
              "the notes lean on the opening/closing. Re-read the middle chunks.")
    if len(stamps) < max(3, nbins):
        failed = True
        print(f"FAIL: only {len(stamps)} timestamps for a {nbins}-bin video — notes need at least one per bin.")

    if a.ledger:
        write_ledger(wd, sections, notes)

    if failed:
        sys.exit(1)
    print("\nPASS: coverage looks even.")


def write_ledger(wd: Path, sections: list[dict], notes: str) -> None:
    low = notes.lower()
    cand: Counter = Counter()
    where: dict[str, float] = {}
    for s in sections:
        text = s["speech"] + " " + s["ocr"]
        for m in re.finditer(r"\b[A-Z][A-Za-z]{2,}(?: [A-Z][A-Za-z]{2,})?\b", text):   # Capitalised names
            cand[m.group(0)] += 1
            where.setdefault(m.group(0), s["start"])
        for m in re.finditer(r"(?<![\w.])\d{2,}(?:[.,]\d+)?\s?(?:%|억|만|천|배|년|명|개|kg|km|달러|원)?", text):  # numbers
            tok = m.group(0).strip()
            if len(tok) >= 2:
                cand[tok] += 1
                where.setdefault(tok, s["start"])
        for line in s["ocr"].splitlines()[:2]:  # slide titles
            line = line.strip()
            if 4 <= len(line) <= 60:
                cand[line] += 2
                where.setdefault(line, s["start"])
    missing = [(k, v, where[k]) for k, v in cand.items() if k.lower() not in low]
    missing.sort(key=lambda x: (-x[1], x[2]))
    out = ["# Ledger — items in the video that the notes do not mention", "",
           "| item | mentions | first at |", "|---|---|---|"]
    out += [f"| {k} | {v} | {hms(t)} |" for k, v, t in missing[:120]]
    (wd / "ledger.md").write_text("\n".join(out), encoding="utf-8")
    print(f"\nledger.md: {len(missing)} candidate omissions (top {min(120, len(missing))} listed)")


if __name__ == "__main__":
    main()
