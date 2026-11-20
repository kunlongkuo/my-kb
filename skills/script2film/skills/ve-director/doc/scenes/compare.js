// compare — two columns side by side (A vs B); an optional verdict marks one of them.
// p.left / p.right: {title, text, at} · p.verdict: {side: "left"|"right", text, at}
// p.big: the text under each title is the point (a rank, a number): about twice the size, and the words sit lower so the
// frame's lower half is not empty (with side.zoom 1.3 the right column still ends left of the host frame)
// p.slam (with big): each column's text lands with slamIn instead of fading in
// p.left.items / p.right.items: [{text, at, hot}] instead of text: a ledger that grows one line per mention under each title
// (e.g. 發行公司｜凍結 vs 攻擊者｜換成以太幣, six lines added over about 30 s on one board);
// hot: that line gets the red underline
SCENES.compare = p => {
  drift(p);
  const Z = p.big ? { title: 84, text: 104, w: 840, ty: 230, by: 400, vy: 720, vs: 72, line: "M 960 180 L 960 860" }
                  : { title: 64, text: 48, w: 680, ty: 250, by: 410, vy: 640, vs: 52, line: "M 960 200 L 960 760" };
  draw(stroke(Z.line, 4, FG, .35), .05, .5);
  const col = (s, cx, rot) => {
    const c = p[s]; if (!c) return null; const t = at(c.at, s === "left" ? .4 : 1.6);
    const h = box(c.title, { cx, y: Z.ty, cls: "card", size: Z.title, rot }); h.style.fontWeight = 800;
    // a long title (「利甲族（耶利米書 35:14）」 at big size) ran past the centre line and off the frame edge:
    // shrink it until it fits its column, then re-centre
    for (let k = 0; k < 4 && h.offsetWidth > Z.w; k++) h.style.fontSize = Math.floor(parseFloat(h.style.fontSize) * Z.w / h.offsetWidth) + "px";
    h.style.left = (cx - h.offsetWidth / 2) + "px"; popIn(h, t);
    if (c.text) { const b = box(c.text, { cx, y: Z.by, size: Z.text, w: Z.w }); b.style.textAlign = "center"; b.style.lineHeight = 1.4;
      if (p.big) b.style.fontWeight = 800;
      b.style.left = (cx - b.offsetWidth / 2) + "px"; if (p.slam) slamIn(b, t + .25); else popIn(b, t + .25); }
    let y = Z.by;
    (c.items || []).forEach((it, k) => {
      const r = box(it.text, { cx, y, cls: "card", size: 44, w: Z.w - 80, rot: k % 2 ? .8 : -.8 }); r.style.textAlign = "center";
      r.style.left = (cx - r.offsetWidth / 2) + "px"; const ti = at(it.at, t + .6 + k * .8); popIn(r, ti);
      if (it.hot) hotLine(r, ti + .3);
      y += r.offsetHeight + 22;
    });
    return h;
  };
  const L = col("left", 520, -1.5), R = col("right", 1400, 1.5);
  if (p.verdict) {
    const target = p.verdict.side === "right" ? R : L, t = at(p.verdict.at, D - 1.5);
    if (target) hotLine(target, t);
    if (p.verdict.text) { const vx = p.verdict.side === "right" ? 1400 : 520, v = box(p.verdict.text, { cx: vx, y: Z.vy, size: Z.vs });
      v.classList.add("hot"); v.style.fontWeight = 800; recentre(v, vx); popIn(v, t + .2); }
  }
};
