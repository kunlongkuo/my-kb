// relation — who (or what) is tied to whom: name cards appear as each is said, then the ties between them draw in, each with
// a short label; a focus can dim everything except the ones that matter. For people (a family, two camps, a teacher and his
// pupils) and for things (a cause and its effects, a company and its subsidiaries): a family tree or an org chart that
// builds, lines that connect portraits. Not for a path through time (timeline), a place (map_route) or a thing that
// travels (flow).
// p.nodes [{id, label, sub, at, hot, src, x, y}] — label: the name; sub: one short line under it (a role, 「王上 1:7」);
//   at: when it appears (default: one after another from 0.3 s); hot: red; src: a round picture above the name (VE still);
//   x / y: the card's centre (1920×1080; keep y 120-820 so the subtitles stay clear) — or leave them out and give p.rows
// p.rows [[id, ...], ...] — automatic layout, top row first: each row spread evenly across the frame (a family tree)
// p.links [{from, to, kind, label, at, hot}] — kind: "tree" (elbow down from parent to child; children of one parent share
//   one bracket), "line" (straight, default), "dash" (a tie that is broken or refused: dashed), "arrow" (one way);
//   label: a small tag at the middle; at: when it draws (default: just after the later of its two cards); hot: red
// p.focus {ids: [...], at} — everything else dims to a quarter · p.title (card top-left) · p.note (small caption bottom-right)
// p.look "board": a clue board — dark cork ground, the cards are paper notes pinned at the top, pictures are instant photos,
// the ties are red string pinned note to note, sagging a little ("dash": dashed string). Same layout and checks.
const BOARD_INK = "#2a2018", BOARD_PAPER = "#f6efdc", BOARD_STRING = "#c0281e";
SCENES.relation = p => {
  drift(p, 1.05);
  if (!document.getElementById("relcss")) { const st = document.createElement("style"); st.id = "relcss"; st.textContent =
    ".rname{font-family:var(--font-big);font-weight:900;font-size:1.25em;line-height:1.15}.rsub{font-size:.62em;opacity:.75;margin-top:4px}" +
    ".rpic{width:150px;height:150px;border-radius:50%;margin:4px auto 10px;background-size:cover;background-position:50% 30%;border:4px solid}";
    document.head.appendChild(st); }
  const BOARD = p.look === "board";
  if (BOARD && !document.getElementById("boardcss")) { const st = document.createElement("style"); st.id = "boardcss"; st.textContent =
    ".board-note{background:" + BOARD_PAPER + ";color:" + BOARD_INK + ";box-shadow:0 8px 16px rgba(0,0,0,.45)}" +
    ".board-note .rpic{border-radius:2px;border:10px solid #fbfbf6;border-bottom-width:28px;box-shadow:0 3px 8px rgba(0,0,0,.35)}" +
    ".board-pin{position:absolute;left:50%;top:-12px;width:26px;height:26px;margin-left:-13px;border-radius:50%;" +
    "background:radial-gradient(circle at 35% 35%,#ff8a7a,#b3261e 55%,#6e140f);box-shadow:0 3px 4px rgba(0,0,0,.5)}";
    document.head.appendChild(st);
    const g = document.createElement("div"); g.className = "full"; CONTENT.prepend(g);
    Object.assign(g.style, { zIndex: 1, border: "18px solid #3b2816", boxShadow: "inset 0 0 120px rgba(0,0,0,.55)",
      backgroundColor: "#7a5a3a", backgroundImage: "radial-gradient(rgba(40,24,10,.35) 1.4px, transparent 1.6px), " +
      "radial-gradient(rgba(255,220,170,.12) 1.2px, transparent 1.5px)", backgroundSize: "9px 9px, 13px 13px",
      backgroundPosition: "0 0, 4px 6px" });
    tl.fromTo(g, { opacity: 0 }, { opacity: 1, duration: .4, immediateRender: false }, 0);
  }
  const N = {}, nodes = p.nodes || [], rows = p.rows || [];
  rows.forEach((r, ri) => r.forEach((id, k) => {
    const n = nodes.find(o => o.id === id); if (!n || n.x != null) return;
    n._row = ri;
    const y0 = p.title ? 250 : 190, y1 = 720;
    n.x = 960 + (k - (r.length - 1) / 2) * Math.min(520, 1500 / Math.max(1, r.length - 1 || 1));
    n.y = rows.length === 1 ? 470 : y0 + ri * (y1 - y0) / (rows.length - 1);
  }));
  if (p.title) popIn(box(p.title, { x: 90, y: 70, cls: "card", size: 44, rot: -1 }), at(p.title_at, .1));
  nodes.forEach((n, k) => {
    const t = at(n.at, .3 + k * .5), col = n.hot ? RED : BOARD ? BOARD_INK : FG;
    const pic = n.src ? `<div class="rpic" style="background-image:url('${n.src}');border-color:${col}"></div>` : "";
    const b = box(`${pic}<div class="rname" style="color:${col}">${n.label}</div>${n.sub ? `<div class="rsub">${n.sub}</div>` : ""}`,
                  { cx: n.x, y: 0, cls: BOARD ? "card board-note" : "card", size: n.src ? 40 : 46, rot: (k % 3 - 1) * 1.2 });
    if (BOARD) { const pin = document.createElement("div"); pin.className = "board-pin"; b.appendChild(pin);
      gsap.set(b, { rotation: (k % 3 - 1) * 2.2 }); }
    b.style.textAlign = "center"; b.style.top = (n.y - b.offsetHeight / 2) + "px"; b.style.left = (n.x - b.offsetWidth / 2) + "px";
    if (n.hot) b.style.outline = `4px solid ${RED}`;
    popIn(b, t); sfx(n.hot ? "pop" : "paper", t);
    N[n.id] = { n, b, t, w: b.offsetWidth, h: b.offsetHeight };
  });
  // A row laid out by p.rows whose cards are too wide for the even spread above (three long English labels: 2026-11-17)
  // is re-spread by the cards' measured widths, 40 px apart, centred; a row that spreads fine keeps its places.
  rows.forEach((r, ri) => {
    const cs = r.map(id => N[id]).filter(o => o && o.n._row === ri);
    if (!cs.some((o, k) => k && o.n.x - cs[k - 1].n.x < (o.w + cs[k - 1].w) / 2 + 40)) return;
    let x = 960 - (cs.reduce((s, o) => s + o.w, 0) + 40 * (cs.length - 1)) / 2;
    cs.forEach(o => { o.n.x = x + o.w / 2; o.b.style.left = x + "px"; x += o.w + 40; });
  });
  // doc_code.py reads these after the build and stops on cards that overlap or run off the frame (2026-11-17)
  window.__relcards = Object.values(N).map(o => [o.n.id, o.b.offsetLeft, o.b.offsetTop, o.w, o.h]);
  const edge = (a, c) => {                 // the point on a card's border towards another point
    const dx = c.n.x - a.n.x, dy = c.n.y - a.n.y, hw = a.w / 2 + 10, hh = a.h / 2 + 10;
    const s = Math.min(hw / Math.abs(dx || 1e-6), hh / Math.abs(dy || 1e-6));
    return [a.n.x + dx * s, a.n.y + dy * s];
  };
  const tagAt = (x, y, text, col, t) => {
    const g = box(text, { cx: x, y: y - 26, size: 30 });
    Object.assign(g.style, { background: col === RED ? RED : BOARD ? BOARD_PAPER : "var(--bg-solid, #f4ecd8)",
      color: col === RED ? "#fff" : BOARD ? BOARD_INK : FG,
      padding: "4px 14px", borderRadius: "999px", border: `2px solid ${col}`, zIndex: 23 });
    g.style.left = (x - g.offsetWidth / 2) + "px"; popIn(g, t + .25);
  };
  const LINKS = [];
  (p.links || []).forEach(l => {
    const A = N[l.from], C = N[l.to]; if (!A || !C) return;
    const t = at(l.at, Math.max(A.t, C.t) + .25), col = BOARD ? BOARD_STRING : l.hot ? RED : FG, kind = l.kind || "line";
    let d, mx, my;
    if (BOARD && kind !== "tree") {         // string from pin to pin, sagging by a tenth of its length
      const x0 = A.n.x, y0 = A.n.y - A.h / 2 + 1, x1 = C.n.x, y1 = C.n.y - C.h / 2 + 1, sag = Math.hypot(x1 - x0, y1 - y0) * .1;
      d = arc(x0, y0, x1, y1, sag); mx = (x0 + x1) / 2; my = (y0 + y1) / 2 + sag / 2;
      if (kind === "arrow") {                // the head on the pin, pointing along the last stretch
        const ang = Math.atan2(y1 - ((y0 + y1) / 2 + sag), x1 - (x0 + x1) / 2), h = 26, a1 = ang + 2.6, a2 = ang - 2.6;
        d += ` M ${x1} ${y1} L ${x1 + h * Math.cos(a1)} ${y1 + h * Math.sin(a1)} M ${x1} ${y1} L ${x1 + h * Math.cos(a2)} ${y1 + h * Math.sin(a2)}`;
      }
    } else if (kind === "tree") {
      const y0 = A.n.y + A.h / 2 + 8, y1 = C.n.y - C.h / 2 - 8, ym = (y0 + y1) / 2;
      d = `M ${A.n.x} ${y0} L ${A.n.x} ${ym} L ${C.n.x} ${ym} L ${C.n.x} ${y1}`; mx = C.n.x; my = ym;
    } else {
      const [x0, y0] = edge(A, C), [x1, y1] = edge(C, A); d = `M ${x0} ${y0} L ${x1} ${y1}`; mx = (x0 + x1) / 2; my = (y0 + y1) / 2;
      if (kind === "arrow") {
        const ang = Math.atan2(y1 - y0, x1 - x0), h = 26, a1 = ang + 2.6, a2 = ang - 2.6;
        d += ` M ${x1} ${y1} L ${x1 + h * Math.cos(a1)} ${y1 + h * Math.sin(a1)} M ${x1} ${y1} L ${x1 + h * Math.cos(a2)} ${y1 + h * Math.sin(a2)}`;
      }
    }
    const s = stroke(d, l.hot ? 6 : 4.5, col, BOARD ? .95 : .85);
    if (BOARD) s.parentNode.parentNode.style.zIndex = 23;   // the string runs over the notes, to their pins
    if (kind === "dash") {                 // draw it, then switch to dashes (a dasharray cannot both draw and dash)
      draw(s, t, .5); tl.set(s, { attr: { "stroke-dasharray": "14 12", "stroke-dashoffset": 0 } }, t + .52);
    } else draw(s, t, kind === "tree" ? .6 : .45);
    sfx("marker", t);
    if (l.label) tagAt(mx, my, l.label, col, t);
    LINKS.push({ l, s });
  });
  if (p.focus) {
    const keep = new Set(p.focus.ids || []), t = at(p.focus.at, D - TAIL - 2);
    Object.values(N).forEach(o => { if (!keep.has(o.n.id)) tl.to(o.b, { opacity: .25, duration: .5 }, t); });
    LINKS.forEach(({ l, s }) => { if (!(keep.has(l.from) && keep.has(l.to))) tl.to(s, { opacity: .15, duration: .5 }, t); });
  }
  if (p.note) { const c = box(p.note, { x: 0, y: 830, size: 28 }); c.style.left = (1830 - c.offsetWidth) + "px"; c.style.opacity = 0;
    tl.to(c, { opacity: .7, duration: .5 }, at(p.note_at, .8)); }
  overlays(p);
};
