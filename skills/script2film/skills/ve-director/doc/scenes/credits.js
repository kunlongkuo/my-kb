// credits — the closing page: a heading, then groups of credit lines rolling up like film end credits:
// every source that needs a credit goes here. Put it on the lines where the host says where the facts came from.
// p.title · p.groups: [{head, lines: [text]}] · p.at (roll starts, default 0.3) · p.x (column centre, default 1060: clear of a
// lower-left pip host)
SCENES.credits = p => {
  const cx = p.x || 1060, t0 = at(p.at, .3);
  if (p.title) { const h = box(p.title, { cx, y: 70, size: 50 }); h.style.fontWeight = 800; recentre(h, cx); popIn(h, .1); }
  const col = document.createElement("div");
  Object.assign(col.style, { position: "absolute", left: (cx - 560) + "px", width: "1120px", top: "0px", textAlign: "center", opacity: 0 });
  col.innerHTML = (p.groups || []).map(g =>
    `<div style="margin:0 0 26px"><div style="font-size:28px;font-weight:800;color:${RED};margin-bottom:6px">${g.head}</div>` +
    g.lines.map(l => `<div style="font-size:26px;line-height:1.45;color:${FG}">${l}</div>`).join("") + "</div>").join("");
  CONTENT.appendChild(col);
  // roll in from below the frame and come to rest under the title, the last line above the subtitle band (y 860) when it fits
  const h = col.offsetHeight, rest = Math.max(160, Math.min(200, 860 - h));
  tl.set(col, { y: 1080, opacity: 1 }, t0);
  tl.to(col, { y: rest, duration: Math.max(1.5, D - TAIL - t0 - .4), ease: "power1.out" }, t0);
};
