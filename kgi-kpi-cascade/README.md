# KGI → CSF → KPI 전개 스킬 (kgi-kpi-cascade)

> 목표를 **검산 가능한 지표 체계**로 바꾸고, 인쇄 가능한 점검 보고서로 내보내는 절차.
> 특정 AI 제품에 묶이지 않는다. 파일을 읽고 Python을 실행할 수 있는 에이전트면 어디서나 동작하고, 그것이 안 되는 환경에서도 절차만으로 쓸 수 있다.

---

## 이 스킬이 푸는 문제

KPI를 만들라고 하면 대개 지표를 나열하게 된다. 그런데 나열된 지표는 대부분 이런 상태다.

- 전부 결과지표여서 **무엇을 해야 할지 알 수 없다**
- 목표 숫자에 **근거가 없다** — 검산해 보면 서로 맞지 않는다
- 어느 활동이 어느 성과로 이어지는지 **추적이 안 된다**
- 원자료에 있던 값과 작성자가 추정한 값이 **구분되지 않는다**

이 스킬은 그 넷을 각각 강제한다. 핵심은 한 문장이다.

> **선행지표 목표를 전부 달성했을 때 결과지표 목표가 산술적으로 나와야 한다.**

나오지 않으면 둘 중 하나가 틀린 것이고, 그 사실을 발견하는 것이 이 작업의 가장 큰 소득이다.

---

## 산출물

| 파일 | 용도 |
|---|---|
| `report.html` | 화면 열람·공유 (라이트/다크 자동) |
| `report_bw.html` | 제출·인쇄 (흰 바탕 흑백) |
| `report.pdf` | 첨부·배포 (A4) |

보고서 구성

```
01 KGI 체계           목표 타일 + 갭 분석 막대
02 KGI → CSF → KPI    항목별 전개표 (코드·유형·단위·기준·목표·현황·주기)
03 선행 → 결과 연결    산출 체인 검산 + 연결 경로
04 마감 일정           종료일 기준 역산표
05 핵심 KPI 대시보드   상태 칩
06 점검 의견           멘토링 코멘트
부록 KPI 코드 색인     전체 지표의 목표와 근거 출처
```

---

## 파일 구조

```
kgi-kpi-cascade/
├── SKILL.md                              # 스킬 정의 (메인 — 에이전트가 읽는 절차)
├── README.md
├── assets/
│   ├── template.html                     # HTML 골격
│   ├── theme-color.css                   # 화면용 (라이트/다크)
│   └── theme-print-bw.css                # 흑백 인쇄용
├── references/
│   ├── method.md                         # 선행/결과 관계, 지표 계층, 검산식 모음
│   ├── data-contract.md                  # data.json 필드 레퍼런스
│   └── print-and-export.md               # 흑백 인쇄 CSS, PDF 변환, 체크리스트
├── scripts/
│   ├── render.py                         # data.json → HTML (코드 자동 부여)
│   ├── validate.py                       # 정합성 검사
│   └── to_pdf.py                         # HTML → A4 PDF
└── examples/
    └── sample-data.json                  # 실제 사례 익명화 예시
```

---

## 사용 방법

### 1) 파일을 읽는 에이전트에서 (권장)

Claude Code / Cowork, Cursor, Gemini CLI, Codex, Copilot Workspace 등 로컬 파일을 읽고 셸을 쓸 수 있는 도구.

```
이 폴더의 SKILL.md 절차에 따라 첨부한 사업계획서와 점검표로
KGI-KPI 체계를 만들고 보고서를 내보내줘.
```

에이전트가 `SKILL.md` → `references/*` 순으로 읽고, `data.json`을 작성한 뒤 스크립트를 돌린다.

**Claude Code / Cowork** 에서는 이 폴더를 개인 스킬 경로(`~/.claude/skills/`)에 두면 자동으로 인식된다.
**Cursor** 에서는 `.cursor/rules/` 에 `SKILL.md` 내용을 넣거나 폴더째 워크스페이스에 두고 지시한다.

### 2) 파일을 못 읽는 웹 채팅에서

`SKILL.md` 본문을 붙여넣고 자료를 첨부한다.

```
아래 절차를 따라 KGI-KPI 체계를 만들어줘. 특히 Phase 5 정합성 검산은
반드시 계산해서 보여줄 것.

[SKILL.md 내용 붙여넣기]
```

산출물은 마크다운 표로 받고, 나중에 `data.json`으로 옮겨 렌더링하면 된다.

### 3) 직접 실행

```bash
python3 scripts/validate.py examples/sample-data.json
python3 scripts/render.py  examples/sample-data.json -o report.html
python3 scripts/render.py  examples/sample-data.json -o report_bw.html --bw
python3 scripts/to_pdf.py  report_bw.html report.pdf
```

`examples/sample-data.json`을 복사해 내용을 바꾸는 것이 가장 빠르다.

---

## 요구사항

| 기능 | 필요한 것 |
|---|---|
| 검증·렌더링 | Python 3.8+ (표준 라이브러리만 사용) |
| PDF 변환 | Playwright 또는 wkhtmltopdf — 없으면 브라우저에서 `Ctrl+P` → PDF로 저장 |
| 한글 조판 | Google Fonts(Noto Sans KR, Gowun Batang) — 오프라인이면 폰트 내장 |

```bash
pip install playwright && playwright install chromium   # PDF 변환이 필요할 때만
```

---

## 시작 전 반드시 확인할 것

에이전트가 자료에서 못 찾으면 **묻게 되어 있다.** 추측하면 이후 계산이 전부 틀어진다.

1. **사업(평가) 종료일** — "연말까지"라고 가정하지 말 것. 한 달 차이로 필요 월평균이 30% 이상 달라진다.
2. **현재 누적 실적과 기준일**
3. **사업비 총액과 항목별 배분** — 집행도 지표다

실제로 이 첫 번째 확인 하나가 "박람회 참가비가 사업비에 잡혀 있는데 그 행사가 사업기간 종료 후"라는 문제를 드러낸 적이 있다. 발견이 늦었으면 예산을 못 쓰고 반납했을 건이다.

---

## 적용 범위

정부·지자체 지원사업 중간점검, 창업기업 멘토링·컨설팅 산출물, 연간 경영목표 수립, R&D 과제 성과지표 설계, 팀 단위 목표 관리.

목표에 **기한과 숫자**가 있고 그 달성 여부를 **주기적으로 점검**해야 하는 상황이면 대체로 맞는다.

---

## 라이선스

MIT
