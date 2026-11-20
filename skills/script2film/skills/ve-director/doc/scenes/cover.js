// cover — a series episode's title card under the spoken opening, laid out right of centre so a round host frame (pip)
// can sit in the lower-left corner. p.series (small label, at p.at) · p.title (the big name) · p.sub (the range, at p.sub_at)
// · p.badge (a red stamp, e.g. the day number, with p.sub) · p.cx (default 1100) · p.size (title, default 190)
SCENES.cover = p => {
  drift(p);
  const t = at(p.at, .15), ts = at(p.sub_at, t + 1), cx = p.cx || 1100;
  const s = box(p.series || "", { cx, y: 270, size: 40 });
  Object.assign(s.style, { fontFamily: "var(--font-ui)", fontWeight: 700, letterSpacing: "8px" });
  s.style.left = (cx - s.offsetWidth / 2) + "px"; popIn(s, t);
  const h = box(p.title, { cx, y: 360, size: p.size || 190, rot: -1 });
  Object.assign(h.style, { fontFamily: "var(--font-big)", fontWeight: 900, lineHeight: 1.1, whiteSpace: "nowrap" });
  // the badge sits right of the title: a long title pushed 「EP1」 off the right edge, so the
  // title shrinks until title + badge fit inside the frame
  const room = 2 * Math.min(cx - 60, 1880 - cx - (p.badge ? 40 + 2 * 92 : 0));
  for (let n = 0; n < 4 && h.offsetWidth > room; n++)
    h.style.fontSize = Math.floor(parseFloat(h.style.fontSize || (p.size || 190)) * room / h.offsetWidth) + "px";
  h.style.left = (cx - h.offsetWidth / 2) + "px"; popIn(h, t + .25); hotLine(h, t + .55);
  if (p.sub) {
    const b = box(p.sub, { cx, y: h.offsetTop + h.offsetHeight + 70, size: 76, cls: "card", rot: 1 });
    Object.assign(b.style, { fontFamily: "var(--font-big)", fontWeight: 800 });
    // a long range (「第 32–33 章、列王紀下 20–21 章、那鴻書 1–3 章」) ran off the right edge:
    // break it at the 、 nearest the middle (a plain wrap left 「章」 alone on line two), then shrink until it fits;
    // maxW (with the card's padding) keeps it inside the frame and clear of the round host frame lower left
    const maxW = 2 * Math.min(cx - 400, 1920 - 120 - cx);
    if (b.offsetWidth > maxW) {
      const cuts = [...p.sub.matchAll(/、/g)].map(m => m.index), mid = p.sub.length / 2;
      if (cuts.length) {
        const k = cuts.reduce((a, c) => Math.abs(c - mid) < Math.abs(a - mid) ? c : a);
        b.innerHTML = p.sub.slice(0, k + 1) + "<br>" + p.sub.slice(k + 1);
      }
      Object.assign(b.style, { textAlign: "center", lineHeight: 1.3, whiteSpace: "nowrap" });
      for (let n = 0; n < 4 && b.offsetWidth > maxW; n++)
        b.style.fontSize = Math.floor(parseFloat(b.style.fontSize) * maxW / b.offsetWidth) + "px";
    }
    b.style.left = (cx - b.offsetWidth / 2) + "px"; popIn(b, ts);
  }
  if (p.badge) {
    const r = 92, x = cx + h.offsetWidth / 2 + 40, y = h.offsetTop + 10;
    // gsap rewrites a <g>'s transform attribute when it scales it: keep the placement on an outer group
    const g = el("g", {}, el("g", { transform: `translate(${x} ${y}) rotate(-8)` }));
    el("circle", { r, fill: RED }, g);   // no bleed: its displacement pulls the disc off the text
    const tx = el("text", { "text-anchor": "middle", "dominant-baseline": "central", fill: "#fff", "font-size": 46,
                            "font-weight": 900, "font-family": "var(--font-big)" }, g);
    tx.textContent = p.badge;
    gsap.set(g, { scale: 0, svgOrigin: "0 0" });
    tl.set(g, { scale: 1.4 }, ts + .4); tl.to(g, { scale: 1, duration: .3, ease: TORN ? "steps(4)" : "back.out(2)" }, ts + .4);
  }
};
