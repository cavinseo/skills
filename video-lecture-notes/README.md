# 강의 영상 분석 스킬 (video-lecture-notes)

> **Claude AI 스킬** — 유튜브·강의 동영상을 **본 사람처럼** 정리합니다. 음성 전사 + 슬라이드 화면 캡처·OCR을 시간축에서 합쳐 타임스탬프 강의노트를 만듭니다.

자막 요약기와 다른 점은 두 가지입니다.

1. **화면을 함께 본다.** 슬라이드가 넘어가는 시점을 감지해 캡처하고 OCR한 뒤, "그 화면이 떠 있는 동안 강사가 한 말"과 묶습니다.
2. **되짚을 수 있다.** 모든 구간 제목과 인용에 타임스탬프가 붙습니다. 유튜브면 `?t=` 링크로.

여기에 더해, 긴 영상에서 AI가 앞뒤만 요약하는 *lost in the middle* 문제를 구조적으로 막는 장치가 들어 있습니다.

---

## 파이프라인

```
                 ┌─ meta.json (제목·챕터·설명)
 URL / mp4 ──────┼─ source.mp4 ──┬─ transcript.json/.srt/.txt   (Whisper)
   fetch.py      └─ subs.*.vtt   └─ frames/*.jpg + OCR, sheets/  (장면 전환 감지 + tesseract)
                                              │
                                     merge.py │
                                              ▼
                            timeline.md   화면별 [OCR + 그때의 발화]
                            chunks/chunk_NN.md   10분 단위 + 분량 예산
                                              │
                                     Claude가 읽고 작성
                                              ▼
                                        notes.md
                                              │
                                   coverage.py │ 커버리지 검사 (FAIL 시 재작성)
                                              ▼
                        HWPX · DOCX · PPTX · 프로젝트 지식베이스
```

| 스크립트 | 하는 일 |
|---|---|
| `fetch.py` | yt-dlp로 다운로드(720p 상한) 또는 로컬 파일 복사. 제목·채널·챕터·설명·자막 수집 |
| `transcribe.py` | faster-whisper 전사. huggingface.co가 막힌 환경에서는 sherpa-onnx(GitHub 배포 모델)로 자동 전환. 공식 자막이 있으면 `--prefer-subs` |
| `keyframes.py` | phash+dhash로 슬라이드·판서 전환 감지 → 키프레임 저장, 한글+영문 OCR, 12장짜리 contact sheet |
| `merge.py` | 전사와 화면을 시간축에서 정렬 → `timeline.md` + 10분 단위 `chunks/` |
| `coverage.py` | 완성된 노트의 타임스탬프 분포를 발화량과 비교해 누락 구간 검출 |
| `run_all.py` | 위 단계 일괄 실행 |
| `doctor.py` | 도구·네트워크 상태 점검 |
| `make_test_video.py` | 네트워크 없이 테스트할 합성 강의 영상 생성 |

## 설치

```bash
sudo apt install ffmpeg tesseract-ocr tesseract-ocr-kor      # macOS: brew install ffmpeg tesseract tesseract-lang
pip install -r requirements.txt
python scripts/doctor.py                                      # 상태 확인
```

Claude Code 스킬로 쓰려면 이 폴더를 통째로 `~/.claude/skills/video-lecture-notes/` 에 복사합니다.

```bash
git clone https://github.com/cavinseo/skills.git
cp -r skills/video-lecture-notes ~/.claude/skills/
```

## 사용

```bash
# 전체 파이프라인
python scripts/run_all.py "https://youtu.be/XXXX" --out work/my-lecture --lang ko --model small

# 노트를 쓴 뒤 커버리지 검사
python scripts/coverage.py work/my-lecture --ledger
```

Claude에게는 그냥 이렇게 말하면 됩니다. "이 유튜브 강의 정리해줘 https://youtu.be/XXXX"

주요 옵션:

| 상황 | 옵션 |
|---|---|
| 판서·화이트보드 강의 | `--hash-dist 10 --min-gap 20` |
| 편집이 많은 영상 | `--max-frames 60` |
| 전문용어가 많은 한국어 강의 | `--model medium --lang ko` |
| 팟캐스트·녹음 파일 | `--audio-only` (화면 단계 자동 생략) |
| 공식 자막이 있고 빠른 결과가 필요 | `--prefer-subs` |

