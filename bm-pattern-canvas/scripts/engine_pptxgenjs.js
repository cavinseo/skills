// BM canvas engine v2: sparse pattern diagrams with core ellipses, support boxes, curved arrows, feedback loops
module.exports = function (pres, C) {
  const T = (s, text, o) => s.addText(text, Object.assign({ isTextBox: true, margin: 0, color: C.text1, valign: "top" }, o));
  const NAMES = { kp: "주요 파트너", ka: "주요 활동", kr: "주요 자원", vp: "가치 제안", cr: "고객 관계", ch: "경로", cs: "세분 고객", cost: "비용 구조", rev: "수익 구조" };
  function canvas(s, x0, y0, w, d, col) {
    const gap = 0.06, colW = (w - 4 * gap) / 5, topH = d.topH || 3.9, botH = d.botH || 1.35, halfH = (topH - gap) / 2, bw2 = (w - gap) / 2;
    const cx = i => x0 + i * (colW + gap);
    const B = { kp: [cx(0), y0, colW, topH], ka: [cx(1), y0, colW, halfH], kr: [cx(1), y0 + halfH + gap, colW, halfH], vp: [cx(2), y0, colW, topH],
      cr: [cx(3), y0, colW, halfH], ch: [cx(3), y0 + halfH + gap, colW, halfH], cs: [cx(4), y0, colW, topH],
      cost: [x0, y0 + topH + gap, bw2, botH], rev: [x0 + bw2 + gap, y0 + topH + gap, bw2, botH] };
    Object.keys(B).forEach(k => { const [x, y, bw, bh] = B[k];
      s.addShape(pres.shapes.RECTANGLE, { x, y, w: bw, h: bh, fill: { color: C.background1 }, line: { color: col, width: 1 } });
      T(s, NAMES[k], { x: x + 0.08, y: y + 0.05, w: bw - 0.16, h: 0.24, fontSize: 10, bold: true, color: C.text2, valign: "middle" }); });
    const R = {};
    d.els.forEach(e => { const [id, blk, fx, fy, text, kind, n, ew, eh] = e; const [bx, by, bw, bh] = B[blk];
      const wide = blk === "cost" || blk === "rev";
      const W = ew || (kind === "c" ? (wide ? 1.9 : colW - 0.1) : (wide ? 1.8 : colW - 0.18)), H = eh || (kind === "c" ? 0.86 : 0.56);
      const x = bx + fx * bw - W / 2, y = by + 0.3 + fy * (bh - 0.35) - H / 2;
      if (kind === "c") { s.addShape(pres.shapes.OVAL, { x, y, w: W, h: H, fill: { color: col }, line: { color: col, width: 1 } });
        s.addText(text, { isTextBox: true, x, y, w: W, h: H, fontSize: 11, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0 }); }
      else { s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: W, h: H, rectRadius: 0.08, fill: { color: C.background1 }, line: { color: col, width: 1.25 } });
        s.addText(text, { isTextBox: true, x, y, w: W, h: H, fontSize: 11, color: C.text1, align: "center", valign: "middle", margin: 1 }); }
      R[id] = { x, y, w: W, h: H, n }; });
    const SIDE = { l: [-1, 0], r: [1, 0], t: [0, -1], b: [0, 1] };
    const pt = (r, sd) => sd === "l" ? [r.x, r.y + r.h / 2] : sd === "r" ? [r.x + r.w, r.y + r.h / 2] : sd === "t" ? [r.x + r.w / 2, r.y] : [r.x + r.w / 2, r.y + r.h];
    (d.arrows || []).forEach(a => { const A = R[a[0]], Bx = R[a[1]]; let s1, s2;
      if (a[2]) [s1, s2] = a[2].split(">"); else { const dx = (Bx.x + Bx.w / 2) - (A.x + A.w / 2), dy = (Bx.y + Bx.h / 2) - (A.y + A.h / 2);
        if (Math.abs(dx) >= Math.abs(dy)) { s1 = dx > 0 ? "r" : "l"; s2 = dx > 0 ? "l" : "r"; } else { s1 = dy > 0 ? "b" : "t"; s2 = dy > 0 ? "t" : "b"; } }
      const p1 = pt(A, s1), p2 = pt(Bx, s2), dist = Math.hypot(p2[0] - p1[0], p2[1] - p1[1]), k = Math.max(0.25, Math.min(1.6, 0.45 * dist));
      const c1 = [p1[0] + SIDE[s1][0] * k, p1[1] + SIDE[s1][1] * k], c2 = [p2[0] + SIDE[s2][0] * k, p2[1] + SIDE[s2][1] * k];
      const xs = [p1[0], p2[0], c1[0], c2[0]], ys = [p1[1], p2[1], c1[1], c2[1]];
      const mx = Math.min(...xs), my = Math.min(...ys), W = Math.max(0.02, Math.max(...xs) - mx), H = Math.max(0.02, Math.max(...ys) - my);
      s.addShape(pres.shapes.CUSTOM_GEOMETRY, { x: mx, y: my, w: W, h: H,
        points: [{ x: p1[0] - mx, y: p1[1] - my, moveTo: true }, { x: p2[0] - mx, y: p2[1] - my, curve: { type: "cubic", x1: c1[0] - mx, y1: c1[1] - my, x2: c2[0] - mx, y2: c2[1] - my } }],
        line: { color: C.text2, width: 1.75, endArrowType: "triangle" } }); });
    Object.values(R).forEach(r => { if (!r.n) return; const x = r.x - 0.02, y = r.y - 0.1;
      s.addShape(pres.shapes.OVAL, { x, y, w: 0.27, h: 0.27, fill: { color: C.background1 }, line: { color: C.accent5, width: 1.5 } });
      s.addText(String(r.n), { isTextBox: true, x, y, w: 0.27, h: 0.27, fontSize: 10, bold: true, color: C.accent5, align: "center", valign: "middle", margin: 0 }); });
  }
  return { canvas, T };
};
