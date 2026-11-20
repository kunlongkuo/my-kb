// timeline — a horizontal line with dated markers appearing as each date is mentioned.
// p.items: [{date: "1950", text: "...", at: phrase}] (2-6) · p.hot: index of the marker to mark in red · p.y (line height, default 520)
// A long line (up to 12 items) shown a few at a time: p.window [first, last] (2-6 items) is what the frame shows at the end;
// p.from [first, last] (as many items) is what it shows first, and at p.pan_at (default 1.0 s) the whole line slides along
// to the window (one series-wide line of eras, each episode on its own stretch). Items in view at the start come in on
// their at (or one after another: 0.8 s apart, 0.2 s with from, a stretch already known that the line leaves); items that slide in are there as they come; the rest are not drawn.
SCENES.timeline = p => {
  drift(p, 1.03);
  if (p.window) return longTimeline(p);   // the row runs close to the frame edges: 1.06 already cuts the outer labels
  const items = p.items, y = p.y || 520, x0 = 260, x1 = 1660, step = (x1 - x0) / Math.max(1, items.length - 1);
  draw(stroke(`M ${x0 - 60} ${y} L ${x1 + 60} ${y}`, 5, FG, .75), .05, .6);
  items.forEach((it, k) => {
    const x = items.length === 1 ? 960 : x0 + k * step, t = at(it.at, .6 + k * .8), hot = k === p.hot;
    const m = dot(x, y, hot ? 18 : 13, hot ? RED : FG); gsap.set(m, { scale: 0 });
    tl.to(m, { scale: 1, duration: .3, ease: TORN ? "steps(3)" : "back.out(2)" }, t);
    // a date never wraps and stays inside the frame (「約公元 200 年」 at the right end lost 「年」 to
    // a second line: box() measures the width first, then the left edge moves right and the line re-wraps)
    const d = box(`<span class="num${hot ? " hot" : ""}" style="white-space:nowrap">${it.date}</span>`, { cx: x, y: y - 150, size: 80 });
    d.style.whiteSpace = "nowrap";
    d.style.left = Math.max(90, Math.min(1830 - d.offsetWidth, x - d.offsetWidth / 2)) + "px"; popIn(d, t);   // 90 px: drift 1.03 pushes the row out
    if (it.text) { const c = box(it.text, { cx: x, y: y + 40, cls: "card", size: 40, w: Math.min(420, step - 20), rot: k % 2 ? 1 : -1 });
      c.style.textAlign = "center"; c.style.left = (x - c.offsetWidth / 2) + "px"; popIn(c, t + .15); }
  });
};
function longTimeline(p) {
  const items = p.items, y = p.y || 520, x0 = 260, x1 = 1660, [a, b] = p.window, [fa, fb] = p.from || p.window;
  const step = (x1 - x0) / (b - a), shift = (fa - a) * step;          // where the from-window sits, in window coordinates
  const xw = k => x0 + (k - a) * step;                                  // an item's x once the line has slid to the window
  const inWin = k => k >= a && k <= b, inFrom = k => k >= fa && k <= fb, tp = at(p.pan_at, 1.0), moving = [];
  const line = stroke(`M ${xw(0) - 60} ${y} L ${xw(items.length - 1) + 60} ${y}`, 5, FG, .75);
  gsap.set(line, { x: -shift }); moving.push(line);
  draw(line, .05, .6);
  items.forEach((it, k) => {
    if (!inWin(k) && !inFrom(k)) return;
    const start = inFrom(k), j = k - fa, hot = k === p.hot, t = start ? at(it.at, p.from ? .3 + j * .2 : .6 + j * .8) : tp;
    const m = dot(xw(k), y, hot ? 18 : 13, hot ? RED : FG); gsap.set(m, { scale: 0, x: xw(k) - shift }); moving.push(m);
    tl.to(m, { scale: 1, duration: .3, ease: TORN ? "steps(3)" : "back.out(2)" }, t);
    const d = box(`<span class="num${hot ? " hot" : ""}" style="white-space:nowrap">${it.date}</span>`, { cx: xw(k), y: y - 150, size: 80 });
    d.style.whiteSpace = "nowrap";
    // kept inside the frame where it stops: the window for items in it, the from-window for the ones that slide out
    const room = l => Math.max(90, Math.min(1830 - d.offsetWidth, l));
    const left = inWin(k) ? room(xw(k) - d.offsetWidth / 2) : room(xw(k) - shift - d.offsetWidth / 2) + shift;
    d.style.left = left + "px"; gsap.set(d, { x: -shift }); moving.push(d); popIn(d, t);
    if (it.text) { const c = box(it.text, { cx: xw(k), y: y + 40, cls: "card", size: 40, w: Math.min(420, step - 20), rot: k % 2 ? 1 : -1 });
      c.style.textAlign = "center"; c.style.left = (xw(k) - c.offsetWidth / 2) + "px"; gsap.set(c, { x: -shift }); moving.push(c); popIn(c, t + .15); }
  });
  if (shift) { tl.to(moving, { x: `+=${shift}`, duration: 1.2, ease: "power2.inOut" }, tp); sfx("whoosh", tp); }
}
