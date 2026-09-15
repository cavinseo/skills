#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data.json -> KGI/CSF/KPI 보고서 HTML 생성기.

    python3 scripts/render.py data.json -o report.html            # 화면용 컬러
    python3 scripts/render.py data.json -o report_bw.html --bw    # 흑백 인쇄용

지표 코드(S1../R1..)는 문서 순서대로 자동 부여된다. 손으로 매기지 말 것.
스키마는 references/data-contract.md 참조.
"""
import argparse, html, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")


def esc(x):
    return html.escape(str(x)) if x is not None else ""


def rich(x):
    """<b>, <br> 등 최소 마크업을 허용하는 필드."""
    return "" if x is None else str(x)


class Doc:
    def __init__(self, data):
        self.d = data
        self.codes = {}          # kpi id -> code
        self.index = []          # 부록 색인 행
        self._r = self._s = 0
        self._assign_codes()

    # ---------- 코드 자동 부여 ----------
    def _assign_codes(self):
        for sec in self.d.get("sections", []):
            for csf in sec.get("csfs", []):
                for k in csf.get("kpis", []):
                    if k.get("type", "R").upper() == "R":
                        self._r += 1
                        code = f"R{self._r}"
                    else:
                        self._s += 1
                        code = f"S{self._s}"
                    k["_code"] = code
                    self.index.append((sec, k))

    # ---------- 01 KGI ----------
    def kgi(self):
        k = self.d.get("kgi", {})
        p = k.get("primary", {})
        tiles = [
            f'<div class="tile lead"><div class="lbl">{esc(p.get("label","최상위 KGI"))}</div>'
            f'<div class="val">{esc(p.get("value",""))}<em>{esc(p.get("unit",""))}</em></div>'
            f'<div class="sub">{rich(p.get("sub",""))}</div></div>'
        ]
        for t in k.get("supporting", []):
            tiles.append(
                f'<div class="tile"><div class="lbl">{esc(t.get("label",""))}</div>'
                f'<div class="val">{esc(t.get("value",""))}<em>{esc(t.get("unit",""))}</em></div>'
                f'<div class="sub">{rich(t.get("sub",""))}</div></div>'
            )

        g = self.d.get("gap", {})
        rows = ""
        if g:
            tgt = float(g["annual_target"])
            act = float(g["actual"])
            rem = tgt - act
            months = float(g["months_remaining"])
            need = rem / months if months else 0
            base = float(g.get("baseline_monthly", 0))
            pct = act / tgt * 100 if tgt else 0
            ratio = need / base if base else 0
            u = g.get("unit", "")
            fmt = lambda v: f"{v:,.0f}"
            scale = max(need, base) or 1
            rows = "".join([
                _bar("연간 목표", 100, f"{fmt(tgt)}{u}"),
                _bar(f"{g.get('as_of','현재')} 누적 실적", pct, f"{fmt(act)}{u} · {pct:.0f}%"),
                _bar(f"잔여 목표 ({g.get('remaining_label','')})", 100 - pct, f"{fmt(rem)}{u} · {100-pct:.0f}%", cls="hatch", offset=pct),
                _bar("기존 월평균 실적", base / scale * 100, f"{fmt(base)}{u}/월"),
                _bar("잔여기간 필요 월평균", need / scale * 100, f"{fmt(need)}{u}/월", cls="w"),
            ])
            note = g.get("note") or (
                f"잔여 {g.get('remaining_label','')} 동안 월 실적을 <b>약 {ratio:.1f}배</b>로 "
                f"끌어올려야 달성한다.")
            rows = (f'<div class="gap"><div class="eyebrow" style="margin-bottom:8px">'
                    f'{esc(g.get("title","목표 갭 분석"))}</div>{rows}'
                    f'<p class="note">{rich(note)}</p></div>')

        return _section("kgi", "01", self.d.get("labels", {}).get("kgi", "KGI 체계 — 최종 목표지표"),
                        "Key Goal Indicator",
                        f'<div class="tiles">{"".join(tiles)}</div>{rows}')

    # ---------- 02 전개 ----------
    def cascade(self):
        legend = ('<div class="legend">'
                  '<span><i class="t r">결과</i> 성과를 확인하는 후행지표</span>'
                  '<span><i class="t l">선행</i> 결과를 만들어 내는 활동·과정지표</span>'
                  '<span><i class="p">제안</i> 원자료에 수치가 없어 역산·통례로 제시한 값</span>'
                  '<span><b class="code">S1 R1</b> 지표 식별코드 — 연결 지도에서 상호 참조</span>'
                  '</div>')
        out = [legend]
        for sec in self.d.get("sections", []):
            has_base = any(k.get("base") not in (None, "") for c in sec["csfs"] for k in c["kpis"])
            tag = sec.get("kind", "선택")
            cls = "tag" if tag in ("필수", "공통") else "tag opt"
            out.append(f'<h3><span class="{cls}">{esc(tag)}</span>{esc(sec.get("no",""))} '
                       f'{esc(sec["title"])}<span class="goal">{rich(sec.get("goal",""))}</span></h3>')
            if sec.get("formula"):
                out.append(f'<p class="formula">{rich(sec["formula"])}</p>')
            th = ('<thead><tr><th>CSF</th><th class="c">코드</th><th>KPI</th><th class="c">유형</th>'
                  '<th>단위</th>' + ('<th class="num">기준</th>' if has_base else '') +
                  '<th class="num">목표</th><th>현황</th><th class="c">주기</th></tr></thead>')
            body = []
            for csf in sec["csfs"]:
                n = len(csf["kpis"])
                for i, k in enumerate(csf["kpis"]):
                    tds = []
                    if i == 0:
                        nm = esc(csf["name"]).replace("\n", "<br>")
                        tds.append(f'<td class="csf" rowspan="{n}">{nm}</td>')
                    tds.append(f'<td class="c cd"><b class="code">{k["_code"]}</b></td>')
                    tds.append(f'<td>{esc(k["name"])}</td>')
                    ty = "r" if k.get("type", "R").upper() == "R" else "l"
                    tds.append(f'<td class="c"><i class="t {ty}">{"결과" if ty=="r" else "선행"}</i></td>')
                    tds.append(f'<td>{esc(k.get("unit",""))}</td>')
                    if has_base:
                        tds.append(f'<td class="num">{esc(k.get("base","—"))}</td>')
                    goal = esc(k.get("target", "—"))
                    if k.get("proposed"):
                        goal += '<span class="p">제안</span>'
                    if k.get("target_note"):
                        goal += f'<br><small style="color:var(--ink-3)">{rich(k["target_note"])}</small>'
                    tds.append(f'<td class="num">{goal}</td>')
                    tds.append(f'<td>{rich(k.get("current","—"))}</td>')
                    tds.append(f'<td class="c">{esc(k.get("cycle",""))}</td>')
                    body.append("<tr>" + "".join(tds) + "</tr>")
            out.append(f'<div class="tw"><table>{th}<tbody>{"".join(body)}</tbody></table></div>')
        return _section("kpi", "02", "KGI → CSF → KPI 전개",
                        f'항목 {len(self.d.get("sections",[]))}개', "".join(out))

    # ---------- 03 연결 지도 ----------
    def linkage(self):
        L = self.d.get("linkage", {})
        if not L:
            return ""
        default_intro = ("<b class=\"code\">S</b>는 선행(활동), <b class=\"code\">R</b>은 결과다. "
                         "한 지표가 아래 단계에서는 결과이면서 위 단계에서는 선행이 되기도 한다.")
        parts = ['<p style="margin:0 0 16px;font-size:13.5px;color:var(--ink-2);max-width:72ch">'
                 + rich(L.get("intro", default_intro)) + '</p>']

        chain = L.get("chain", [])
        if chain:
            parts.append(f'<h3>ⓐ {esc(L.get("chain_title","목표 산출 체인"))}'
                         f'<span class="goal">선행 목표를 모두 달성하면 결과 목표가 나오는지 검산</span></h3>')
            rows = []
            for c in chain:
                n = len(c.get("steps", [])) or 1
                for i, st in enumerate(c["steps"]):
                    tds = []
                    if i == 0:
                        tds.append(f'<td class="csf" rowspan="{n}">{rich(c["channel"])}</td>')
                    tds.append(f'<td>{rich(st["leading"])}</td>')
                    tds.append(f'<td class="calc">{rich(st["calc"])}</td>')
                    tds.append(f'<td class="num">{rich(st["result"])}</td>')
                    tds.append(f'<td class="ok-mark">{"✓" if st.get("ok", True) else "✗"}</td>')
                    rows.append("<tr>" + "".join(tds) + "</tr>")
            if L.get("chain_total"):
                t = L["chain_total"]
                bg = ' style="background:var(--ochre-soft)"'
                rows.append(f'<tr><td class="csf"{bg}>합계</td><td colspan="2"{bg}>{rich(t["text"])}</td>'
                            f'<td class="num"{bg}><b>{rich(t["value"])}</b></td>'
                            f'<td class="ok-mark"{bg}>{"✓" if t.get("ok",True) else "✗"}</td></tr>')
            parts.append('<div class="tw"><table><thead><tr><th>채널</th><th>선행지표 (활동)</th>'
                         '<th>산출식</th><th class="num">결과</th><th class="c">검산</th></tr></thead>'
                         f'<tbody>{"".join(rows)}</tbody></table></div>')

        paths = L.get("paths", [])
        if paths:
            parts.append('<h3>ⓑ 비매출 항목의 선행 → 결과 경로'
                         '<span class="goal">선행을 다 했는데 결과가 안 나오면 무엇을 의심할 것인가</span></h3>')
            rows = "".join(
                f'<tr><td class="csf">{rich(p["leading"])}</td><td class="calc">{rich(p["path"])}</td>'
                f'<td>{rich(p["result"])}</td><td>{rich(p["check"])}</td></tr>' for p in paths)
            parts.append('<div class="tw"><table><thead><tr><th>선행지표</th><th>연결 경로</th>'
                         '<th>최종 기여</th><th>선행 달성 · 결과 미달 시 점검할 가정</th></tr></thead>'
                         f'<tbody>{rows}</tbody></table></div>')
        return _section("link", "03", "선행 → 결과 연결 지도",
                        "어느 활동이 어느 성과를 만드는가", "".join(parts))

    # ---------- 04 마감 일정 ----------
    def schedule(self):
        sc = self.d.get("schedule", [])
        if not sc:
            return ""
        rows = "".join(
            f'<tr><td class="csf c">{rich(r["period"])}</td><td class="num">{rich(r.get("target","—"))}</td>'
            f'<td>{rich(r["musts"])}</td><td>{_chip(r.get("risk"))}</td></tr>' for r in sc)
        return _section("close", "04", self.d.get("labels", {}).get("schedule", "마감 일정"),
                        "기간별 필수 완료 항목",
                        '<div class="tw"><table><thead><tr><th class="c">시점</th><th class="num">목표</th>'
                        '<th>반드시 끝나야 할 일</th><th>마감 리스크</th></tr></thead>'
                        f'<tbody>{rows}</tbody></table></div>')

    # ---------- 05 대시보드 ----------
    def dashboard(self):
        db = self.d.get("dashboard", [])
        if not db:
            return ""
        rows = ""
        for i, r in enumerate(db, 1):
            code = r.get("code", "")
            cls = "code kgi" if code.upper() == "KGI" else "code"
            rows += (f'<tr><td class="c">{i}</td><td class="c cd"><b class="{cls}">{esc(code)}</b></td>'
                     f'<td>{rich(r["kpi"])}</td><td class="num">{rich(r.get("target","—"))}</td>'
                     f'<td>{rich(r.get("current","—"))}</td><td>{_chip(r.get("state"))}</td></tr>')
        return _section("dash", "05", f'핵심 KPI {len(db)} — 정기 점검 대시보드',
                        self.d.get("labels", {}).get("dash_note", ""),
                        '<div class="tw"><table><thead><tr><th class="c">#</th><th class="c">코드</th>'
                        '<th>핵심 KPI</th><th class="num">목표</th><th>현황</th><th>상태</th></tr></thead>'
                        f'<tbody>{rows}</tbody></table></div>')

    # ---------- 06 코멘트 ----------
    def comments(self):
        cm = self.d.get("comments", [])
        if not cm:
            return ""
        items = "".join(
            f'<div class="note-item"><div class="idx">{i}</div><div><h4>{rich(c["title"])}</h4>'
            f'<p>{rich(c["body"])}</p></div></div>' for i, c in enumerate(cm, 1))
        return _section("notes", "06", self.d.get("labels", {}).get("comments", "점검 의견"),
                        "", f'<div class="notes">{items}</div>')

    # ---------- 부록 색인 ----------
    def appendix(self):
        if not self.index:
            return ""
        rows, cur = [], None
        n_prop = sum(1 for _, k in self.index if k.get("proposed"))
        for sec, k in self.index:
            if sec is not cur:
                cur = sec
                rows.append(f'<tr><td colspan="4" class="grp">{esc(sec.get("no",""))} {esc(sec["title"])}</td></tr>')
            src = "<b>역산 제안</b>" if k.get("proposed") else esc(k.get("source", "원문"))
            rows.append(f'<tr><td class="c"><b class="code">{k["_code"]}</b></td><td>{esc(k["name"])}</td>'
                        f'<td class="num">{esc(k.get("target","—"))}</td><td class="c">{src}</td></tr>')
        intro = (f'03장에서 쓴 <b class="code">S</b>·<b class="code">R</b> 코드의 전체 목록이다. '
                 f'<b>근거</b> 열은 그 목표치가 어디서 나왔는지를 밝힌 것이다. '
                 f'전체 {len(self.index)}개 중 <b>{n_prop}개가 역산 제안</b>이므로, '
                 f'확정하기 전까지는 목표가 아니라 <b>가설</b>로 다뤄야 한다.')
        return _section("idx", "부록", "KPI 코드 색인",
                        f"전체 {len(self.index)}개 · 선행 {self._s} · 결과 {self._r}",
                        f'<p style="margin:0 0 14px;font-size:13.5px;color:var(--ink-2);max-width:74ch">{intro}</p>'
                        '<div class="tw"><table><thead><tr><th class="c">코드</th><th>KPI</th>'
                        '<th class="num">목표</th><th class="c">근거</th></tr></thead>'
                        f'<tbody>{"".join(rows)}</tbody></table></div>')

    def header(self):
        m = self.d.get("meta", {})
        meta = "<br>".join(rich(x) for x in m.get("meta_lines", []))
        return (f'<header><div><div class="eyebrow">{esc(m.get("eyebrow",""))}</div>'
                f'<h1>{esc(m.get("title",""))}<small>{esc(m.get("subtitle",""))}</small></h1></div>'
                f'<div class="meta">{meta}</div></header>')

    def build(self):
        body = (self.header() + self.kgi() + self.cascade() + self.linkage() +
                self.schedule() + self.dashboard() + self.comments() + self.appendix())
        foot = self.d.get("meta", {}).get("footer", "")
        return f'<div class="wrap">{body}<footer>{rich(foot)}</footer></div>'


def _bar(label, pct, value, cls="", offset=None):
    pct = max(0, min(100, pct))
    style = f'width:{pct:.1f}%'
    if offset is not None:
        style += f';left:{offset:.1f}%'
    return (f'<div class="row"><span class="k">{esc(label)}</span>'
            f'<div class="bar"><i class="{cls}" style="{style}"></i></div>'
            f'<span class="v">{esc(value)}</span></div>')


def _chip(state):
    if not state:
        return "—"
    if isinstance(state, str):
        state = {"level": "ok", "label": state}
    lvl = state.get("level", "ok")
    return f'<span class="st {esc(lvl)}">{esc(state.get("label",""))}</span>'


def _section(sid, no, title, note, inner):
    n = f'<span class="n">{esc(no)}</span>' if no else ""
    p = f'<p>{esc(note)}</p>' if note else ""
    return (f'<section id="{sid}"><div class="sec-head">{n}<h2>{esc(title)}</h2>{p}</div>'
            f'{inner}</section>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--bw", action="store_true", help="흑백 인쇄용 스타일")
    ap.add_argument("--lang", default="ko")
    a = ap.parse_args()

    data = json.load(open(a.data, encoding="utf-8"))
    css_file = "theme-print-bw.css" if a.bw else "theme-color.css"
    css = open(os.path.join(ASSETS, css_file), encoding="utf-8").read()
    tpl = open(os.path.join(ASSETS, "template.html"), encoding="utf-8").read()

    out = (tpl.replace("{{LANG}}", a.lang)
              .replace("{{COLOR_SCHEME_META}}",
                       '<meta name="color-scheme" content="light only">' if a.bw else "")
              .replace("{{TITLE}}", esc(data.get("meta", {}).get("title", "KGI-KPI 체계")))
              .replace("{{CSS}}", css)
              .replace("{{CONTENT}}", Doc(data).build()))
    open(a.out, "w", encoding="utf-8").write(out)
    print(f"wrote {a.out} ({len(out):,} bytes)")


if __name__ == "__main__":
    sys.exit(main())
