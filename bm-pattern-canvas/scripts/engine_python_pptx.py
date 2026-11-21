"""BM 패턴 캔버스 엔진 (python-pptx). engine_pptxgenjs.js와 같은 데이터 형식을 쓴다.
사용: from engine_python_pptx import canvas, text ; canvas(slide, x0, y0, w, data, "2F6FB7")
단위는 인치. data = {"els": [...], "arrows": [...], "topH": 3.9, "botH": 1.35}
els 항목: [id, 칸, 가로위치(0~1), 세로위치(0~1), 글자, "c"(타원)|"b"(상자), 번호|None, 너비?, 높이?]
arrows 항목: [출발 id, 도착 id, "r>b" 같은 변 지정(생략 가능)]"""
import math
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

FONT = "Malgun Gothic"
INK, MUTED, WHITE, RED = "1B1F2A", "5B6472", "FFFFFF", "D63B3A"
NAMES = {"kp": "주요 파트너", "ka": "주요 활동", "kr": "주요 자원", "vp": "가치 제안", "cr": "고객 관계",
         "ch": "경로", "cs": "세분 고객", "cost": "비용 구조", "rev": "수익 구조"}

def _rgb(h): return RGBColor.from_string(h)

def text(slide, s, x, y, w, h, size=11, bold=False, color=INK, align="l", anchor="t", italic=False):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE}[anchor]
    for i, line in enumerate(str(s).split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
        r = p.add_run(); r.text = line; f = r.font
        f.size = Pt(size); f.bold = bold; f.italic = italic; f.name = FONT; f.color.rgb = _rgb(color)
        rpr = r._r.get_or_add_rPr(); ea = etree.SubElement(rpr, qn("a:ea")); ea.set("typeface", FONT)
    return tb

def _shape(slide, kind, x, y, w, h, fill, line, lw=1.0):
    sp = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    sp.fill.solid(); sp.fill.fore_color.rgb = _rgb(fill)
    sp.line.color.rgb = _rgb(line); sp.line.width = Pt(lw); sp.shadow.inherit = False
    return sp

def _arrow(slide, p1, c1, c2, p2, color=MUTED, lw=1.75, n=24):
    pts = []
    for i in range(n + 1):
        t = i / n; a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        pts.append((a * p1[0] + b * c1[0] + c * c2[0] + d * p2[0], a * p1[1] + b * c1[1] + c * c2[1] + d * p2[1]))
    fb = slide.shapes.build_freeform(Inches(pts[0][0]), Inches(pts[0][1]))
    fb.add_line_segments([(Inches(x), Inches(y)) for x, y in pts[1:]], close=False)
    sp = fb.convert_to_shape(); sp.fill.background(); sp.shadow.inherit = False
    sp.line.color.rgb = _rgb(color); sp.line.width = Pt(lw)
    ln = sp.line._get_or_add_ln(); tail = etree.SubElement(ln, qn("a:tailEnd")); tail.set("type", "triangle")
    return sp

def canvas(slide, x0, y0, w, d, col):
    gap = 0.06; colW = (w - 4 * gap) / 5; topH = d.get("topH", 3.9); botH = d.get("botH", 1.35)
    halfH = (topH - gap) / 2; bw2 = (w - gap) / 2
    cx = lambda i: x0 + i * (colW + gap)
    B = {"kp": (cx(0), y0, colW, topH), "ka": (cx(1), y0, colW, halfH), "kr": (cx(1), y0 + halfH + gap, colW, halfH),
         "vp": (cx(2), y0, colW, topH), "cr": (cx(3), y0, colW, halfH), "ch": (cx(3), y0 + halfH + gap, colW, halfH),
         "cs": (cx(4), y0, colW, topH), "cost": (x0, y0 + topH + gap, bw2, botH), "rev": (x0 + bw2 + gap, y0 + topH + gap, bw2, botH)}
    for k, (x, y, bw, bh) in B.items():
        _shape(slide, MSO_SHAPE.RECTANGLE, x, y, bw, bh, WHITE, col, 1.0)
        text(slide, NAMES[k], x + 0.08, y + 0.05, bw - 0.16, 0.24, 10, True, MUTED, anchor="m")
    R = {}
    for e in d["els"]:
        e = list(e) + [None] * (9 - len(e)); id_, blk, fx, fy, s, kind, n, ew, eh = e
        bx, by, bw, bh = B[blk]; wide = blk in ("cost", "rev")
        W = ew or ((1.9 if wide else colW - 0.1) if kind == "c" else (1.8 if wide else colW - 0.18))
        H = eh or (0.86 if kind == "c" else 0.56)
        x = bx + fx * bw - W / 2; y = by + 0.3 + fy * (bh - 0.35) - H / 2
        if kind == "c":
            _shape(slide, MSO_SHAPE.OVAL, x, y, W, H, col, col, 1.0); text(slide, s, x, y, W, H, 11, True, WHITE, "c", "m")
        else:
            _shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, W, H, WHITE, col, 1.25); text(slide, s, x, y, W, H, 11, False, INK, "c", "m")
        R[id_] = (x, y, W, H, n)
    SIDE = {"l": (-1, 0), "r": (1, 0), "t": (0, -1), "b": (0, 1)}
    def pt(r, sd):
        x, y, W, H, _ = r
        return {"l": (x, y + H / 2), "r": (x + W, y + H / 2), "t": (x + W / 2, y), "b": (x + W / 2, y + H)}[sd]
    for a in d.get("arrows", []):
        A, Bx = R[a[0]], R[a[1]]
        if len(a) > 2 and a[2]: s1, s2 = a[2].split(">")
        else:
            dx = (Bx[0] + Bx[2] / 2) - (A[0] + A[2] / 2); dy = (Bx[1] + Bx[3] / 2) - (A[1] + A[3] / 2)
            if abs(dx) >= abs(dy): s1, s2 = ("r", "l") if dx > 0 else ("l", "r")
            else: s1, s2 = ("b", "t") if dy > 0 else ("t", "b")
        p1, p2 = pt(A, s1), pt(Bx, s2); k = max(0.25, min(1.6, 0.45 * math.hypot(p2[0] - p1[0], p2[1] - p1[1])))
        c1 = (p1[0] + SIDE[s1][0] * k, p1[1] + SIDE[s1][1] * k); c2 = (p2[0] + SIDE[s2][0] * k, p2[1] + SIDE[s2][1] * k)
        _arrow(slide, p1, c1, c2, p2)
    for x, y, W, H, n in R.values():
        if not n: continue
        _shape(slide, MSO_SHAPE.OVAL, x - 0.02, y - 0.1, 0.27, 0.27, WHITE, RED, 1.5)
        text(slide, str(n), x - 0.02, y - 0.1, 0.27, 0.27, 10, True, RED, "c", "m")

if __name__ == "__main__":
    from pptx import Presentation
    prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
    s = prs.slides.add_slide(prs.slide_layouts[6])
    text(s, "B1  자원의 성 · 지식재산의 성", 0.5, 0.3, 12, 0.6, 26, True)
    demo = {"els": [["ka", "ka", .5, .5, "R&D", "c", 1], ["kr", "kr", .5, .5, "보호받는\n지식재산", "c"],
                    ["vp", "vp", .5, .32, "지식재산에 따른\n차별적 가치", "c", 2], ["cs", "cs", .5, .32, "고객\n세그먼트", "b"],
                    ["cost", "cost", .5, .5, "R&D 비용", "c", None, 1.8], ["rev", "rev", .55, .5, "프리미엄 가격", "b", 3, 2.0]],
            "arrows": [["ka", "kr"], ["kr", "vp", "r>b"], ["vp", "cs"], ["cs", "rev", "b>r"], ["rev", "vp", "l>b"], ["kr", "cost"]]}
    canvas(s, 0.5, 1.3, 7.9, demo, "2F6FB7")
    prs.save("demo_canvas.pptx"); print("saved demo_canvas.pptx")
