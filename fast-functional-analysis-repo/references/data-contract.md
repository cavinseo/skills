# template.html DATA 블록 레퍼런스

`assets/template.html` 상단 `DATA` 영역의 전 필드. 그 아래 `ENGINE` 영역은 수정하지 않는다.

HTML 태그(`<b>`, `<br>`, `<span style>`)는 대부분의 문자열 필드에서 쓸 수 있다. 예외는 아래 표기.

---

## META

| 필드 | 형식 | 설명 |
|---|---|---|
| `title` | HTML | 헤더 제목. `<br>`로 줄바꿈 |
| `subtitle` | HTML | 해결방안 한 줄 요약 |
| `meta` | 문자열 배열 | 헤더 하단 회색 줄. 개정 이력·보완사항 |
| `footer` | 평문 | 페이지 최하단 |
| `task` | HTML | **과업** — FAST 다이어그램 1열 |
| `taskPurpose` | 평문 | 과업의 상위목적 |
| `basicFunction` | HTML | **기본기능** — §0 카드에 크게 표시 |
| `basicFunctionShort` | HTML | FAST 다이어그램 2열용 축약형. 생략 시 `basicFunction` 사용 |
| `basicFunctionNote` | HTML | 기본기능 내 모호한 용어의 정의 |
| `s0Lead` … `s7Lead` | HTML | 각 절 도입부. 그 절에서 **무엇을 판단해야 하는지** 쓴다 |
| `s1Title` | 평문 | §1 제목 (기본: "대응 시나리오 — 핵심 흐름") |
| `tiles` | 배열 | §0 요약 타일. `val`에 `"auto:core"` / `"auto:sub"` / `"auto:subsub"`를 쓰면 개수 자동 계산 |
| `constraintsTitle` | 평문 | 제약 카드 제목 |
| `constraints` | HTML 배열 | 설계 제약. `<b>이름</b> — 설명` 형식 권장 |
| `portfolioNote` | HTML | §5.4 포트폴리오 **해설**. 분포 서술이 아니라 판단을 쓴다 |
| `matrixNote` | HTML | §5.5 평가 매트릭스 해설 |

```js
tiles: [
  {label:"핵심기능 (2차)", val:"auto:core", note:"수집 · 판정 · 대응 · 축적"},
  {label:"세부기능 (3차)", val:"auto:sub", note:"Kano / QFD 분석 단위"},
  {label:"세세부기능 (4차)", val:"auto:subsub", note:"개발 태스크 분해 단위"}
]
```

---

## CORE — 핵심기능 (2차)

```js
{id:"F1", sh:"수집", name:"신호를 수집한다", en:"Data Acquisition",
 def:"...", req:"1항 (실시간 모니터링)", slot:1,
 scores:{"고객가치":5,"차별성":4,"난이도":4,"투자비용":3,"데이터의존":2}}
```

| 필드 | 설명 |
|---|---|
| `id` | `F1`~`F6` 형식. 세부기능 ID의 접두사가 된다 |
| `sh` | 2~3자 약칭. 차트 축 라벨용 |
| `name` | **동사+명사 종결형** |
| `en` | 영문명 (선택) |
| `def` | 기능 정의 한 문장 |
| `req` | 원 요구사항·정의서의 대응 항목 (선택, 없으면 `–`) |
| `slot` | 1~6 → 색상 `--s1`~`--s6`. 순서대로 부여 |
| `scores` | §5.5 히트맵. **모든 CORE가 동일한 축 이름**을 가져야 한다. 1~5 |

---

## SUB — 세부기능 (3차)

배열의 배열. 순서 고정:

```js
["F1.1", "이기종 설비와 통신한다", "기능 정의", "적용기술 A, 기술 B", 8, 4, 5, "시험", "Must-be", 1, 0]
//  id      name(동사+명사)         def            tech              TRL 난이도 가치  단계    Kano가설   Phase 신규
```

| 위치 | 필드 | 값 |
|---|---|---|
| 0 | id | `F1.1` — 앞부분이 CORE의 id와 일치해야 한다 |
| 1 | name | 동사+명사 종결형 |
| 2 | def | 기능 정의 |
| 3 | tech | 적용기술 쉼표 나열. QFD 상단축으로 이관되고 세세부기능의 출처가 된다 |
| 4 | TRL | 1–9 |
| 5 | 난이도 | 1–5 |
| 6 | 가치 | 1–5 |
| 7 | 단계 | `"시험"` / `"최종"` (자유 문자열, 자동으로 범례 생성) |
| 8 | Kano | `"Must-be"` / `"One-dimensional"` / `"Attractive"` / `"Indifferent"` — **철자 정확히** |
| 9 | Phase | 정수. `PHASES`의 `n`과 일치 |
| 10 | 신규 | `1`이면 "신규" 배지 + 필터 버튼 생성. 개정 시에만 사용, 신규 문서는 전부 `0` |

---

## SUBSUB — 세세부기능 (4차)

```js
["F1.1", "F1.1.1", "프로토콜 드라이버 구현"]
//  부모     id        실행 태스크
```

부모 id는 `SUB`에 존재해야 한다. 각 세부기능당 3~4개 권장. 표에서 `▸` 버튼으로 펼쳐진다.

---

## FLOW — §1 시나리오 흐름도

```js
const FLOW = {
  enable: true,
  columns: [
    {head:"① 감지 · 판별", tone:"neutral", steps:[
      {sid:"F1", text:"신호를 실시간 수집"},
      {sid:"F2.7 · 분기점", kind:"gate", text:"<b>대응 주체를 판별한다</b>", note:"L1 자율 / L3 전문가"},
      {sid:"L0 · 즉시", accent:"critical", text:"안전 인터록 → <b>정지·대피 지시</b>"}
    ]}
  ],
  loopNote: "...",
  gradeTable: {...},
  callout: {title:"...", body:"..."}
};
```