## lost in the middle 방지

긴 영상을 통째로 읽고 한 번에 요약하면, 서론과 결론만 촘촘하고 중간이 비는 노트가 나옵니다. 모델의 위치 편향, 요약 문장이 앞뒤에 몰리는 강의의 구조, 그리고 "한 번에 읽고 한 번에 쓰는" 작업 방식이 겹친 결과입니다. 이 스킬은 그 작업 방식 자체를 막습니다.

- **청크 map-reduce** — `merge.py`가 10분 단위 `chunks/chunk_NN.md`를 만들고, 각 청크 머리에 그 구간의 발화량과 그에 비례하는 *분량 예산*을 적습니다. 스킬은 청크를 하나씩 읽고 **읽은 즉시** `chunk_NN.notes.md`를 쓰게 한 뒤, 최종 노트는 원본이 아니라 청크 노트들만 모아 씁니다. 모든 청크가 "첫 번째 입력"이 되므로 중간이 흐려지지 않습니다. 서브에이전트가 있으면 청크별 병렬 처리도 가능합니다.
- **커버리지 게이트** — `coverage.py`가 노트의 타임스탬프를 시간축에 뿌려 발화량과 비교합니다. 발화가 있는데 인용이 하나도 없는 구간이 있거나, 중간 1/3의 인용 밀도가 전체 평균의 35% 미만이면 exit 1로 실패합니다.
- **누락 원장** — `--ledger`는 영상에 나왔지만 노트에 없는 고유명사·숫자·슬라이드 제목 후보를 `ledger.md`로 뽑아 줍니다.

```
         bin  spoken words  citations  bar
 00:00-10:00          1402         11  ###########
 10:00-20:00          1533          0     <-- UNCOVERED
 20:00-30:00          1495          0     <-- UNCOVERED
 30:00-38:00          1108          9  #########

citations per 1000 spoken words —  first third: 7.8   middle: 0.0   last: 8.1   (overall 3.6)

FAIL: 2 bin(s) with real speech but no citation: 10:00-20:00, 20:00-30:00
FAIL: middle third density 0.0 < 35% of overall 3.6 — the notes lean on the opening/closing.
```

검사는 "언급했는가"를 잴 뿐 "이해했는가"를 재지는 못합니다. 그래서 타임스탬프만 흩뿌려 통과시키는 것은 SKILL.md에서 명시적으로 금지하고 있습니다.

## 산출물

기본은 마크다운 강의노트(`assets/note_template.md` 구조: 3줄 요약 → 핵심 메시지 → 타임스탬프 목차 → 구간별 상세 → 용어표 → 프레임워크 → 인용 → 비판적 검토 → 적용 아이디어). 여기서 HWPX/DOCX 보고서, PPT 재구성, 프로젝트 지식베이스 축적, 구조화 JSON으로 파생합니다. 변환 규칙은 [`references/output-formats.md`](references/output-formats.md).

## 환경별 제약

| 환경 | 동작 |
|---|---|
| 로컬 Claude Code | 전부 동작. GPU가 있으면 faster-whisper가 자동 사용 |
| 클라우드 샌드박스(Cowork 등) | youtube.com·huggingface.co가 막힌 경우가 있음 → 전사는 sherpa-onnx로 자동 전환, 다운로드는 로컬 머신에서 받아 전달 |
| 연결된 사용자 컴퓨터 | 도구가 설치돼 있으면 그쪽에서 실행하고 결과만 회수 |

자세한 내용은 [`references/setup-and-environments.md`](references/setup-and-environments.md).

## 성능 (CPU 기준, 1시간 영상)

| 모델 | 전사 시간 | 품질 |
|---|---|---|
| small | 20~60분 | 또렷한 한국어/영어 강의에 충분 |
| medium | 1~3시간 | 전문용어·억양에 강함 |
| large-v3 | GPU 권장 | 최고 품질 |

키프레임 추출과 OCR은 1시간 영상 기준 보통 3~10분입니다.

## 라이선스

MIT — [LICENSE](LICENSE). 이 저장소의 코드에 대한 라이선스이며, 분석 대상 영상의 저작권과는 무관합니다 — 본인이 권리를 갖거나 이용이 허락된 영상에만 사용하세요.
