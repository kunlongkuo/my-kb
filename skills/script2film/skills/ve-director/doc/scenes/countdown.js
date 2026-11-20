// countdown — a clock running from 0 to how long something took, a bar draining under it; the end lands in red.
// For a reconstruction (e.g. 0:00 → 3:24 授權生效到錢包被掃空).
// p.value (seconds the event took) · p.from (default 0) · p.label (small line above, e.g. "授權生效（分:秒）") · p.at (clock
// starts) · p.dur (seconds the clock runs on screen, default 3) · p.hot (default true: the final value turns red) ·
// p.bar (default true) · p.caption / p.caption_at (one line under the bar, after the clock stops)
SCENES.countdown = p => {
  drift(p);
  const t0 = at(p.at, .3), run = p.dur || 3, end = t0 + run, x = 300;
  const fmt = s => { s = Math.round(s); const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), r = String(s % 60).padStart(2, "0");
    return h ? `${h}:${String(m).padStart(2, "0")}:${r}` : `${m}:${r}`; };
  if (p.label) { const l = box(p.label, { x, y: 260, size: 44 }); l.style.fontWeight = 700; popIn(l, Math.max(0, t0 - .3)); }
  const n = box(`<span class="num">${fmt(p.value)}</span>`, { x, y: 330, size: 300 }), span = n.firstChild, o = { v: p.from || 0 };
  span.textContent = fmt(o.v); popIn(n, t0);
  tl.to(o, { v: p.value, duration: run, ease: "none", onUpdate: () => { span.textContent = fmt(o.v); } }, t0);
  if (p.hot !== false) tl.call(() => span.classList.add("hot"), null, end);
  sfx("reveal", end);
  if (p.bar !== false) {
    const W = 1100, rim = document.createElement("div"), fill = document.createElement("div");
    fill.className = "cd-fill"; CONTENT.appendChild(rim); rim.appendChild(fill);
    Object.assign(rim.style, { position: "absolute", left: x + "px", top: "700px", width: W + "px", height: "34px",
      border: `4px solid ${FG}`, opacity: 0 });
    Object.assign(fill.style, { position: "absolute", inset: "4px", background: FG, transformOrigin: "100% 50%" });
    tl.to(rim, { opacity: 1, duration: .3 }, t0);
    tl.fromTo(fill, { scaleX: 1 }, { scaleX: 0, duration: run, ease: "none" }, t0);
  }
  if (p.caption) { const c = box(p.caption, { x, y: 790, cls: "card", size: 44, rot: -1 }); c.style.fontWeight = 700;
    popIn(c, at(p.caption_at, end + .3)); }
};
