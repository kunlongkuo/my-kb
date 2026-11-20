// stat_count — one number that matters, counting up as it is said, with a label under it.
// p.value (number) · p.from (default 0) · p.decimals · p.prefix / p.suffix ("%", " 年") · p.caption · p.at (count starts) ·
// p.dur (count seconds, default 1.2) · p.hot (true: number in the accent red) · p.caption_at
// p.slam: the number lands at its final value on p.at (slamIn) instead of counting up, for the few numbers the film turns on
SCENES.stat_count = p => {
  drift(p);
  const t0 = at(p.at, .3), dec = p.decimals || 0, fmt = v => (p.prefix || "") + v.toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec }) + (p.suffix || "");
  const n = box(`<span class="num${p.hot ? " hot" : ""}">${fmt(p.value)}</span>`, { cx: 960, y: 290, size: p.size || 260 });
  n.style.left = (960 - n.offsetWidth / 2) + "px";           // width measured with the final value
  const span = n.firstChild, o = { v: p.from || 0 };
  if (p.slam) slamIn(n, t0);
  else {
    span.textContent = fmt(o.v); popIn(n, t0);
    tl.to(o, { v: p.value, duration: p.dur || 1.2, ease: "power2.out", onUpdate: () => { span.textContent = fmt(dec ? o.v : Math.round(o.v)); } }, t0);
    sfx("reveal", t0 + (p.dur || 1.2));
  }
  if (p.caption) { const l = box(p.caption, { cx: 960, y: 600, cls: "card", size: 44, rot: -1 }); l.style.fontWeight = 700; recentre(l, 960); popIn(l, at(p.caption_at, t0 + .5)); }
};
