#!/usr/bin/env python3
"""Step 2 — speech to text.

Usage:
  transcribe.py WORKDIR [--model small|medium|large-v3] [--lang ko] [--prefer-subs] [--device auto]

Writes into WORKDIR:
  transcript.json   {"language": "ko", "source": "whisper|subs", "segments": [{"start","end","text"}]}
  transcript.srt    same content as SRT (handy for editors / other tools)
  transcript.txt    plain text with [mm:ss] timestamps every paragraph

Engine selection:
  * --prefer-subs and a subs.<lang>.vtt/srt exists  -> parse subtitles (fast, no model)
  * otherwise faster-whisper (pip install faster-whisper). Model downloads on first use
    (~500MB for 'small', ~1.5GB 'medium', ~3GB 'large-v3').
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import die, find_source, hms, log, need, run, srt_time, write_json  # noqa: E402


# ---------- subtitle parsing ----------
TS = re.compile(r"(\d+):(\d+):(\d+)[.,](\d+)|(\d+):(\d+)[.,](\d+)")


def _parse_ts(s: str) -> float:
    m = TS.search(s)
    if not m:
        return 0.0
    if m.group(1) is not None:
        h, mi, se, ms = m.group(1), m.group(2), m.group(3), m.group(4)
    else:
        h, mi, se, ms = 0, m.group(5), m.group(6), m.group(7)
    return int(h) * 3600 + int(mi) * 60 + int(se) + int(ms.ljust(3, "0")[:3]) / 1000


def parse_subs(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    segs, last = [], ""
    for block in re.split(r"\n\s*\n", text):
        lines = [l for l in block.strip().splitlines() if l.strip()]
        tl = next((l for l in lines if "-->" in l), None)
        if not tl:
            continue
        a, b = tl.split("-->")[:2]
        body = [l for l in lines[lines.index(tl) + 1:] if not l.strip().isdigit()]
        clean = " ".join(re.sub(r"<[^>]+>", "", l) for l in body).strip()
        clean = re.sub(r"\s+", " ", clean)
        if not clean or clean == last:  # YouTube auto-subs repeat lines
            continue
        last = clean
        segs.append({"start": _parse_ts(a), "end": _parse_ts(b), "text": clean})
    return segs


# ---------- whisper ----------
def whisper_transcribe(media: Path, model_name: str, lang: str | None, device: str) -> tuple[list[dict], str]:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        die("faster-whisper missing: pip install faster-whisper")
    compute = "float16" if device == "cuda" else "int8"
    if device == "auto":
        try:
            import ctranslate2  # noqa
            device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
        except Exception:
            device = "cpu"
        compute = "float16" if device == "cuda" else "int8"
    log(f"loading whisper '{model_name}' on {device} ({compute})")
    model = WhisperModel(model_name, device=device, compute_type=compute)
    segments, info = model.transcribe(
        str(media), language=lang, vad_filter=True, beam_size=5,
        vad_parameters={"min_silence_duration_ms": 500},
    )
    out = []
    for s in segments:
        t = s.text.strip()
        if t:
            out.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": t})
        if len(out) % 50 == 0 and out:
            log(f"  ... {hms(s.end)}")
    return out, info.language


# ---------- sherpa-onnx whisper (works where huggingface.co is blocked: models come from GitHub) ----------
SHERPA_RELEASE = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/"


def sherpa_model_dir(model_name: str) -> Path:
    """Download (once) sherpa-onnx whisper + silero VAD into ~/.cache/vln/."""
    import tarfile
    import urllib.request

    name = {"large-v3": "large-v3", "large": "large-v3"}.get(model_name, model_name)
    cache = Path(os.environ.get("VLN_MODEL_CACHE", Path.home() / ".cache" / "vln"))
    cache.mkdir(parents=True, exist_ok=True)
    mdir = cache / f"sherpa-onnx-whisper-{name}"
    if not mdir.exists():
        url = SHERPA_RELEASE + f"sherpa-onnx-whisper-{name}.tar.bz2"
        tgz = cache / f"whisper-{name}.tar.bz2"
        log(f"downloading {url} (one-time)")
        urllib.request.urlretrieve(url, tgz)
        with tarfile.open(tgz) as tf:
            tf.extractall(cache)
        tgz.unlink()
    vad = cache / "silero_vad.onnx"
    if not vad.exists():
        urllib.request.urlretrieve(SHERPA_RELEASE + "silero_vad.onnx", vad)
    return mdir


def sherpa_transcribe(wav: Path, model_name: str, lang: str | None) -> tuple[list[dict], str]:
    try:
        import numpy as np
        import sherpa_onnx
    except ImportError:
        die("sherpa-onnx missing: pip install sherpa-onnx numpy")
    import wave

    mdir = sherpa_model_dir(model_name)
    stem = mdir.name.replace("sherpa-onnx-whisper-", "")
    enc = mdir / f"{stem}-encoder.int8.onnx"
    dec = mdir / f"{stem}-decoder.int8.onnx"
    if not enc.exists():
        enc, dec = mdir / f"{stem}-encoder.onnx", mdir / f"{stem}-decoder.onnx"
    threads = max(1, (os.cpu_count() or 2))
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=str(enc), decoder=str(dec), tokens=str(mdir / f"{stem}-tokens.txt"),
        language=lang or "", task="transcribe", num_threads=threads)

    w = wave.open(str(wav))
    sr = w.getframerate()
    samples = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0
    vc = sherpa_onnx.VadModelConfig()
    vc.silero_vad.model = str(mdir.parent / "silero_vad.onnx")
    vc.silero_vad.min_silence_duration = 0.4
    vc.silero_vad.max_speech_duration = 18.0   # advisory; split_long() enforces the whisper 30s window
    vc.sample_rate = sr
    vad = sherpa_onnx.VoiceActivityDetector(vc, buffer_size_in_seconds=120)
    ws = vc.silero_vad.window_size
    out, detected = [], lang or "und"

    def split_long(chunk, target: float = 18.0, hard: float = 26.0):
        """Split a long VAD segment at its quietest moments so whisper's 30s window never
        truncates and we don't cut through a word. Returns list of (offset, sub_chunk)."""
        n = len(chunk)
        if n <= int(hard * sr):
            return [(0, chunk)]
        win = int(0.2 * sr)
        pieces, pos = [], 0
        while n - pos > int(hard * sr):
            lo, hi = pos + int((target - 6) * sr), pos + int((target + 6) * sr)
            energies = [(float(np.abs(chunk[i:i + win]).mean()), i) for i in range(lo, hi - win, win // 2)]
            cut = min(energies)[1] + win // 2
            pieces.append((pos, chunk[pos:cut]))
            pos = cut
        pieces.append((pos, chunk[pos:]))
        return pieces

    def decode(start_sample: int, chunk) -> None:
        st = rec.create_stream()
        st.accept_waveform(sr, chunk)
        rec.decode_stream(st)
        t = st.result.text.strip()
        if t:
            out.append({"start": round(start_sample / sr, 2),
                        "end": round((start_sample + len(chunk)) / sr, 2), "text": t})
            if len(out) % 25 == 0:
                log(f"  ... {hms(out[-1]['end'])}")

    def drain():
        while not vad.empty():
            seg = vad.front
            vad.pop()
            # whisper sees 30s windows; VAD normally splits on silence, but continuous
            # speech (or TTS) can exceed that — hard-split so nothing gets discarded.
            for off, piece in split_long(np.asarray(seg.samples, dtype=np.float32)):
                decode(seg.start + off, piece)

    i = 0
    while i + ws <= len(samples):
        vad.accept_waveform(samples[i:i + ws])
        i += ws
        drain()
    vad.flush()
    drain()
    return out, detected


def hf_reachable(timeout: float = 4.0) -> bool:
    import socket
    import urllib.request
    try:
        urllib.request.urlopen("https://huggingface.co", timeout=timeout)
        return True
    except Exception:
        pass
    try:  # local cache already has the model? then faster-whisper works offline
        from huggingface_hub import scan_cache_dir
        return any("whisper" in r.repo_id.lower() for r in scan_cache_dir().repos)
    except Exception:
        return False


def extract_audio(media: Path, workdir: Path) -> Path:
    wav = workdir / "audio16k.wav"
    if not wav.exists():
        need("ffmpeg")
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(media), "-vn", "-ac", "1", "-ar", "16000", str(wav)])
    return wav


