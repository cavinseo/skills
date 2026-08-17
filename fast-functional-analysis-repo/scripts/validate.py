#!/usr/bin/env python3
"""
FAST 대시보드 DATA 블록 검증기.

    python scripts/validate.py 결과물.html [--render]

검사 항목
  구조    CORE/SUB/SUBSUB 파싱 가능 여부, 고아 ID, 중복 ID
  형식    기능 기술이 동사+명사 종결형인가 (모듈명 혼입 탐지)
  값      TRL 1-9, 난이도/가치 1-5, Kano 철자, Phase 참조, scores 축 일치
  내용    기본기능 수단 혼입, KPI 베이스라인 null 여부, 포트폴리오 해설 유무
  --render  headless 브라우저로 렌더링해 JS 런타임 오류까지 확인 (playwright 필요)

종료 코드: 오류가 있으면 1, 경고만 있거나 깨끗하면 0.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

KANO_VALID = {"Must-be", "One-dimensional", "Attractive", "Indifferent"}
# 3차 이하 기능명에 들어가면 안 되는 '모듈명' 신호
NOUNY_TAIL = ("모듈", "시스템", "기능", "엔진", "관리자", "매니저", "플랫폼", "솔루션", "서비스")
# 내용이 비어 있는 동사
VAGUE_VERBS = ("관리한다", "지원한다", "처리한다", "수행한다", "제공한다", "운영한다")

ERRORS: list[str] = []
WARNINGS: list[str] = []
NOTES: list[str] = []


def err(m): ERRORS.append(m)
def warn(m): WARNINGS.append(m)
def note(m): NOTES.append(m)


def extract_data(html: str) -> dict:
    """DATA 블록의 JS 리터럴을 node로 평가해 JSON으로 받아온다."""
    script = re.search(r"<script>([\s\S]*?)</script>", html)
    if not script:
        err("<script> 블록을 찾지 못했습니다.")
        return {}
    body = script.group(1)
    # DATA와 ENGINE의 경계를 찾는다. 'ENGINE'이라는 낱말은 DATA 머리말 주석에도
    # 나오므로 단순 find는 0에서 잘린다. 엔진 첫 선언을 우선 landmark로 쓰고,
    # 없으면 ENGINE을 담은 '마지막' 주석 블록의 시작을 쓴다.
    end = None
    landmark = body.find("const $=s=>document.querySelector")
    if landmark != -1:
        opener = body.rfind("/*", 0, landmark)
        end = opener if opener != -1 else landmark
    else:
        banners = [m.start() for m in re.finditer(r"/\*[\s\S]*?ENGINE[\s\S]*?\*/", body)]
        if banners:
            end = banners[-1]
    if end is None or "const CORE" not in body[:end]:
        warn("DATA/ENGINE 경계를 확정하지 못해 <script> 전체를 평가합니다.")
        end = len(body)
    data_src = body[:end]

    harness = (
        data_src
        + "\n"
        + "const __out = {META:typeof META!=='undefined'?META:null,"
        "CORE:typeof CORE!=='undefined'?CORE:null,"
        "SUB:typeof SUB!=='undefined'?SUB:null,"
        "SUBSUB:typeof SUBSUB!=='undefined'?SUBSUB:null,"
        "FLOW:typeof FLOW!=='undefined'?FLOW:null,"
        "LOGIC:typeof LOGIC!=='undefined'?LOGIC:null,"
        "KPI:typeof KPI!=='undefined'?KPI:null,"
        "PHASES:typeof PHASES!=='undefined'?PHASES:null,"
        "VOC:typeof VOC!=='undefined'?VOC:null,"
        "QFD:typeof QFD!=='undefined'?QFD:null,"
        "RISKS:typeof RISKS!=='undefined'?RISKS:null,"
        "NEXT:typeof NEXT!=='undefined'?NEXT:null};\n"
        "console.log(JSON.stringify(__out));\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(harness)
        path = f.name
    try:
        r = subprocess.run(["node", path], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            err(f"DATA 블록 문법 오류 — node 평가 실패:\n{r.stderr.strip()[:800]}")
            return {}
        return json.loads(r.stdout)
    except FileNotFoundError:
        warn("node를 찾을 수 없어 DATA 검증을 건너뜁니다.")
        return {}
    except Exception as e:  # noqa: BLE001
        err(f"DATA 블록 평가 중 오류: {e}")
        return {}
    finally:
        Path(path).unlink(missing_ok=True)


def check_structure(d: dict):
    CORE, SUB, SUBSUB = d.get("CORE"), d.get("SUB"), d.get("SUBSUB")
    if not CORE:
        err("CORE(핵심기능)가 비어 있습니다.")
        return
    if not SUB:
        err("SUB(세부기능)이 비어 있습니다.")
        return

    core_ids = [c["id"] for c in CORE]
    if len(set(core_ids)) != len(core_ids):
        err(f"CORE에 중복 id가 있습니다: {core_ids}")
    if not 3 <= len(CORE) <= 9:
        warn(f"핵심기능이 {len(CORE)}개입니다. 4~8개가 통상 범위입니다 "
             "(3개 이하는 과도한 뭉침, 9개 이상은 묶기 실패 신호).")

    sub_ids = [s["id"] for s in SUB]
    if len(set(sub_ids)) != len(sub_ids):
        dup = [i for i in sub_ids if sub_ids.count(i) > 1]
        err(f"SUB에 중복 id가 있습니다: {sorted(set(dup))}")
    for s in SUB:
        if s.get("core") not in core_ids:
            err(f"[{s['id']}] 부모 핵심기능 '{s.get('core')}'가 CORE에 없습니다.")
    if not 20 <= len(SUB) <= 60:
        warn(f"세부기능이 {len(SUB)}개입니다. 25~50개가 실무 범위입니다 "
             "(20개 미만은 분해 부족, 60개 초과는 3·4차 혼재 가능).")

    if SUBSUB:
        ss_ids = [x["id"] for x in SUBSUB]
        if len(set(ss_ids)) != len(ss_ids):
            dup = [i for i in ss_ids if ss_ids.count(i) > 1]
            err(f"SUBSUB에 중복 id가 있습니다: {sorted(set(dup))}")
        sub_set = set(sub_ids)
        for x in SUBSUB:
            if x["parent"] not in sub_set:
                err(f"[{x['id']}] 부모 세부기능 '{x['parent']}'가 SUB에 없습니다.")
        counts: dict[str, int] = {}
        for x in SUBSUB:
            counts[x["parent"]] = counts.get(x["parent"], 0) + 1
        missing = [i for i in sub_ids if i not in counts]
        if missing:
            warn(f"세세부기능이 없는 세부기능 {len(missing)}개: {', '.join(missing[:8])}"
                 + (" …" if len(missing) > 8 else ""))
        heavy = [k for k, v in counts.items() if v > 6]
        if heavy:
            warn(f"세세부기능이 6개를 넘는 항목: {', '.join(heavy)} — 3차가 너무 컸다는 신호입니다.")


def check_naming(d: dict):
    """기능 기술이 동사+명사 종결형인지."""
    for key, label in (("CORE", "핵심기능"), ("SUB", "세부기능")):
        for item in d.get(key) or []:
            name = item.get("name", "")
            ident = item.get("id", "?")
            if not name:
                err(f"[{ident}] {label} 이름이 비어 있습니다.")
                continue
            if not name.rstrip().endswith("다"):
                err(f"[{ident}] \"{name}\" — {label}은 동사+명사 종결형(~한다)이어야 합니다. "
                    "명사구는 해법을 고정시킵니다.")
            if name.rstrip().endswith(NOUNY_TAIL):
                err(f"[{ident}] \"{name}\" — 모듈명으로 보입니다. 동작으로 바꾸세요.")
            for v in VAGUE_VERBS:
                if name.rstrip().endswith(v):
                    warn(f"[{ident}] \"{name}\" — '{v}'는 내용이 비어 있는 동사입니다. "
                         "무엇을 어떻게 하는지 특정하세요.")


def check_values(d: dict):
    phases = {p["n"] for p in (d.get("PHASES") or [])}
    for s in d.get("SUB") or []:
        i = s["id"]
        trl, diff, val = s.get("trl"), s.get("diff"), s.get("val")
        if not (isinstance(trl, int) and 1 <= trl <= 9):
            err(f"[{i}] TRL이 1–9 범위를 벗어났습니다: {trl}")
        if not (isinstance(diff, int) and 1 <= diff <= 5):
            err(f"[{i}] 난이도가 1–5 범위를 벗어났습니다: {diff}")
        if not (isinstance(val, int) and 1 <= val <= 5):
            err(f"[{i}] 가치가 1–5 범위를 벗어났습니다: {val}")
        if s.get("kano") not in KANO_VALID:
            err(f"[{i}] Kano 값 '{s.get('kano')}'가 올바르지 않습니다. "
                f"허용: {', '.join(sorted(KANO_VALID))}")
        if phases and s.get("phase") not in phases:
            err(f"[{i}] Phase {s.get('phase')}가 PHASES에 정의되어 있지 않습니다.")

    CORE = d.get("CORE") or []
    if CORE:
        axis_sets = {tuple((c.get("scores") or {}).keys()) for c in CORE}
        if len(axis_sets) > 1:
            err("CORE의 scores 축이 항목마다 다릅니다 — 히트맵이 깨집니다. "
                f"발견된 축 조합: {axis_sets}")
        for c in CORE:
            for k, v in (c.get("scores") or {}).items():
                if not (isinstance(v, int) and 1 <= v <= 5):
                    err(f"[{c['id']}] scores['{k}']가 1–5 범위를 벗어났습니다: {v}")


def check_content(d: dict):
    """내용 품질 — 오류가 아니라 되짚어볼 지점."""
    META = d.get("META") or {}

    bf = re.sub(r"<[^>]+>", "", META.get("basicFunction", ""))
    if not bf.strip():
        err("기본기능(META.basicFunction)이 비어 있습니다. FAST의 핵심 산출물입니다.")
    else:
        means = [w for w in ("AI", "인공지능", "센서", "클라우드", "앱", "챗봇", "LLM", "플랫폼")
                 if w in bf]
        if means:
            warn(f"기본기능에 구현 수단이 들어 있습니다: {', '.join(means)}. "
                 "수단은 3차 이하에서 다루고 기본기능은 목적으로 씁니다. (수단 테스트)")
        if len(bf) < 20:
            warn("기본기능이 너무 짧습니다. 차별화 지점이 문장에 담겨 있는지 확인하세요. (경쟁자 테스트)")

    if not (d.get("LOGIC") or []):
        warn("LOGIC(How-Why 검증표)이 비어 있습니다. FAST의 유일한 검증 장치입니다.")

    KPI = d.get("KPI")
    if KPI and KPI.get("rows"):
        if not any(r.get("v") is None for r in KPI["rows"]):
            warn("KPI에 베이스라인(v:null) 행이 없습니다. 현행을 모르면 목표치는 "
                 "검증 불가능한 약속이 됩니다.")

    if not META.get("portfolioNote"):
        warn("META.portfolioNote가 비어 있습니다. 포트폴리오는 그리는 게 아니라 읽는 것입니다 — "
             "어느 사분면에 차별화가 몰렸고 Phase 1에 무엇을 넣어야 하는지 적으세요.")

    if not (META.get("constraints") or []):
        warn("설계 제약(META.constraints)이 비어 있습니다. 제약은 QFD 지붕(상충관계)의 원인이 됩니다.")

    RISKS = d.get("RISKS") or {}
    for r in RISKS.get("rows") or []:
        if len(r) >= 4:
            plain_mit = re.sub(r"<[^>]+>", "", str(r[2]))
            if not re.search(r"F\d+(\.\d+)?", plain_mit):
                warn(f"리스크 '{re.sub(r'<[^>]+>', '', str(r[0]))[:24]}' — "
                     "완화 수단에 기능 ID가 없습니다. 기능으로 연결되지 않은 리스크는 대응되지 않은 것입니다.")
            if not str(r[3]).strip():
                warn(f"리스크 '{re.sub(r'<[^>]+>', '', str(r[0]))[:24]}' — 잔여 리스크가 비어 있습니다. "
                     "완전히 해소되는 리스크는 드뭅니다.")

    VOC = d.get("VOC") or []
    translated = [v[0] for v in VOC if len(v) > 2 and re.search(
        r"(필요하다|중요하다|해야 한다|요구된다)$", str(v[2]).strip())]
    if translated:
        warn(f"VOC {', '.join(translated)}가 요구사항 문장으로 보입니다. "
             "VOC는 고객이 실제로 한 날것의 말이어야 정보가 남습니다.")

    subs = d.get("SUB") or []
    if subs:
        attractive = sum(1 for s in subs if s.get("kano") == "Attractive")
        if attractive / len(subs) > 0.5:
            warn(f"Attractive 가설이 {attractive}/{len(subs)}개로 과다합니다. "
                 "매력품질 오판은 곧 과잉 개발입니다 — 설문 우선 검증 대상으로 표시하세요.")
        p1 = [s for s in subs if s.get("phase") == 1]
        if p1 and not any(s.get("diff", 0) >= 4 for s in p1):
            warn("Phase 1이 전부 저난도 기능입니다. 쉬운 것만 모아 성공하면 아무것도 증명하지 못합니다 — "
                 "전략과제(고난도·고가치)를 최소 하나 포함하세요.")


def check_render(path: str):
    js = f"""
