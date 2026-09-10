---
name: porter-value-analysis
description: >
  마이클 포터(1985)의 벨류시스템(Value System)과 벨류체인(Value Chain)을
  인터랙티브 HTML 위젯으로 시각화한다. 산업명이나 서비스명을 주면
  ① 산업군 정의, ② 공급자→기업→구매자로 이어지는 벨류시스템(수평 타일),
  ③ 4~5개 주요 플레이어 유형별 탭형 벨류체인(지원활동 4 × 본원적활동 5)을
  하나의 위젯으로 생성한다.

  다음 키워드가 포함된 요청에 반드시 사용할 것:
  "벨류시스템", "벨류체인", "가치사슬", "가치시스템", "포터", "산업 구조 그려줘",
  "Value System", "Value Chain", "Porter", "산업 가치 흐름", "공급망 구조 시각화",
  "이 산업의 구조를 그려줘", "가치 창출 구조 분석", "산업 플레이어 정리".
  명시적 언급 없이도 특정 산업·서비스의 생태계나 구조 파악을 요청할 때 사용.
sources: [chat]
aliases: [벨류시스템, 벨류체인, 가치사슬, 포터분석, value-chain, value-system]
---

# Porter Value System & Chain 시각화 스킬

## 개요

이 스킬은 **마이클 포터(1985)** 이론을 기반으로 임의의 산업·서비스에 대해
인터랙티브 HTML 위젯을 생성한다. 출력물은 항상 `visualize:show_widget` 도구로
렌더링한다 (파일 생성 X, 아티팩트 X).

출력 구성 (항상 이 순서로):
1. **산업군 정의** — 핵심 산업 분류 + 세부 산업군 3~4개 박스 + 태그
2. **벨류시스템** — 수평 타일 5~8단계 (공급자 체인 → 기업 체인 → 구매자 체인)
3. **벨류체인** — 탭형 인터페이스 (3~5개 플레이어 유형 × 9개 활동 셀)

---

## Step 1 — 산업 분석 (내부 추론)

위젯 생성 전, 다음 내용을 머릿속으로 결정한다.

### 1-1. 산업군 정의
- **핵심 산업군명** (한 줄)
- **세부 산업군** 3~4개: 각각 이름·색상·설명·대표 기업/기관
- **키워드 태그** 6~8개 (규제·기술·수익모델·정책 등 핵심 요소)

> **소셜 임팩트 섹터 특수 처리**: '마진' 개념이 화폐 이익 대신
> 사회적 가치(SROI) + 재무 지속성 두 축으로 대체됨. 마진 바를 둘로 분리.

### 1-2. 벨류시스템 설계
각 타일에 대해 결정:
- **단계 수**: 5~8개 (너무 적으면 구조가 안 보임, 9개 이상이면 가독성 저하)
- **각 타일**: 영역명(9자 이내), 제목(12자 이내), 설명(소재·기능·특징), 대표 기업/기관
- **색상**: 산업 정체성에 맞는 색상 팔레트. 각 타일마다 다른 색

**산업별 색상 가이드**:
| 산업 유형 | 권장 팔레트 |
|---|---|
| 첨단기술·반도체 | 파랑·보라·회색 계열 |
| 농업·식품·자연 | 녹색·갈색·주황 계열 |
| 헬스케어·멘탈 | 청록·보라·소프트 계열 |
| 소셜임팩트·공공 | 청록·남색·따뜻한 보라 |
| 문화·콘텐츠 | 붉은색·자주·금색 계열 |
| 금융·핀테크 | 남색·금색·회색 계열 |

### 1-3. 벨류체인 플레이어 설계
- **플레이어 수**: 3~5개 유형 (탭으로 전환)
- **각 플레이어**: 뱃지명, 색상, 대표 예시 기업/기관, 9개 활동 셀 내용

**9개 활동 셀 순서 (항상 이 순서 유지)**:
```
지원활동 [0] 기업 인프라   [1] 인적자원관리   [2] 기술 개발   [3] 조달
본원적활동 [4] 투입물류    [5] 운영·제조     [6] 산출물류   [7] 마케팅·영업   [8] 서비스
```

**활동별 작성 기준**:
- [0] 인프라: 법인 형태, 자금 구조, 규제·인증, 거버넌스, 리스크 관리
- [1] HR: 핵심 직군, 채용·보상, 교육·전수 방식, 인력 구조 특수성
- [2] R&D: 핵심 기술 개발, 특허·지식재산, 혁신 방향, 측정·검증
- [3] 조달: 핵심 원자재·부품·서비스 조달, 주요 공급업체, 계약 방식
- [4] 투입물류: 입고 검수, 재고 관리, 수급 일정, 품질 관리
- [5] 운영: 핵심 생산·서비스 프로세스, 품질 기준, 생산성 지표
- [6] 산출물류: 배송·배포, 채널 연결, 출하·납품, 버전 관리
- [7] 마케팅: 채널 전략, 고객 획득, 브랜딩, B2B/B2G/B2C 구분
- [8] 서비스: AS, 모니터링, 피드백 루프, 위기 대응, 사후 관리

