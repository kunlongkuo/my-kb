// bars — a bar chart; each bar grows as its label is said, value printed on top. Same frame as line_chart (baseline y 770,
// tallest bar to y 330 so its value clears the title, x 280-1640; enlarged 2026-11-13 with the other charts: they and their words read small).
// p.items: [{label, value, at, dir}] (2-6; dir "up" / "down" colours a market move, see doc.json "rise") · p.max (default: largest value) · p.hot: index drawn in red · p.unit ("%", "") · p.title
SCENES.bars = p => {
  const items = p.items, max = p.max || Math.max(...items.map(i => i.value)), base = 770, top = 330, n = items.length;
  const w = Math.min(210, 1020 / n), gap = (1360 - n * w) / Math.max(1, n - 1), x0 = 280;
  draw(stroke(`M 220 ${base} L 1700 ${base}`, 4, FG, .7), .05, .5);
  if (p.title) popIn(box(p.title, { cx: 960, y: 76, cls: "card", size: 60, rot: -1 }), .2);
  items.forEach((it, k) => {
    const x = x0 + k * (w + gap), h = (base - top) * it.value / max, t = at(it.at, .6 + k * .7), hot = k === p.hot;
    const ink = it.dir === "up" ? UP : it.dir === "down" ? DOWN : hot ? RED : FG;
    const r = el("rect", { x, y: base, width: w, height: 0, fill: ink, opacity: hot || it.dir ? 1 : .8, filter: "url(#bleed)" });
    tl.to(r, { attr: { y: base - h, height: h }, duration: .6, ease: TORN ? "steps(6)" : "power2.out" }, t);
    const v = box(`<span class="num${hot ? " hot" : ""}"${it.dir ? ` style="color:${ink}"` : ""}>${it.value}${p.unit || ""}</span>`, { cx: x + w / 2, y: base - h - 118, size: 72 }); popIn(v, t + .5);
    const l = box(it.label, { cx: x + w / 2, y: base + 18, size: 46 }); popIn(l, t);
  });
};
