# data.json 필드 레퍼런스

모든 블록은 선택이지만 `meta` · `sections` 는 사실상 필수다.
`rich` 로 표시한 필드는 `<b>` `<br>` `<small>` 같은 최소 마크업을 허용한다. 그 외는 자동 이스케이프된다.

## meta

```json
"meta": {
  "eyebrow": "2026 민간 산림복지 창업·성장 패키지 · FOR GROW",
  "title": "㈜루나무 KGI → KPI 도출표",
  "subtitle": "한국 전통 목공문화 기반 산림복지 DIY KIT 및 체험 서비스",
  "meta_lines": [                                    // rich, 우측 상단 메타 블록
    "기준 자료 <b>사업계획서(2026.07.06) · 사업점검표(2026.08.31)</b>",
    "작성 기준일 <b>2026.09.13</b> · 사업종료 <b>2026.11.30</b>"
  ],
  "footer": "「제안」 표기 수치는 역산 제안값으로 확정 전 협의 필요"   // rich
}
```

## kgi

```json
"kgi": {
  "primary":   { "label": "최상위 KGI · 2026 연매출", "value": "250,000", "unit": "천원",
                 "sub": "2025 실적 174,448천원 대비 <b>+43.3%</b>" },   // sub: rich
  "supporting": [ { "label": "...", "value": "8", "unit": "곳+ 확보", "sub": "..." } ]
}
```

`value` 는 문자열로 넣는다. 천단위 구분과 단위 표기를 작성자가 통제하기 위해서다.

## gap

갭 분석 막대를 그리고 `validate.py` 가 검사하는 블록.

| 필드 | 타입 | 설명 |
|---|---|---|
| `annual_target` | number | 연간(전체) 목표 |
| `actual` | number | 누적 실적 |
| `as_of` | string | 실적 기준일 표기 (예: `"8/31"`) |
| `months_remaining` | number | **종료일 기준** 잔여 개월수 |
| `baseline_monthly` | number | 기존 월평균 실적 |
| `period_end` | string | 사업·평가 종료일. 없으면 validate 가 error |
| `remaining_label` | string | 예: `"9~11월"` |
| `unit` | string | 예: `"천원"` |
| `title` | string | 기본값 `"목표 갭 분석"` |
| `note` | rich | 생략하면 배수를 계산해 자동 생성 |

## channels

채널 배분. 합계가 `annual_target − actual` 과 일치해야 한다.

```json
"channels": [ { "key": "delivery", "name": "기관·학교 납품", "target": 95000 } ]
```

## sections → csfs → kpis

본문 전개표. 배열 순서가 그대로 출력 순서이고, **코드는 이 순서로 자동 부여**된다.

```json
"sections": [{
  "no": "①", "kind": "필수", "title": "수익창출",
  "goal": "KGI · 연매출 250,000천원",                        // rich
  "formula": "연매출 = ⓐ 납품 + ⓑ 체험 + ⓒ 온라인",           // rich, 선택
  "csfs": [{
    "name": "CSF-1\n기관·학교 B2B/B2G 납품 확대",              // \n 은 <br> 로 변환
    "kpis": [{
      "name": "제안·견적 발송 건수",
      "type": "S",                  // "R"(결과) 또는 "S"(선행)
      "unit": "건/월",
      "base": "—",                  // 선택. 한 섹션에서 하나라도 있으면 '기준' 열 생성
      "target": "10",
      "target_note": "월 5회 · 9~11월",   // rich, 선택
      "proposed": true,             // true 면 「제안」 배지
      "source": "점검표",            // proposed=false 일 때 부록 근거 열에 표시
      "current": "—",               // rich
      "cycle": "주"
    }]
  }]
}]
```

`kind` 는 `필수` `선택` `공통` 중 하나. `필수`·`공통`은 채운 배지, `선택`은 테두리 배지로 나온다.

## linkage

```json
"linkage": {
  "intro": "...",                                  // rich, 선택
  "chain_title": "매출 KGI 130,000천원의 산출 체인",
  "chain": [{
    "channel": "ⓐ 기관·학교 납품<br><small>R1 · 95,000천원</small>",   // rich
    "steps": [{
      "leading": "<b class='code'>S1</b> 견적 10건/월",     // rich
      "calc":    "10건 × 30% = <b>월 3건</b>",              // rich
      "result":  "45,000천원",                             // rich
      "ok": true                                          // false 면 validate error
    }]
  }],
  "chain_total": { "text": "95,000 + 15,000 + 20,000 = 130,000천원", "value": "130,000천원", "ok": true },
  "paths": [{
    "leading": "<b class='code'>S15</b><br>KC 시험 접수",
    "path":    "접수 → 시험 6주 → <b class='code'>R15</b> 완료",
    "result":  "<b class='code'>R12</b> 출시의 선결조건",
    "check":   "접수가 늦으면 결과가 아니라 사업기간 자체가 제약 — 만회 불가"
  }]
}
```

`check` 열이 이 표의 핵심이다. 원인 후보를 구체적으로 지목한다.

## schedule

```json
"schedule": [{
  "period": "9월",
  "target": "43,333천원<br><small>누적 163,333</small>",    // rich
  "musts":  "자사몰 오픈 · KC 시험 서류 확정 · ...",          // rich
  "risk":   { "level": "warn", "label": "박람회 대체 편성" },
  "out_of_period": false
}]
```

## dashboard

```json
"dashboard": [{
  "code": "R2",                 // "KGI" 도 가능(회색 표기)
  "kpi": "신규 거래처 수",
  "target": "15곳",
  "current": "8곳+",
  "state": { "level": "ok", "label": "순항" }
}]
```

번호(`#`)는 자동 부여된다.

### state / risk 의 level

| level | 컬러 | 흑백 | 용도 |
|---|---|---|---|
| `ok` | 녹색 | ● 실선 원 | 순항 |
| `warn` | 적색 | ◆ 채운 배경 | 목표 미달 위험, 일정 리스크 |
| `todo` | 회색 | ○ 점선 | 미측정, 체계 구축 필요 |

문자열만 주면 `ok` 로 처리된다.

## comments

```json
"comments": [ { "title": "사업기간이 11월 종료", "body": "..." } ]   // 둘 다 rich
```

## budget (선택)

```json
"budget": { "total": 11000, "items": [ { "name": "소모품비·재료비", "amount": 6600 } ] }
```

넣으면 `validate.py` 가 항목 합계와 총액이 맞는지, 집행률 KPI가 있는지 검사한다.

## labels (선택)

섹션 제목을 바꿀 때 쓴다.

```json
"labels": { "kgi": "KGI 체계", "schedule": "사업종료까지 3개월 마감 일정",
            "comments": "점검 의견 — 멘토링 코멘트", "dash_note": "매월 말 공동 점검" }
```
