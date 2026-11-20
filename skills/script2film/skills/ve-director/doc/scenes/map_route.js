// map_route — a sketch map: faint coastlines first, then a route drawn stop by stop as each place is said.
// p.land: [svg path d, ...] (coasts, rivers; drawn faint at the start) · p.stops: [{name, x, y, at, side: "left" | "right"}]
// p.hot: index of the stop to mark in red · p.title (top-left card) · p.note (small caption, e.g. "路線示意（傳統說法）")
// Keep y within 150-820 so the subtitles stay clear.
// p.base: an old (or modern) map under the route — {src, size: [w, h], crop: [x, y, w, h],
//   kind: "old" | "modern", credit, dim (0-.6, default .15), push (1-1.2, default 1.04)}. With a base, stops and land are pixels on the
//   map image: the crop is fitted into the frame (centred, paper either side when it is taller than 16:9) and every point
//   follows it. The whole picture pushes in on the hot stop (#drift, so the name cards stay on their dots); a modern map
//   says so in the note. doc_build.map_route() fills base and the stops' x / y from the series map library.
SCENES.map_route = p => {
  const B = p.base;
  let X = v => v, Y = v => v, s = 1;
  if (B) {
    const [cx, cy, cw, ch] = B.crop, [W, H] = B.size;
    s = Math.min(1920 / cw, 1080 / ch);
    const ox = (1920 - cw * s) / 2, oy = (1080 - ch * s) / 2;
    X = v => ox + (v - cx) * s; Y = v => oy + (v - cy) * s;
    const g = el("g", {}); svg.insertBefore(g, svg.querySelector("defs").nextSibling);   // under every stroke
    const cp = el("clipPath", { id: "basecrop" }, svg.querySelector("defs"));
    el("rect", { x: ox, y: oy, width: cw * s, height: ch * s }, cp);
    if (cw * s < 1919) el("rect", { x: ox + 6, y: oy + 8, width: cw * s, height: ch * s, fill: "rgba(40,28,14,.22)", filter: "url(#wash)" }, g);
    el("image", { href: B.src, x: X(0), y: Y(0), width: W * s, height: H * s, preserveAspectRatio: "none", "clip-path": "url(#basecrop)" }, g);
    el("rect", { x: ox, y: oy, width: cw * s, height: ch * s, fill: BG, opacity: Math.max(0, Math.min(B.dim ?? .15, .6)) }, g);
    const h = p.stops[p.hot ?? p.stops.length - 1] || p.stops[0];
    gsap.set("#drift", { transformOrigin: `${X(h.x)}px ${Y(h.y)}px` });
    tl.fromTo("#drift", { scale: 1 }, { scale: Math.max(1, Math.min(B.push ?? 1.04, 1.2)), duration: D, ease: "none" }, 0);
    if (B.credit) { const c = box(B.credit, { x: 1560, y: 40, size: 22 }); c.style.opacity = .6; popIn(c, .3); }
  }
  // land: with a base, drawn in map pixels inside a group that maps them onto the frame (strokes keep their width)
  const lg = B ? el("g", { transform: `translate(${X(0)} ${Y(0)}) scale(${s})` }) : null;
  (p.land || []).forEach((d, k) => {
    const st = stroke(d, B ? 5 / s : 5, FG, .35);
    if (lg) lg.appendChild(st);
    draw(st, .05 + k * .08, .6);
  });
  if (p.title) { const h = box(p.title, { x: 120, y: 120, cls: "card", size: 54, rot: -1 }); h.style.fontWeight = 800; popIn(h, .2); }
  const note = B && B.kind === "modern" ? [p.note, "今日位置示意"].filter(Boolean).join("｜") : p.note;
  if (note) { const n = box(note, { x: 1380, y: 800, size: 30 }); n.style.opacity = .7; popIn(n, .4); }
  const stops = p.stops.map(o => ({ ...o, x: X(o.x), y: Y(o.y) }));
  stops.forEach((s, k) => {
    const t = at(s.at, .6 + k * .8), hot = k === p.hot;
    if (k > 0) {   // the leg into this stop draws up to the moment the place is named
      const a = stops[k - 1], bend = (k % 2 ? -1 : 1) * 40;
      const leg = stroke(arc(a.x, a.y, s.x, s.y, bend), 7, RED, .85);
      draw(leg, Math.max(at(a.at, .6 + (k - 1) * .8) + .2, t - .5), .5, "power1.inOut");
    }
    const m = dot(s.x, s.y, hot ? 18 : 12, hot ? RED : FG); gsap.set(m, { scale: 0 });
    tl.to(m, { scale: 1, duration: .3, ease: TORN ? "steps(3)" : "back.out(2)" }, t); sfx("pluck", t);
    const right = s.side !== "left";
    const b = box(s.name, { x: right ? s.x + 30 : s.x - 30, y: s.y - 36, cls: "card", size: 40, rot: k % 2 ? 1 : -1 });
    if (!right) b.style.left = (s.x - 30 - b.offsetWidth) + "px";
    popIn(b, t + .1);
  });
};
