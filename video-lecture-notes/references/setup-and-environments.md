# Setup & environment notes

## Dependencies

| Need | Package | Install |
|------|---------|---------|
| ffmpeg / ffprobe | system | `apt install ffmpeg` · `brew install ffmpeg` · `winget install Gyan.FFmpeg` |
| YouTube download | yt-dlp | `pip install yt-dlp` |
| Speech-to-text (default) | faster-whisper | `pip install faster-whisper` (models from huggingface.co on first run) |
| Speech-to-text (fallback) | sherpa-onnx | `pip install sherpa-onnx numpy` (models from GitHub releases on first run) |
| Keyframe detection | imagehash, Pillow | `pip install imagehash pillow` |
| OCR | tesseract + kor | `apt install tesseract-ocr tesseract-ocr-kor` · `brew install tesseract tesseract-lang` |

One-liner: `pip install yt-dlp faster-whisper sherpa-onnx imagehash pillow numpy`

Check everything at once: `python scripts/doctor.py`

## Whisper model choice (CPU, per hour of audio, rough)

| model | quality | time on 4-core CPU | memory |
|-------|---------|--------------------|--------|
| small | fine for clear Korean/English lectures | ~10–15 min | ~1 GB |
| medium | noticeably better for technical vocabulary, accents | ~30–45 min | ~2.5 GB |
| large-v3 | best; use on GPU or for short clips | 1h+ on CPU, ~3 min on GPU | ~4 GB |

Korean lectures with jargon: `--model medium --lang ko`. Always pass `--lang` when you know it —
auto-detect can flip to Japanese/Chinese on short noisy openings.

## Where the pipeline is running — three cases

### A. Local Claude Code on the user's own machine (the normal case)
Everything works: yt-dlp reaches YouTube, faster-whisper downloads from Hugging Face,
GPU is used automatically if ctranslate2 sees CUDA.

### B. Cowork / Claude cloud sandbox
The sandbox blocks youtube.com and huggingface.co (but PyPI, apt and github.com work).
Consequences and what to do:
- `fetch.py <youtube-url>` fails with `Tunnel connection failed: 403`. Options, in order:
  1. If a computer is linked (device tools available): run `yt-dlp` there with `device_bash`
     into a connected folder, then `device_stage_files` the mp4 (and any .vtt) into the sandbox,
     then `fetch.py <staged mp4> --out WORKDIR`. Prefer 720p or `-f "bv*[height<=480]+ba"` to keep
     the transfer under the 400 MB per-file cap; for long lectures use `--audio-only` plus a
     separate low-res video for keyframes if needed.
  2. Ask the user to attach the video file to the chat.
  3. If the user can paste the YouTube transcript ("...more → Show transcript"), save it as
     `subs.ko.vtt`-style text in WORKDIR and run `transcribe.py WORKDIR --prefer-subs`.
- Whisper: `transcribe.py` auto-detects that Hugging Face is unreachable and switches to the
  sherpa-onnx engine, whose models download from GitHub (small ≈ 640 MB one-time, cached in
  `~/.cache/vln`). Quality is the same Whisper weights; segments are VAD-chunked (up to ~18 s)
  instead of sentence-level, which `merge.py` compensates for by splitting straddling segments
  across slide boundaries.
- CPU only, 2 cores: budget ~1× real-time for `small`. For a 90-minute lecture that is 60–90 min;
  run it in the background and tell the user.

### C. User's machine via device_bash (Cowork with linked computer)
The local VM may have no network at all. `which yt-dlp ffmpeg` first. If tools exist, run the
whole pipeline there and stage only `timeline.md`, `frames.json`, `frames/` and `sheets/` back —
never the video.

## GPU
faster-whisper picks CUDA automatically when `ctranslate2.get_cuda_device_count() > 0`.
Force with `--device cuda`. Apple Silicon: faster-whisper runs CPU int8; fine for `small`/`medium`.
