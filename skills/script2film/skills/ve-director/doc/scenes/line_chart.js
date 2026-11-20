// line_chart — a trend: rises and falls, highs and lows. The line draws as far as
// the narration has got; comparing single years is still bars.
// p.labels [..] (2-24; at most 8 shown, evenly picked, first and last always) · p.series [{name, values, color}] (1-3;
//   color accent | fg | accent2 | up | down, default in that order) · p.reveal [{upto, at}] (draw to point upto, 0-based,
//   inclusive; 0.6 s each; without it the whole line draws from 0.4 s over 1.2 s) · p.marks [{i, series, text, at}] (at most
//   4 small cards on a point) · p.band {from, to, label, at} (a tinted stretch) · p.min / p.max (default: data range ± 8%) ·
//   p.unit · p.hot (point drawn red, series 0) · p.title (card, centred on top)
// Plot area x 280-1560, y 250-770 (labels end near y 850; the bottom 200 px stay free for subtitles). Enlarged
// 2026-11-13 together with bars (trial film: the charts and their words read small).
SCENES.line_chart = p => {
  const base = 770, top = 250, x0 = 280, x1 = 1560, labels = p.labels, n = labels.length, unit = p.unit || "";
  const MUST = cv("--must") || FG, INK = { accent: RED, fg: FG, accent2: MUST, up: UP, down: DOWN };
  const all = p.series.flatMap(s => s.values), dlo = Math.min(...all), dhi = Math.max(...all), pad = (dhi - dlo) * .08 || Math.abs(dhi) * .08 || 1;
  const lo = p.min ?? dlo - pad, hi = p.max ?? dhi + pad;
  const X = i => x0 + i * (x1 - x0) / (n - 1), Yv = v => base - (v - lo) / (hi - lo) * (base - top);
  draw(stroke(`M 220 ${base} L 1640 ${base}`, 4, FG, .7), .05, .5);
  if (p.title) popIn(box(p.title, { cx: 960, y: 76, cls: "card", size: 60, rot: -1 }), .2);
  if (p.band) {
    const bt = at(p.band.at, .3), r = el("rect", { x: X(p.band.from), y: top, width: X(p.band.to) - X(p.band.from), height: base - top, fill: MUST, opacity: 0 });
    tl.to(r, { opacity: .18, duration: .4 }, bt);
    if (p.band.label) { const l = box(p.band.label, { cx: (X(p.band.from) + X(p.band.to)) / 2, y: top - 52, size: 38 });
      l.style.color = cv("--muted") || FG; popIn(l, bt); }
  }
  const step = n <= 8 ? 1 : (n - 1) / 7, pick = new Set(Array.from({ length: Math.min(n, 8) }, (_, k) => Math.round(k * step)));
  [...pick].forEach(i => popIn(box(labels[i], { cx: X(i), y: base + 18, size: 46, cls: "xlab" }), .3));
  // reveals: [{upto, t}] in order; each takes 0.6 s; without p.reveal one draw of the whole line
  const reveals = (p.reveal || []).map(r => ({ upto: r.upto, t: at(r.at, .4) }));
  const end = reveals.length ? reveals[reveals.length - 1].t + .6 : 1.6;
  const reached = i => { const r = reveals.find(r => r.upto >= i); return r ? r.t + .6 : end; };
  p.series.forEach((s, k) => {
    const ink = INK[s.color || ["accent", "fg", "accent2"][k]], pts = s.values.map((v, i) => [X(i), Yv(v)]);
    const path = stroke(polyPath(pts), 9, ink, 1); path.setAttribute("class", "series");
    const len = path.getTotalLength(), seg = pts.slice(1).map((q, i) => Math.hypot(q[0] - pts[i][0], q[1] - pts[i][1]));
    const sum = seg.reduce((a, c) => a + c, 0), upTo = u => seg.slice(0, u).reduce((a, c) => a + c, 0) / sum;
    if (!reveals.length) draw(path, .4, 1.2);
    reveals.forEach(r => {
      if (r.upto === n - 1) draw(path, r.t, .6);
      else tl.to(path, { strokeDashoffset: len * (1 - upTo(r.upto)), duration: .6, ease: "power2.inOut" }, r.t);
    });
    const last = reveals.length ? reveals[reveals.length - 1].upto : n - 1, [lx, ly] = pts[last];
    const tail = box(`<span class="num" style="color:${ink}">${s.values[last]}${unit}</span>`, { x: lx + 24, y: ly - 36, size: 72, cls: "tail" });
    popIn(tail, end);
    if (k === 0 && p.hot != null) { const h = dot(pts[p.hot][0], pts[p.hot][1], 16, RED); gsap.set(h, { scale: 0 });
      tl.to(h, { scale: 1, duration: .3, ease: "back.out(2)" }, reached(p.hot)); }
  });
  reveals.forEach(r => sfx("reveal", r.t + .6));
  if (!reveals.length) sfx("reveal", 1.6);
  (p.marks || []).forEach(m => {
    const s = p.series[m.series || 0], x = X(m.i), y = Yv(s.values[m.i]), t = at(m.at, reached(m.i));
    const d = dot(x, y, 11, FG); gsap.set(d, { scale: 0 }); tl.to(d, { scale: 1, duration: .25 }, t);
    popIn(box(m.text, { cx: x, y: y - 136, cls: "card", size: 40 }), t);
  });
};
