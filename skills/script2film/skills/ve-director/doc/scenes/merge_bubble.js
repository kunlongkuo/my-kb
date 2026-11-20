// merge_bubble — one company swallows another: bubble A appears, bubble B appears beside it, B is pulled into A and
// stays inside as a smaller nested bubble; an optional price tag pops under them.
// p.a / p.b {name, sub, color} · p.a_at · p.b_at · p.merge_at · p.value {text, at} (big red figure under the bubbles)
SCENES.merge_bubble = p => {
  const A = p.a || {}, B = p.b || {}, ta = at(p.a_at, .2), tb = at(p.b_at, ta + .8), tm = at(p.merge_at, tb + 1);
  const bubble = (o, d, col) => {
    const b = box(`<div class="bname">${o.name || ""}</div><div class="bsub">${o.sub || ""}</div>`, { x: 0, y: 0 });
    Object.assign(b.style, { width: d + "px", height: d + "px", borderRadius: "50%", display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center", textAlign: "center", color: "#fff",
      background: `radial-gradient(circle at 35% 30%, ${col}ee, ${col}99 60%, ${col}55)`,
      boxShadow: `0 0 60px ${col}88, inset 0 0 40px rgba(255,255,255,.18)` });
    b.querySelector(".bname").style.cssText = `font-family:var(--font-big);font-weight:900;font-size:${Math.round(Math.min(d / 6, d * .78 / Math.max(1, [...(o.name || "")].length)))}px;line-height:1.1`;
    b.querySelector(".bsub").style.cssText = `font-size:${Math.round(d / 16)}px;opacity:.8;margin-top:8px`;
    return b;
  };
  const DA = 520, DB = 340, ax = 960 - DA / 2, ay = 220;
  const a = bubble(A, DA, A.color || "#7b3fe4"), b = bubble(B, DB, B.color || "#2f6fe0");
  Object.assign(a.style, { left: ax + "px", top: ay + "px", zIndex: 22 });
  Object.assign(b.style, { left: (ax + DA + 80) + "px", top: (ay + (DA - DB) / 2) + "px", zIndex: 23 });
  tl.fromTo(a, { opacity: 0, scale: .6 }, { opacity: 1, scale: 1, duration: .6, ease: "power2.out", immediateRender: false }, ta);
  tl.fromTo(b, { opacity: 0, scale: .6 }, { opacity: 1, scale: 1, duration: .5, ease: "power2.out", immediateRender: false }, tb);
  // swallow: B travels into A's lower half and shrinks to a nested bubble (scale is about its centre, so left = 960 - DB / 2 centres it)
  tl.to(b, { left: (960 - DB / 2) + "px", top: (ay + DA * .62 - DB / 2) + "px", scale: .55, duration: .9, ease: "power2.inOut" }, tm);
  tl.to(a.querySelector(".bname"), { y: -DA * .18, duration: .9, ease: "power2.inOut" }, tm);
  tl.to(a.querySelector(".bsub"), { y: -DA * .18, duration: .9, ease: "power2.inOut" }, tm);
  tl.to(a, { scale: 1.06, duration: .25, yoyo: true, repeat: 1, ease: "power1.inOut" }, tm + .8);
  let v = null;
  if (p.value) {
    v = box(`<span class="num hot">${p.value.text}</span>`, { cx: 960, y: ay + DA + 40, size: 84 });
    popIn(v, at(p.value.at, tm + 1));
  }
  // p.badge {at, s, x, y}: the merged pair shrinks into a corner badge (doc.json "sticker" keeps it on the next beats).
  // Each bubble scales about its own centre, so its new centre is T + (centre - G) * s, G = the pair's centre.
  if (p.badge) {
    const tb2 = at(p.badge.at, tm + 1.6), s = p.badge.s || .32, Tx = p.badge.x ?? 123, Ty = p.badge.y ?? 123, G = ay + DA / 2;
    if (v) tl.to(v, { opacity: 0, duration: .2 }, tb2);
    tl.to(a, { left: (Tx - DA / 2) + "px", top: (Ty - DA / 2) + "px", scale: s, duration: .55, ease: "power3.inOut" }, tb2);
    tl.to(b, { left: (Tx - DB / 2) + "px", top: (Ty + (DA * .62 - DA / 2) * s - DB / 2) + "px", scale: .55 * s,
               duration: .55, ease: "power3.inOut" }, tb2);
  }
};