| 필드 | 값 |
|---|---|
| `enable` | `false`면 §1 전체 생략 |
| `columns[].head` | 열 제목 |
| `columns[].tone` | `neutral`(회색) / `primary`(파랑) / `accent`(주황) / `alt`(초록) |
| `steps[].sid` | 기능 ID 라벨 (선택) |
| `steps[].kind` | 생략=기본 / `hi`=강조 배경 / `gate`=점선 테두리(분기점·복귀점) |
| `steps[].accent` | 좌측 컬러바: `s1` `s2` `s3` `warning` `critical` (선택) |
| `steps[].text` | 본문 HTML |
| `steps[].note` | 회색 보조설명 (선택) |
| `loopNote` | 흐름도 하단 학습루프 설명 (선택) |
| `callout` | 최대 리스크 강조 박스 (선택) |

단계 사이 화살표(↓)는 자동 삽입된다.

### gradeTable — 판단 기준 표 (선택)

분기점의 등급 체계를 표로 명시한다.

```js
gradeTable: {
  enable:true,
  title:"대응등급 체계 (판별 기준) — 초안",
  head:["등급","대응 주체","해당 상황 예시","시스템이 제공하는 것","목표 대응시간"],
  rows:[
    [{badge:"L1", color:"var(--s1)"}, "<b>자율 대응</b>", "리셋 가능 알람", "단계별 안내", {num:"5분 이내"}]
  ],
  caption:"이 등급표는 QFD에서 <b>기술특성 목표치</b>의 근거가 된다."
}
```

셀 값: 문자열(HTML) / `{badge, color}`(색상 배지) / `{num}`(가운데 정렬 숫자).

---

## LOGIC — How-Why 검증표

```js
const LOGIC = [
  ["생산성·설비 신뢰성 향상", "<b>비계획 정지 손실을 최소화한다</b> (과업)", "대응 주체를 아래로 내려 복구 시간을 줄인다"]
  // [WHY, 기능, HOW]
];
```

과업 → 기본기능 → 각 핵심기능 순으로 한 줄씩. 빈 배열이면 §2 검증표가 생략된다.

---

## KPI — §5.1 대표 지표

```js
const KPI = {
  title:"5.1 자기완결처리율 목표", sub:"본 솔루션의 대표 KPI · 단위 %",
  axisLabel:"전문가 호출 없이 종결한 이벤트 비율", max:100, unit:"%",
  rows:[
    {label:"현행 (베이스라인)", note:"실측 필요", v:null, placeholder:"측정되지 않음 — Phase 1 첫 과업"},
    {label:"Phase 1 목표", note:"L1 유형 한정", v:35}
  ],
  note:"<b>정의</b> — ... <b>주의</b> — 베이스라인 실측이 선행되어야 한다."
};
```

`v: null`이면 점선 빈 막대로 그려지고 `placeholder` 문구가 들어간다. **베이스라인 행은 거의 항상 `null`이어야 한다** — 이유는 `quantification.md` §7.

`KPI`를 `null`로 두면 §5.1이 통째로 생략된다.

---

## PHASES

```js
{n:1, name:"Phase 1 · 시험(PoC)", term:"0–6개월",
 goal:"1개 설비, 웹 UI — <b>검증 질문: 사용자가 실제로 혼자 끝내는가?</b>"}
```

`n`은 `SUB`의 Phase 값과 일치. `goal`에는 **검증 질문**을 굵게 넣는다 — 이것이 없으면 Phase는 일정표에 불과하다.

---

## VOC

```js
["V01", "오퍼레이터", "알람이 떠도 뭘 해야 할지 몰라 결국 반장을 부른다", "조치 방법이 즉시 제시될 것", "F3.1, F3.2"]
//  id     요구주체      고객의 말(날것 그대로)                              환산된 요구품질            주 연관 기능
```

3열은 자동으로 따옴표가 붙고 HTML 이스케이프된다(태그 사용 불가). 나머지는 HTML 가능.

---

## QFD

```js
const QFD = {
  enable:true,
  axisTitle:"QFD 품질의 집 — 축 구성(안)",
  axes:[["<b>좌측 (WHATs)</b>","..."], ...],   // [축 이름, 내용]
  kanoTitle:"Kano 설문 설계 지침",
  kanoGuide:["<b>응답자 계층</b> — ...", ...],  // 항목 배열
  vocCaption:"VOC는 현장 인터뷰 전 가안이다."
};
```

`enable:false`면 §6 전체 생략.

---

## RISKS / NEXT

```js
const RISKS = {
  title:"채택에 따라 새로 생긴 리스크",
  rows:[["<b>환각</b>","근거 없는 조치를 그럴듯하게 안내","F3.2 근거 출처 강제 표시","안전 관련은 사람 확인 필수"]]
  // [리스크, 내용, 완화 기능·설계, 잔여 리스크]
};

const NEXT = {
  title:"다음 단계",
  items:["<b>① 대응등급 실사</b> — 과거 1년 이력을 분류해 실제 상한을 구한다."]
};
```

완화 열에는 **기능 ID를 넣는다**. 잔여 리스크 열을 비우지 않는다.

---

## 검증

```bash
python scripts/validate.py 결과물.html
```

계층 정합성(고아 ID), 기능 기술 형식(동사 종결), Kano 철자, Phase 참조, `scores` 축 일치, 필수 필드 누락을 검사한다. `--render` 옵션을 주면 headless 브라우저로 렌더링해 JS 오류까지 잡는다(playwright 필요).
