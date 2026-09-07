# Output formats — where the notes go after `notes.md` exists

Write `notes.md` first, always. Every other format is derived from it, so the user can ask
for "the same thing as a PPT" later without re-analysing the video.

## 1. Markdown lecture notes (default)
- File: `WORKDIR/notes.md`, built from `assets/note_template.md`.
- Embed the 3–8 most informative frames inline: `![슬라이드 제목](frames/f0007_00-12-40.jpg)`.
  A frame earns its place when it carries a diagram, table, formula or a slide the notes refer to;
  a talking-head frame never does.
- Deliver `notes.md` and, when frames are embedded, zip `notes.md + frames/` so links resolve.

## 2. HWPX (한글) / DOCX report
Use the `hwpx` skill (Korean institutional reports) or `docx` skill. Map the note sections onto
the document like this:
- 표지/머리말: title, source, date, analyst
- 요약: "한눈에 보기" + "핵심 메시지"
- 본문: 구간별 상세 정리 (one heading per 구간, timestamp in the heading)
- 표: 핵심 개념·용어 table, 목차 table
- 부록: 인용문, 후속 질문; embed 3–6 keyframes as figures with captions "[mm:ss] 슬라이드: …"
Don't paste the full transcript into the report unless asked — attach `transcript.txt` beside it.

## 3. PPT reconstruction
Two different requests hide behind "PPT로 만들어줘" — ask which one if unclear:
- **Re-teach deck** (the user will present this content): one slide per 구간 from the notes,
  title = 구간 제목, body = 3–5 bullets of the spoken essence, speaker notes = the fuller
  paragraph + timestamp. Use the `pptx` skill (or `nongchon-green-deck` for the deep-green
  institutional style). Never paste keyframes as the slide itself — rebuild as native text/shapes;
  keyframes may go in the notes pane or as a small "원본 화면" thumbnail.
- **Slide archive** (the user wants the original slides): one slide per keyframe image, full-bleed,
  timestamp caption. `frames/` already has the images; this is a 20-line pptxgenjs/python-pptx job.

## 4. Project knowledge base (accumulating across many videos)
When a Claude Project is attached (Projects tool present), write after each analysis:
- `videos/<yyyy-mm-dd>-<slug>.md` — the full `notes.md`
- `videos/INDEX.md` — one line per analysed video: date · title · source · 3 keywords · path.
  Read it first, append, write back (there is no in-place patch).
Keep frames out of the project (images don't help RAG search); the notes describe them.
When the user maintains a topic map (e.g. an ontology or curriculum doc), add a "관련 영상"
line there pointing to the new note instead of duplicating content.

## 5. Structured JSON (for downstream tools)
`timeline.json` is already machine-readable. If the user wants notes as data too, emit
`notes.json` with keys: title, source, summary[3], key_message, toc[{t,title,summary}],
concepts[{term,definition,t}], quotes[{text,t}], critique[], applications[].