---

## Step 2 — 위젯 코드 생성

`visualize:show_widget` 도구를 호출한다.

### 필수 CSS 클래스 (항상 포함)
```css
.vs-tier { flex:1; border:0.5px solid var(--color-border-tertiary);
  border-top:2.5px solid; padding:10px 8px;
  background:var(--color-background-primary); min-width:96px; }
.vs-arr  { color:var(--color-text-tertiary); padding:0 3px;
  align-self:center; flex-shrink:0; font-size:18px; }
.vc-tab  { background:none; border:0.5px solid var(--color-border-tertiary);
  border-radius:6px; padding:5px 12px; font-size:12px;
  color:var(--color-text-secondary); cursor:pointer; }
.vc-tab.act { background:var(--color-background-secondary);
  color:var(--color-text-primary); font-weight:500;
  border-color:var(--color-border-secondary); }
.pg { display:grid; grid-template-columns:1fr 1fr 1fr 1fr 1fr 42px;
  border:0.5px solid var(--color-border-tertiary); min-width:580px; }
.pgs { grid-column:1/6; padding:8px 12px;
  border-bottom:0.5px solid var(--color-border-tertiary);
  background:var(--color-background-secondary); }
.pgs.thick { border-bottom:1px solid var(--color-border-primary); }
.pgp { padding:9px 10px; border-right:0.5px solid var(--color-border-tertiary); }
.pgp:last-of-type { border-right:none; }
.pgl { font-size:10px; font-weight:500; color:var(--color-text-tertiary);
  letter-spacing:.04em; margin:0 0 4px; }
.pgc { font-size:11px; color:var(--color-text-secondary); line-height:1.6; }
.pgh { font-size:11px; font-weight:500; color:var(--color-text-primary); margin:0 0 6px; }
.sec-label { font-size:10px; font-weight:500; letter-spacing:.08em;
  color:var(--color-text-tertiary); margin:0 0 8px; text-transform:uppercase; }
.tag { display:inline-block; font-size:10px; font-weight:500;
  padding:2px 7px; border-radius:10px; margin:2px 2px 0 0; }
```

### 섹션 1 — 산업군 정의 블록
```html
<p class="sec-label">▸ 산업군 정의 — Industry Classification</p>
<div style="background:var(--color-background-secondary);
  border:0.5px solid var(--color-border-secondary);
  border-left:3px solid {핵심색};
  border-radius:6px; padding:14px 16px; margin-bottom:1rem;">
  <div style="font-size:13px;font-weight:600;...">핵심 산업군: <span>...</span></div>
  <div style="font-size:11px;...">설명</div>
  <!-- 세부 산업군 박스 3~4개 (display:flex gap:8px) -->
  <!-- 태그 영역 -->
</div>
```

### 섹션 2 — 벨류시스템
```html
<p class="sec-label">▸ 산업 벨류시스템 — Porter (1985) : Value System</p>
<p style="font-size:12px;...">산업 특수성 한두 줄 설명</p>
<div style="overflow-x:auto;">
  <div style="display:flex; align-items:stretch; min-width:{타일수×130}px;">
    <!-- 타일 반복: .vs-tier + border-top-color -->
    <!-- 화살표: .vs-arr > (타일 사이) -->
    <!-- 마진 바: 오른쪽 끝 세로 막대 -->
  </div>
</div>
<!-- 하단 주석 3줄: 산업 특수성 핵심 메모 -->
```

**마진 바 코드**:
```html
<div style="display:flex;align-items:center;justify-content:center;
  flex-shrink:0;width:36px;background:var(--color-background-secondary);
  border:0.5px solid var(--color-border-tertiary);margin-left:4px;">
  <div style="writing-mode:vertical-rl;font-size:10px;font-weight:500;
    color:var(--color-text-primary);letter-spacing:.14em;">마 진</div>
</div>
```

> **소셜 임팩트 특수**: 마진 바 width:46px, 두 줄("사회적 가치" / "재무적 지속성")로 분리.
> 역방향 피드백 루프 박스를 벨류시스템 아래에 추가.

