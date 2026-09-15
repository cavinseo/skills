#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data.json 정합성 검사. 보고서를 내보내기 전에 반드시 돌린다.

    python3 scripts/validate.py data.json

[ERROR] 는 반드시 고친다. [WARN] 은 의도한 것인지 확인한다.
가장 중요한 검사는 '선행 목표를 다 달성하면 결과 목표가 나오는가'다.
"""
import json, sys, re

E, W, OK = [], [], []


def err(m): E.append(m)
def warn(m): W.append(m)
def ok(m): OK.append(m)


def num(x):
    """'95,000천원', '월 31,667' 같은 문자열에서 첫 숫자를 뽑는다."""
    if isinstance(x, (int, float)):
        return float(x)
    m = re.search(r"-?[\d,]+(?:\.\d+)?", str(x or ""))
    return float(m.group().replace(",", "")) if m else None


def main(path):
    d = json.load(open(path, encoding="utf-8"))

    # 1) 기간 ----------------------------------------------------------
    g = d.get("gap", {})
    if not g:
        warn("gap 블록이 없다. 목표 갭 분석 없이는 KPI 목표의 근거를 세울 수 없다.")
    else:
        for f in ("annual_target", "actual", "months_remaining"):
            if f not in g:
                err(f"gap.{f} 누락")
        if not g.get("period_end"):
            err("gap.period_end(사업·평가 종료일) 누락 — 잔여기간 계산의 전제다. 반드시 확인할 것.")
        if all(f in g for f in ("annual_target", "actual", "months_remaining")):
            rem = float(g["annual_target"]) - float(g["actual"])
            need = rem / float(g["months_remaining"])
            base = float(g.get("baseline_monthly") or 0)
            ok(f"잔여 {rem:,.0f} / {g['months_remaining']}개월 = 필요 월평균 {need:,.0f}")
            if base:
                r = need / base
                ok(f"기존 월평균 대비 {r:.1f}배")
                if r > 3:
                    warn(f"필요 배수가 {r:.1f}배다. 목표가 현실적인지 코멘트에서 다룰 것.")

    # 2) 채널 합계 = 잔여 KGI -------------------------------------------
    ch = d.get("channels", [])
    if ch and g:
        tot = sum(float(c["target"]) for c in ch)
        rem = float(g["annual_target"]) - float(g["actual"])
        if abs(tot - rem) > max(1, rem * 0.001):
            err(f"채널 목표 합계 {tot:,.0f} ≠ 잔여 KGI {rem:,.0f} (차이 {tot-rem:+,.0f})")
        else:
            ok(f"채널 합계 {tot:,.0f} = 잔여 KGI")

    # 3) 코드·유형·CSF 구조 ---------------------------------------------
    nR = nS = nProp = nTot = 0
    for sec in d.get("sections", []):
        for csf in sec.get("csfs", []):
            types = [k.get("type", "R").upper() for k in csf.get("kpis", [])]
            if not types:
                err(f'{csf.get("name")} 에 KPI가 없다')
                continue
            if "R" not in types:
                warn(f'{csf.get("name")}: 결과지표(R)가 없다 — 성과를 확인할 방법이 없다')
            if "S" not in types:
                err(f'{csf.get("name")}: 선행지표(S)가 없다 — 관리 불가능한 CSF다')
            for k in csf["kpis"]:
                nTot += 1
                nR += types.count("R") and k.get("type", "R").upper() == "R"
                nS += k.get("type", "R").upper() == "S"
                if k.get("proposed"):
                    nProp += 1
                elif not k.get("source"):
                    warn(f'{k.get("name")}: proposed=false 인데 source(근거)가 없다')
                if not k.get("cycle"):
                    warn(f'{k.get("name")}: 측정주기 미지정')
                if k.get("type", "R").upper() == "S" and k.get("cycle") in ("분기", "반기", "연"):
                    warn(f'{k.get("name")}: 선행지표인데 주기가 {k["cycle"]}다 — '
                         f'선행은 주·월 단위여야 만회가 가능하다')
    if nTot:
        p = nProp / nTot * 100
        ok(f"지표 {nTot}개 (선행 {nS} / 결과 {nR}) · 역산 제안 {nProp}개 ({p:.0f}%)")
        if p > 50:
            warn(f"제안값 비중이 {p:.0f}%다. 본문에 명시하고 확정 전까지 '가설'로 다룰 것.")

    # 3b) 연결 지도·대시보드가 참조하는 코드가 실재하는가 ------------------
    #     코드는 렌더러가 문서 순서로 자동 부여하므로, 본문을 고치면
    #     연결 지도에 손으로 적어 둔 코드가 어긋나기 쉽다.
    valid, r, s = set(), 0, 0
    for sec in d.get("sections", []):
        for csf in sec.get("csfs", []):
            for k in csf.get("kpis", []):
                if k.get("type", "R").upper() == "R":
                    r += 1
                    valid.add(f"R{r}")
                else:
                    s += 1
                    valid.add(f"S{s}")
    refs = set()
    blob = json.dumps({"l": d.get("linkage", {}), "d": d.get("dashboard", [])}, ensure_ascii=False)
    for m in re.finditer(r"\b([RS])(\d+)\b", blob):
        refs.add(m.group(1) + m.group(2))
    dead = sorted(refs - valid, key=lambda x: (x[0], int(x[1:])))
    if dead:
        err(f"존재하지 않는 코드를 참조한다: {', '.join(dead)} "
            f"(유효 범위 S1~S{s}, R1~R{r}) — 본문 순서를 바꾸면 코드도 바뀐다")
    elif refs:
        ok(f"연결 지도·대시보드의 코드 참조 {len(refs)}건 모두 유효")

    # 4) 산출 체인 검산 --------------------------------------------------
    for c in d.get("linkage", {}).get("chain", []):
        for st in c.get("steps", []):
            if st.get("ok") is False:
                err(f'산출 체인 불일치: {c.get("channel")} — {st.get("calc")}')
    t = d.get("linkage", {}).get("chain_total")
    if t and t.get("ok") is False:
        err("산출 체인 합계가 KGI와 맞지 않는다")

    # 5) 기간 밖 항목 ----------------------------------------------------
    for r in d.get("schedule", []):
        if r.get("out_of_period") and not r.get("risk"):
            warn(f'{r.get("period")}: 사업기간 밖인데 리스크 표시가 없다')

    # 6) 사업비 ----------------------------------------------------------
    b = d.get("budget", {})
    if b:
        tot = float(b.get("total", 0))
        ssum = sum(float(i["amount"]) for i in b.get("items", []))
        if tot and abs(ssum - tot) > 1:
            err(f"사업비 항목 합계 {ssum:,.0f} ≠ 총액 {tot:,.0f}")
        else:
            ok(f"사업비 {tot:,.0f} 항목 정합")
        if not any("집행" in k.get("name", "")
                   for s in d.get("sections", []) for c in s.get("csfs", []) for k in c.get("kpis", [])):
            warn("사업비가 있는데 집행률 KPI가 없다 — 기간 내 집행은 별도 지표로 관리할 것")

    # ------------------------------------------------------------------
    for m in OK:
        print(f"  [OK]    {m}")
    for m in W:
        print(f"  [WARN]  {m}")
    for m in E:
        print(f"  [ERROR] {m}")
    print(f"\n{len(E)} error, {len(W)} warning")
    return 1 if E else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
