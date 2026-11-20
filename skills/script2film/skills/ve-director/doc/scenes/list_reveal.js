// list_reveal — a short list (2-5 items) building up one item per mention; optional title; one item can be marked.
// p.title · p.items: [{text, at}] · p.hot: index to underline in red (at its own time + 0.6 s)
// p.big: larger words and wider spacing for a 2-3 item list that would leave the frame half empty
// An item too long for one line wraps inside its card (which stops 100 px short of the right edge) and pushes the items below
// it down by the extra lines; if that would run into the bottom 200 px (subtitles) the words and the spacing shrink together
// (to 60 % at most) until the list fits (2026-11-17 trial: a wrapped big item's second line sat under the next card).
// One-line lists keep their places.
SCENES.list_reveal = p => {
  const Z = p.big ? { title: 88, item: 76, x: 380, y0: 330, max: 190, room: 640 } : { title: 66, item: 54, x: 520, y0: 290, max: 130, room: 560 };
  if (p.title) { const h = box(p.title, { cx: 960, y: 130, size: Z.title }); h.style.fontWeight = 800; recentre(h, 960); popIn(h, .2); }
  const n = p.items.length, y0 = p.title ? Z.y0 : 220, step = Math.min(Z.max, Z.room / n), FLOOR = 1080 - 200 - (p.hot != null ? 12 : 0);   // + the red underline
  const card = (html, k) => { const b = box(html, { x: Z.x, y: y0, cls: "card", size: Z.item, rot: k % 2 ? .8 : -.8 });
    b.style.maxWidth = (1920 - Z.x - 100) + "px"; return b; };
  const B = p.items.map((it, k) => card(`<span class="num">${k + 1}</span>　${it.text}`, k)), one = card(`<span class="num">1</span>　x`, 0);
  const place = size => {   // a card taller than one line moves the rest down by the difference; returns the list's bottom
    [...B, one].forEach(b => b.style.fontSize = size + "px");
    let y = y0; B.forEach(b => { b.style.top = y + "px"; y += step * size / Z.item + b.offsetHeight - one.offsetHeight; });
    return B[n - 1].offsetTop + B[n - 1].offsetHeight;
  };
  // (the template builds scenes once the fonts are in, so these heights are the real font's)
  let s = Z.item; place(s);
  if (B.some(b => b.offsetHeight > one.offsetHeight)) while (place(s) > FLOOR && s > Z.item * .6) s -= 2;
  one.remove();
  p.items.forEach((it, k) => { const t = at(it.at, .5 + k * .9); popIn(B[k], t); sfx("tick", t); if (k === p.hot) hotLine(B[k], t + .6); });
};