### 섹션 3 — 벨류체인 (탭형)
```html
<div style="margin-top:2.5rem;">
  <p class="sec-label">▸ 주체 유형별 벨류체인 — Porter (1985) : Value Chain</p>
  <!-- 탭 버튼들 -->
  <div style="display:flex;gap:6px;margin-bottom:1rem;flex-wrap:wrap;">
    <button class="vc-tab act" onclick="sw('key1',this)">플레이어1</button>
    ...
  </div>
  <!-- 현재 선택 뱃지 + 예시 기업 -->
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:.75rem;">
    <span id="tb" ...>뱃지</span>
    <span id="ex" ...>예시기업</span>
  </div>
  <!-- 그리드 -->
  <div style="overflow-x:auto;">
    <div class="pg">
      <!-- 지원활동 4개: id="c0"~"c3", 마지막은 .thick -->
      <!-- 본원적활동 5개: id="c4"~"c8" (.pgp) -->
      <!-- 마진 바: grid-column:6 grid-row:1/6 -->
    </div>
  </div>
</div>
```

### JavaScript 데이터 구조
```javascript
const D = {
  player1: {
    badge:'플레이어1명', color:'#RRGGBB',
    ex:'대표 기업·기관 목록',
    d: [
      '지원①인프라 내용',   // c0
      '지원②HR 내용',       // c1
      '지원③R&D 내용',      // c2
      '지원④조달 내용',     // c3
      '본원①투입물류 내용', // c4
      '본원②운영 내용',     // c5
      '본원③산출물류 내용', // c6
      '본원④마케팅 내용',   // c7
      '본원⑤서비스 내용'    // c8
    ]
  },
  // 나머지 플레이어...
};

function sw(key, btn) {
  document.querySelectorAll('.vc-tab').forEach(t => t.classList.remove('act'));
  btn.classList.add('act');
  const d = D[key];
  document.getElementById('tb').textContent = d.badge;
  document.getElementById('tb').style.color = d.color;
  document.getElementById('tb').style.borderColor = d.color;
  document.getElementById('ex').textContent = d.ex;
  d.d.forEach((v, i) => { document.getElementById('c' + i).textContent = v; });
}
sw('player1', document.querySelector('.vc-tab')); // 초기 탭 설정
```

---

## Step 3 — 위젯 호출

```
loading_messages: 4개, 각 5단어 내외, 한국어
title: snake_case 영문 식별자 (예: semiconductor_value_system_chain)
widget_code: 완성된 HTML
```

---

## Step 4 — 위젯 후 텍스트 코멘트

위젯 렌더링 후, 2~4개 항목으로 **산업 구조의 핵심 인사이트**를 텍스트로 보완한다.

권장 코멘트 구조:
1. **이 산업의 핵심 마진 원천** — 어느 단계/역량에서 가치가 집중 창출되는가
2. **병목(Bottleneck) 또는 진입 장벽** — 가장 어렵고 중요한 활동·관계
3. **포지셔닝 시사점** — 구상 중인 서비스/기업이 어디에 위치하는가
4. (선택) **추가 분석 제안** — SWOT, Kano, STP 연계 가능성

---

## 품질 기준

| 항목 | 기준 |
|---|---|
| 벨류시스템 타일 | 5개 이상, 각 단계 기업명 실제 사례 포함 |
| 벨류체인 탭 | 3개 이상, 각 9개 셀 모두 산업 특화 내용 |
| 산업군 정의 | 세부 산업 3개 이상, 태그 6개 이상 |
| 색상 | 단계별 다른 색상, CSS 변수 기반 |
| 반응형 | overflow-x:auto + min-width 설정 필수 |
| 코멘트 | 위젯 후 인사이트 텍스트 반드시 포함 |

---

## 적용 예시 (트리거 패턴)

| 사용자 입력 | 스킬 적용 여부 |
|---|---|
| "반도체 산업의 벨류시스템 그려줘" | ✅ 즉시 |
| "화훼 산업의 가치사슬 분석해줘" | ✅ 즉시 |
| "이 앱의 산업 생태계 구조 그려줘" | ✅ 즉시 |
| "소셜임팩트 서비스의 가치 흐름" | ✅ 즉시 |
| "SWOT 분석해줘" | ❌ (다른 스킬) |
| "이 산업의 경쟁자는?" | ❌ (Porter 5 Forces 필요 시 별도) |

---

## 주의사항

- `visualize:show_widget` 호출 전 반드시 `visualize:read_me` 로 `["diagram","interactive"]` 로드
- HTML 코드에 `<html>`, `<head>`, `<body>` 태그 포함 금지
- 모든 색상은 CSS 변수(`var(--color-*)`) 기반으로 작성 (다크모드 호환)
- `localStorage` 등 브라우저 저장소 사용 금지
- 위젯 코드 내 한국어 문자열은 그대로 삽입 (인코딩 이슈 없음)
- 실제 존재하는 기업명 사용 (가상 기업명 지양)
- 각 셀 내용은 해당 산업에 특화된 구체적 활동 서술 (일반적 설명 지양)
