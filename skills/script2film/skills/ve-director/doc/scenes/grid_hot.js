// grid_hot — many numbered cells appear one after another, then one of them turns red and the rest dim.
// For a reconstruction (e.g. 一筆交易 50 張授權，生效的是第 17 張).
// p.count (2-100 cells) · p.cols (default 10) · p.title (line above the grid) · p.at (cells start) · p.stagger (seconds for
// all cells to appear, default 1.2) · p.hot (1-based cell to mark) · p.hot_at (when it turns red; default 0.8 s after the
// last cell) · p.fmt ("#{n}" by default; {n} is zero-padded to the count's width) · p.caption / p.caption_at
SCENES.grid_hot = p => {
  drift(p);
  const N = Math.max(2, Math.min(p.count || 50, 100)), C = Math.min(p.cols || 10, N), R = Math.ceil(N / C);
  const gap = 14, cw = Math.min(150, Math.floor((1560 - gap * (C - 1)) / C)), ch = Math.round(cw * .58);
  const top = p.title ? 330 : 280, left = 960 - (C * cw + (C - 1) * gap) / 2, w = String(N).length;
  const t0 = at(p.at, .3), st = (p.stagger || 1.2) / N, fmt = p.fmt || "#{n}";
  if (p.title) { const h = box(p.title, { cx: 960, y: top - 110, size: 52 }); h.style.fontWeight = 800; recentre(h, 960); popIn(h, Math.max(0, t0 - .3)); }
  const cells = [];
  for (let k = 0; k < N; k++) {
    const c = document.createElement("div"); c.className = "cell"; CONTENT.appendChild(c); cells.push(c);
    c.textContent = fmt.replace("{n}", String(k + 1).padStart(w, "0"));
    Object.assign(c.style, { position: "absolute", left: left + (k % C) * (cw + gap) + "px", top: top + Math.floor(k / C) * (ch + gap) + "px",
      width: cw + "px", height: ch + "px", lineHeight: ch + "px", textAlign: "center", fontSize: Math.round(ch * .42) + "px",
      fontVariantNumeric: "tabular-nums", color: FG, border: `3px solid ${FG}`, boxSizing: "border-box", opacity: 0 });
    tl.to(c, { opacity: 1, duration: .15 }, t0 + k * st);
  }
  const th = at(p.hot_at, t0 + N * st + .8);
  if (p.hot) {
    const hk = Math.max(1, Math.min(p.hot, N)) - 1;
    tl.to(cells.filter((_, k) => k !== hk), { opacity: .18, duration: .4 }, th);
    tl.to(cells[hk], { backgroundColor: RED, borderColor: RED, color: "#fff", scale: 1.25, duration: .25, ease: "back.out(2)" }, th);
    sfx("reveal", th);
  }
  if (p.caption) { const cy = top + R * (ch + gap) + 40, c = box(p.caption, { cx: 960, y: cy, cls: "card", size: 44, rot: -1 });
    c.style.fontWeight = 700; recentre(c, 960); popIn(c, at(p.caption_at, th + .4)); }
};
