# 인쇄와 내보내기

## 두 벌을 만든다

| 파일 | 용도 | 스타일 |
|---|---|---|
| `report.html` | 화면 열람·공유 | `theme-color.css` · 라이트/다크 자동 대응 |
| `report_bw.html` | 제출·인쇄 | `theme-print-bw.css` · 흰 바탕 흑백 고정 |
| `report.pdf` | 첨부·배포 | 위 흑백판을 A4로 변환 |

본문 HTML은 동일하고 `<style>` 블록만 교체된다. 그래서 내용을 한 번만 쓰면 된다.

## 흑백에서 정보를 잃지 않는 법

색을 빼면 구분이 무너진다. 색 대신 **굵기·테두리·빗금·도형**으로 옮긴다.

| 구분 | 컬러판 | 흑백판 |
|---|---|---|
| 결과지표 | 녹색 배지 | 검정 채움 배지 (흰 글씨) |
| 선행지표 | 황토 배지 | 흰 바탕 + 검정 테두리 배지 |
| 제안값 | 황토 글씨 | 점선 테두리 |
| 순항 | 녹색 칩 | ● 실선 원 + 테두리 |
| 경고 | 적색 칩 | ◆ 검정 배경 + 흰 마름모 |
| 미측정 | 회색 칩 | ○ 점선 테두리 |
| 막대 달성분 | 채운 색 | 진한 회색 채움 |
| 막대 부족분 | 빗금 | 45° 빗금 (`repeating-linear-gradient`) |

## 인쇄 CSS 필수 항목

```css
@page { size: A4; margin: 14mm 12mm }

@media print {
  body { -webkit-print-color-adjust: exact; print-color-adjust: exact }
  thead { display: table-header-group }   /* 표가 쪽을 넘어갈 때 머리행 반복 */
  tr { break-inside: avoid }
  .tw { overflow: visible }               /* 화면용 가로 스크롤 해제 */
  table { min-width: 0 }
  h3 { break-after: avoid }               /* 제목만 남고 표가 넘어가는 것 방지 */
  .tw, .gap, .tiles { break-inside: avoid }
}
```

### 긴 표는 예외 처리

`break-inside: avoid` 를 모든 표에 걸면 60행짜리 부록 색인이 한 쪽에 들어가지 못해 **앞 쪽이 통째로 비는** 현상이 생긴다. 긴 표만 따로 푼다.

```css
@media print {
  #idx .tw { break-inside: auto }
  #idx tr  { break-inside: avoid }
  #idx     { break-before: auto }
}
```

### 다크모드 차단

흑백판은 뷰어 테마를 따라가면 안 된다.

```html
<meta name="color-scheme" content="light only">
```
```css
html { color-scheme: light only }
body { background: #fff }
```

## 한글 조판

- 본문 `Noto Sans KR`, 제목 `Gowun Batang` 조합이 공문서 톤에 맞는다.
- 폰트는 Google Fonts `<link>` 로 부른다. 오프라인 제출이 잦으면 `@font-face` + base64 로 내장한다.
- 숫자 열에는 `font-variant-numeric: tabular-nums` 를 준다. 자릿수가 맞아야 표가 읽힌다.
- 인쇄 본문은 11.5px 안팎, 표는 10.5px 안팎이 A4에서 적당하다.

## PDF 변환

```bash
python3 scripts/to_pdf.py report_bw.html report.pdf
```

Playwright(권장) → wkhtmltopdf 순으로 찾는다. 둘 다 없으면 브라우저에서 `Ctrl+P` → PDF로 저장해도 결과는 같다. 인쇄 규칙이 스타일시트에 들어 있기 때문이다.

Playwright 설치:

```bash
pip install playwright && playwright install chromium
```

`wait_for_timeout(1500)` 은 웹폰트 로딩을 기다리는 것이다. 줄이면 폰트가 대체 글꼴로 나올 수 있다.

## 내보낸 뒤 반드시 확인

PDF를 **실제로 열어서** 본다. 렌더링 결과를 보지 않고 배포하지 않는다.

- [ ] 표가 가로로 잘리지 않았다
- [ ] 쪽을 넘는 표에 머리행이 반복된다
- [ ] 제목만 남고 내용이 다음 쪽으로 넘어간 곳이 없다
- [ ] 빈 페이지가 없다 (있으면 `break-inside` 규칙 조정)
- [ ] 흑백 출력에서 결과/선행, 상태 칩이 구분된다
- [ ] 폰트가 대체 글꼴로 떨어지지 않았다

## 다른 형식이 필요할 때

- **한글(HWPX)·워드** — 표 구조를 그대로 옮긴다. 상태 칩은 텍스트(순항/경고/미측정)로 바꾼다.
- **엑셀** — 부록 코드 색인에 「확정·수정·삭제」 체크란을 붙이면 검토 회의용으로 쓸 수 있다.
- **슬라이드** — 01 KGI 타일, 03 산출 체인, 05 대시보드 세 장이면 보고가 된다.
