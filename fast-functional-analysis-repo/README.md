# FAST 기능분석 스킬 (fast-functional-analysis)

> **Claude AI 스킬** — 제품·시스템·서비스의 기능분석(FAST, Function Analysis System Technique)을 수행하고 인터랙티브 HTML 분석 대시보드를 생성합니다.

---

## 개요

이 스킬은 Claude가 **FAST(Function Analysis System Technique)** 방법론에 따라 제품·시스템·서비스의 기능을 체계적으로 분해·분석하고, 결과를 **인터랙티브 HTML 대시보드**로 만들어주는 절차를 담고 있습니다.

### 핵심 기능
- **5단 계층 분해**: 과업 → 기본기능 → 핵심기능 → 세부기능 → 세세부기능
- **How-Why 논리 검증**: 양방향 논리 검증으로 기능 트리 정합성 보장
- **정량 평가**: TRL·난이도·가치 점수화 및 기능 포트폴리오 산점도
- **Kano·QFD 연계**: VOC → 요구품질 → 품질의 집(HoQ) 설계 지원
- **리스크 분석**: 채택 설계 기반 리스크 식별 및 기능 ID 연결
- **인터랙티브 대시보드**: 라이트/다크 토글, 필터, 차트, 툴팁 자동 생성

---

## 파일 구조

```
fast-functional-analysis/
├── SKILL.md                        # Claude 스킬 정의 (메인)
├── assets/
│   └── template.html               # 인터랙티브 HTML 대시보드 템플릿
├── references/
│   ├── data-contract.md            # DATA 블록 필드 레퍼런스
│   ├── example-plc.md              # 실제 사례 (PLC 통합관리 솔루션)
│   ├── kano-qfd.md                 # Kano 분류·QFD 설계 가이드
│   ├── method.md                   # 기능 기술 규칙·How-Why·흐름도
│   └── quantification.md           # TRL·난이도·가치 척도 정의
└── scripts/
    └── validate.py                 # 데이터 정합성 검증 스크립트
```

---

## 사용 방법

### Claude 스킬로 설치

1. 이 리포지토리를 클론합니다:
   ```bash
   git clone https://github.com/cavinseo/fast-functional-analysis.git
   ```
2. `fast-functional-analysis/` 폴더를 Claude 스킬 디렉터리에 추가합니다.
3. Claude에게 기능분석을 요청합니다.

### 트리거 키워드 (Claude가 자동 인식)

| 한국어 | 영어 |
|---|---|
| 기능분석, FAST 다이어그램, 기능계통도 | functional analysis, FAST diagram |
| 기능전개, VE(가치공학) | value engineering, function tree |
| QFD, 품질의 집, House of Quality | quality function deployment |
| Kano 모델, 요구품질, VOC 전개 | Kano model, VOC analysis |
| 개발 우선순위 도출, WBS 기능분해 | feature prioritization, WBS breakdown |

또한 **"기능을 체계적으로 정리해줘"**, **"개발 우선순위를 정하고 싶다"**, **"제안서에 넣을 기능 구성을 만들어줘"** 처럼 FAST를 명시하지 않아도 기능 체계화·우선순위화가 핵심인 요청이면 자동으로 이 스킬이 작동합니다.

---

## 분석 절차 (6 Phase)

| Phase | 내용 |
|---|---|
| **Phase 0** | 대상 파악과 질문 — 현행 대안, 지불 이유, 사용자 계층, 제약 확인 |
| **Phase 1** | 과업·기본기능 정의 — 경쟁자·수단·"그래서?" 테스트 3중 검증 |
| **Phase 2** | 기능 분해 — 동사+명사 규칙, How-Why 양방향 검증, 시나리오 흐름도 |
| **Phase 3** | 정량화 — TRL·난이도·가치 평가, 포트폴리오 해석, KPI 설계 |
| **Phase 4** | Kano·QFD 연계 — VOC 수집, Kano 분류, QFD 품질의 집 구성 |
| **Phase 5** | 리스크 분석 — 설계 기반 리스크, 완화 기능 ID 연결, 잔여 리스크 |
| **Phase 6** | 대시보드 생성 — template.html DATA 블록 교체 → validate.py 검증 |

---

## 산출물 예시

- [PLC 통합관리 솔루션 기능분석 사례](references/example-plc.md)

---

## 라이선스

MIT License — 자유롭게 사용·수정·배포하세요.
