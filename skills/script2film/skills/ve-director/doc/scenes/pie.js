// pie — what something is made of and how big each share is: a ring (or a solid
// pie) whose slices sweep open as each is said, a legend on the right that comes in with its slice.
// p.items [{label, value, at}] (2-6, value > 0) · p.donut (inner radius share 0-0.7, default 0.55; 0 = solid pie) ·
// p.focus [{i, at}] (slice i moves out 26 px, the rest dim to .25; may be given more than once) · p.show "percent" (default:
// whole percents by largest remainder, so they add to 100) | "value" · p.unit (default "%" with percent) ·
// p.center {text, sub, at} (ring only) · p.hot (slice in the accent) · p.title (card top-left, as relation)
SCENES.pie = p => {
  const cx = 640, cy = 490, R = 300, items = p.items, n = items.length, donut = p.donut ?? .55, r0 = R * donut;
  const MUST = cv("--must") || FG, MUTED = cv("--muted") || FG, show = p.show || "percent";
  const unit = p.unit ?? (show === "percent" ? "%" : "");
  if (p.title) popIn(box(p.title, { x: 90, y: 70, cls: "card", size: 52, rot: -1 }), at(p.title_at, .1));
  // whole percents by largest remainder: floor each, hand the points left over to the largest fractions
  const total = items.reduce((a, it) => a + it.value, 0), raw = items.map(it => it.value / total * 100), pct = raw.map(Math.floor);
  raw.map((v, k) => [v - pct[k], k]).sort((a, b) => b[0] - a[0] || a[1] - b[1]).slice(0, 100 - pct.reduce((a, c) => a + c, 0))
    .forEach(([, k]) => pct[k]++);
  // fills: hot in the accent; the others in turn: accent2, ink at .85 / .6 / .4 / .25, muted
  const SEQ = [[MUST, 1], [FG, .85], [FG, .6], [FG, .4], [FG, .25], [MUTED, 1]];
  let next = 0;
  const fills = items.map((_, k) => k === p.hot ? [RED, 1] : SEQ[next++]);
  const G = [], ROWS = [], rowH = 100, ry0 = cy - n * rowH / 2;
  let a = 0, last = 0;
  items.forEach((it, k) => {
    const span = 2 * Math.PI * it.value / total, a0 = a, t = at(it.at, .4 + k * .6), [col, op] = fills[k];
    a += span; last = Math.max(last, t + .5);
    const g = el("g", { class: "sector" }), path = el("path", { class: "slice", d: sectorPath(cx, cy, r0, R, a0, a0), fill: col, "fill-opacity": op }, g);
    const st = { u: 0 };
    tl.to(st, { u: 1, duration: .5, ease: "power2.out", onUpdate: () => path.setAttribute("d", sectorPath(cx, cy, r0, R, a0, a0 + st.u * span)) }, t);
    sfx("paper", t);
    g.mid = a0 + span / 2; G.push(g);
    const shown = show === "percent" ? pct[k] : it.value;
    const row = box(`<div class="lrow" style="display:flex;align-items:center;gap:22px">` +
      `<span style="width:42px;height:42px;border-radius:9px;background:${col};opacity:${op}"></span>` +
      `<span style="font-weight:700">${it.label}</span><span class="num pval"${k === p.hot ? ` style="color:${RED}"` : ""}>${shown}${unit}</span></div>`,
      { x: 1060, y: ry0 + k * rowH, size: 54 });
    popIn(row, t); ROWS.push(row.firstChild);
  });
  (p.focus || []).forEach(f => {
    const t = at(f.at, D - TAIL - 1.5);
    focusDim(G, f.i, t); focusDim(ROWS, f.i, t);
    G.forEach((g, k) => tl.to(g, { x: k === f.i ? 26 * Math.sin(g.mid) : 0, y: k === f.i ? -26 * Math.cos(g.mid) : 0, duration: .3, ease: "power2.out" }, t));
  });
  if (p.center && r0 > 0) {
    const c = box(`<div class="num" style="font-size:78px">${p.center.text}</div>` + (p.center.sub ? `<div style="font-size:34px;margin-top:8px;color:${MUTED}">${p.center.sub}</div>` : ""),
      { cx, y: 0, size: 78 });
    c.style.textAlign = "center"; c.style.top = (cy - c.offsetHeight / 2) + "px"; c.style.left = (cx - c.offsetWidth / 2) + "px";
    popIn(c, at(p.center.at, last));
  }
};