const {{ chromium }} = require('playwright');
(async () => {{
  let exe = undefined;
  try {{ require('fs').accessSync('/opt/pw-browsers/chromium'); exe = '/opt/pw-browsers/chromium'; }} catch (e) {{}}
  const b = await chromium.launch(exe ? {{ executablePath: exe }} : {{}});
  const p = await b.newPage();
  const errs = [];
  p.on('pageerror', e => errs.push('pageerror: ' + e.message));
  p.on('console', m => {{ if (m.type() === 'error') errs.push('console: ' + m.text()); }});
  await p.goto('file://{Path(path).resolve()}');
  await p.waitForTimeout(700);
  const stats = {{
    sections: await p.$$eval('section', e => e.length),
    coreRows: await p.$$eval('#coreTbl tr', e => e.length).catch(() => 0),
    scatter: await p.$$eval('#c3 .mark', e => e.length).catch(() => 0),
  }};
  console.log(JSON.stringify({{ errs, stats }}));
  await b.close();
}})();
"""
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(js)
        jp = f.name
    try:
        r = subprocess.run(["node", jp], capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            warn(f"렌더링 검사를 실행하지 못했습니다 (playwright 미설치 등):\n{r.stderr.strip()[:300]}")
            return
        out = json.loads(r.stdout.strip().splitlines()[-1])
        for e in out["errs"]:
            err(f"렌더링 중 JS 오류 — {e}")
        s = out["stats"]
        note(f"렌더링 확인: 섹션 {s['sections']}개 · 핵심기능 행 {s['coreRows']}개 · 산점도 마커 {s['scatter']}개")
    except Exception as e:  # noqa: BLE001
        warn(f"렌더링 검사 생략: {e}")
    finally:
        Path(jp).unlink(missing_ok=True)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    do_render = "--render" in sys.argv
    if not args:
        print(__doc__)
        sys.exit(2)
    path = args[0]
    html = Path(path).read_text(encoding="utf-8")

    data = extract_data(html)
    if data:
        check_structure(data)
        check_naming(data)
        check_values(data)
        check_content(data)
    if do_render:
        check_render(path)

    print(f"\n{'=' * 62}\nFAST 대시보드 검증 — {Path(path).name}\n{'=' * 62}")
    if data.get("CORE"):
        print(f"핵심기능 {len(data.get('CORE') or [])} · 세부기능 {len(data.get('SUB') or [])} "
              f"· 세세부기능 {len(data.get('SUBSUB') or [])} · VOC {len(data.get('VOC') or [])}")
    for m in NOTES:
        print(f"\n  · {m}")
    if ERRORS:
        print(f"\n오류 {len(ERRORS)}건 — 고쳐야 합니다")
        for m in ERRORS:
            print(f"  ✗ {m}")
    if WARNINGS:
        print(f"\n경고 {len(WARNINGS)}건 — 의도한 것인지 확인하세요")
        for m in WARNINGS:
            print(f"  ! {m}")
    if not ERRORS and not WARNINGS:
        print("\n  ✓ 통과 — 구조·형식·값·내용 점검에서 지적사항이 없습니다.")
    print()
    sys.exit(1 if ERRORS else 0)


if __name__ == "__main__":
    main()