def write_outputs(workdir: Path, segs: list[dict], language: str, source: str) -> None:
    write_json(workdir / "transcript.json", {"language": language, "source": source, "segments": segs})
    with open(workdir / "transcript.srt", "w", encoding="utf-8") as f:
        for i, s in enumerate(segs, 1):
            f.write(f"{i}\n{srt_time(s['start'])} --> {srt_time(s['end'])}\n{s['text']}\n\n")
    # paragraph-ish txt: new stamp every ~45s or on long pauses
    lines, buf, buf_start, last_end = [], [], None, 0.0
    for s in segs:
        if buf and (s["start"] - buf_start > 45 or s["start"] - last_end > 2.5):
            lines.append(f"[{hms(buf_start)}] " + " ".join(buf))
            buf = []
        if not buf:
            buf_start = s["start"]
        buf.append(s["text"])
        last_end = s["end"]
    if buf:
        lines.append(f"[{hms(buf_start)}] " + " ".join(buf))
    (workdir / "transcript.txt").write_text("\n\n".join(lines), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workdir")
    ap.add_argument("--model", default="small", help="faster-whisper model (tiny/base/small/medium/large-v3)")
    ap.add_argument("--lang", default=None, help="force language code (ko, en, ...). Default: auto-detect")
    ap.add_argument("--prefer-subs", action="store_true", help="use subtitle file if present instead of whisper")
    ap.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    ap.add_argument("--engine", default="auto", choices=["auto", "faster-whisper", "sherpa"],
                    help="auto = faster-whisper when huggingface.co is reachable, else sherpa-onnx (GitHub models)")
    a = ap.parse_args()

    wd = Path(a.workdir)
    media = find_source(wd)
    if not media:
        die(f"no source.* media in {wd} — run fetch.py first")

    subs = sorted(list(wd.glob("subs.*.vtt")) + list(wd.glob("subs.*.srt")))
    if a.prefer_subs and subs:
        # prefer requested language, else first
        pick = next((s for s in subs if a.lang and f".{a.lang}." in s.name), subs[0])
        segs = parse_subs(pick)
        lang = pick.name.split(".")[1]
        log(f"using subtitles {pick.name}: {len(segs)} cues")
        write_outputs(wd, segs, lang, f"subs:{pick.name}")
    else:
        audio = extract_audio(media, wd)
        engine = a.engine
        if engine == "auto":
            engine = "faster-whisper" if hf_reachable() else "sherpa"
            log(f"engine auto -> {engine}")
        if engine == "faster-whisper":
            segs, lang = whisper_transcribe(audio, a.model, a.lang, a.device)
        else:
            segs, lang = sherpa_transcribe(audio, a.model, a.lang)
        log(f"{engine} done: {len(segs)} segments, language={lang}")
        write_outputs(wd, segs, lang, f"{engine}:{a.model}")
    print(str(wd / "transcript.json"))


if __name__ == "__main__":
    main()
