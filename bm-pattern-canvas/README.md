# bm-pattern-canvas

기업의 비즈니스 모델을 9캔버스로 분석하고 오스터왈더의 BM 유형을 판별해, 도식과 번호별 설명 표가 담긴 PPT로 만드는 스킬이다.

## 무엇을 하나

- 기업 자료를 조사해 9캔버스를 채운다
- BM 유형을 세 층으로 판별한다: 《비즈니스 모델의 탄생》 5패턴, 《최강 기업의 탄생》 발명 패턴 9범주 27유형, 개선 패턴 12전환
- 이전·이후 또는 기업 간 도식을 나란히 그린다. 핵심 요소는 타원, 보조 요소는 상자, 흐름은 곡선 화살표로 표시한다
- 도식의 번호와 대응하는 설명 표를 만든다

기본 산출물은 3장짜리 PPTX다(소개·맥락·유형 / BM 도식 / 번호별 설명 표).

## 구성

| 경로 | 용도 |
|---|---|
| `SKILL.md` | 지침 본문. 이 파일 하나만 있어도 동작한다 |
| `scripts/engine_pptxgenjs.js` | PPTX 도식 엔진 (Node.js, pptxgenjs) |
| `scripts/engine_python_pptx.py` | PPTX 도식 엔진 (Python, python-pptx). 단독 실행하면 예시 파일을 만든다 |
| `examples/demo_canvas.pptx` | Python 엔진으로 만든 예시 한 장 |

## 쓰는 방법

**스킬을 지원하는 환경**: 이 폴더를 스킬 디렉터리에 넣거나 압축해 올린다. "○○의 BM을 분석해 줘"처럼 요청하면 불린다.

**그 밖의 AI**: `SKILL.md`를 맞춤 지침이나 지식 파일로 넣거나, 대화에 첨부하고 "이 지침대로 ○○를 분석해 줘"라고 요청한다. 코드를 실행할 수 있으면 `scripts/`의 엔진도 함께 올린다. 코드를 실행할 수 없으면 지침의 B 방식(HTML과 SVG) 또는 C 방식(글과 표)으로 결과가 나온다.

## 요청 예시

- "넷플릭스의 BM을 이전·이후로 분석해 줘"
- "스타벅스와 블루보틀의 BM을 비교해 줘"
- "P1 매출 차별자 유형을 도식으로 설명해 줘"

## 엔진 사용

두 엔진은 같은 데이터 형식을 받는다. 형식은 `SKILL.md` 6장에 있다.

```python
from engine_python_pptx import canvas, text
canvas(slide, 0.5, 1.3, 7.9, data, "2F6FB7")
```

```js
const { canvas, T } = require("./engine_pptxgenjs.js")(pres, pres.SchemeColor);
canvas(slide, 0.5, 1.3, 7.9, data, pres.SchemeColor.accent6);
```

Node 엔진은 테마 색(dk2, lt2, accent5)이 정의되어 있어야 한다.

## 알아둘 점

- Python 엔진은 곡선을 짧은 선분 여러 개로 근사해 그린다. 화면에서는 곡선으로 보이지만 PowerPoint에서 점 편집을 하면 꼭짓점이 많다
- 글꼴은 맑은 고딕으로 지정되어 있다. Python 엔진은 `FONT` 값을 바꾸면 된다
- 유형 이름은 국내 번역판 목차 표기를 따랐다. F2 채널의 왕, B3 규모 확장자, P3 마진의 달인과 그 하위 유형은 원서 용어를 옮긴 것이라 번역판과 다를 수 있다
- 책에 실린 사례 기업은 지침에 넣지 않았다. 인용할 때는 원문을 확인한다
- 유형 판별은 분석자의 해석이며, 산출물에도 그렇게 밝히도록 되어 있다

## 출처

유형 체계는 알렉산더 오스터왈더 외 《비즈니스 모델의 탄생》(Business Model Generation)과 《최강 기업의 탄생》(The Invincible Company)에 근거한다. 도식 문법과 엔진은 이 스킬에서 따로 만든 것이다.
