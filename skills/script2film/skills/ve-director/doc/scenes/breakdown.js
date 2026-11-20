// breakdown — one quantity split into its parts (利潤 = 收入 − 成本): the root on
// top, the parts in a row under it, each with its operator in front of its value, optionally a second level under any part.
// p.root {text, value, at} · p.parts [{text, value, op, at, hot, parts}] (2-5; op + − × ÷ on every part but the first;
//   parts: a second level of 2-3, same op rule, at most 6 in all, no third level) · p.unit (after every printed value;
//   only items with a value print one) · p.focus [{id, at}] (id "1" = second part, "1.0" = its first child: it and its
//   path to the root stay lit, the rest dim to .25) · p.title (card top-left)
// Card centres, two levels: root y 190, first level y 470 spread as relation rows, second level y 715 under its parent
// (x = parent + (j − (m−1)/2) × c, c = min(230, S / m), S the first level's spacing; card width c − 20). One level only:
// root y 270 and the parts y 600, both larger, so the tree fills the frame above the subtitles (2026-11-13, trial film:
// it sat in the top half and read small). Root and first-level cards have a fixed width too: a card sized by its text is
// placed before the web font loads and lands a few px off its branch once it does.
// The operator is printed in the card, in front of the value (−60萬), or in front of the name when the part has no
// value. Until 2026-11-13 it was a round stamp on the branch: on the drop it covered the short segment and the branch
// looked cut off before the card, on the bar it read as odd (trial film, twice). Branches touch both cards.
SCENES.breakdown = p => {
  if (!document.getElementById("bdcss")) { const st = document.createElement("style"); st.id = "bdcss"; st.textContent =
    ".bname{font-family:var(--font-big);font-weight:900;font-size:1.15em;line-height:1.15}.bnode .num{font-size:1.05em;margin-top:6px}";
    document.head.appendChild(st); }
  const unit = p.unit || "", parts = p.parts, n = parts.length, S = Math.min(520, 1500 / (n - 1));
  if (p.title) popIn(box(p.title, { x: 90, y: 70, cls: "card", size: 52, rot: -1 }), at(p.title_at, .1));
  const NODE = {}, ELS = [];   // NODE[id] = {x, y, b, els: [indexes into ELS], up: parent id}
  const card = (id, it, x, y, size, w, t, up) => {
    const col = it.hot ? RED : FG, op = it.op || "", val = it.value != null ? `<div class="num">${op}${it.value}${unit}</div>` : "";
    const b = box(`<div class="card bnode" style="text-align:center"><div class="bname" style="color:${col}">${val ? "" : op}${it.text}</div>${val}</div>`,
                  { cx: x, y: 0, size, w, cls: "node" });
    b.dataset.id = id; b.style.top = (y - b.offsetHeight / 2) + "px"; b.style.left = (x - b.offsetWidth / 2) + "px";
    if (it.hot) b.firstChild.style.outline = `4px solid ${RED}`;
    popIn(b, t); sfx(it.hot ? "pop" : "paper", t);
    NODE[id] = { x, y, b, t, up, els: [ELS.push(b.firstChild) - 1] };
    return NODE[id];
  };
  // a parent's children hang from one bar; each child's branch draws as it is said, from the parent's edge to the child's
  const branch = (P, kids) => {
    const y0 = P.b.offsetTop + P.b.offsetHeight, y1 = Math.min(...kids.map(([C]) => C.b.offsetTop)), ym = (y0 + y1) / 2;
    kids.forEach(([C, it]) => {
      const s = stroke(`M ${P.x} ${y0} L ${P.x} ${ym} L ${C.x} ${ym} L ${C.x} ${C.b.offsetTop}`, 4.5, it.hot ? RED : FG, .85);
      draw(s, C.t, .45); sfx("marker", C.t); C.els.push(ELS.push(s) - 1);
    });
  };
  const deep = parts.some(it => it.parts), wide = S >= 500;   // wide: 2-4 parts, room for larger words
  const R = card("root", p.root, 960, deep ? 190 : 270, deep ? 72 : 84, deep ? 480 : 600, at(p.root.at, .3), null);
  const first = parts.map((it, k) => [card(String(k), it, 960 + (k - (n - 1) / 2) * S, deep ? 470 : 600,
    wide ? (deep ? 64 : 76) : 58, Math.min(S - 40, 460), at(it.at, .9 + k * .6), "root"), it]);
  branch(R, first);
  first.forEach(([P, it], k) => {
    if (!it.parts) return;
    const m = it.parts.length, c = Math.min(230, S / m);
    const kids = it.parts.map((ch, j) => [card(`${k}.${j}`, ch, P.x + (j - (m - 1) / 2) * c, 715, 46, c - 20, at(ch.at, P.t + .4 + j * .4), String(k)), ch]);
    branch(P, kids);
  });
  (p.focus || []).forEach(f => {
    const keep = [];
    for (let id = f.id; id; id = NODE[id].up) keep.push(...NODE[id].els);
    focusDim(ELS, keep, at(f.at, D - TAIL - 1.5)); sfx("marker", at(f.at, D - TAIL - 1.5));
  });
};
