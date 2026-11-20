// web_evidence — a still screenshot of a real page (official site, README, announcement, news headline) as evidence: the
// part that matters, cropped, with the spoken words swiped by a highlighter as they are said, and the source under it.
// p.src (png / jpg in the project) · p.crop [x, y, w, h] (source pixels, default the whole image) · p.source (required:
// site or outlet + date, shown under the card) · p.marks [{box: [x, y, w, h] source pixels, at}] · p.at (card in) ·
// p.push (slow push-in scale, default 1.03) · p.maxh (card height cap, default 700; 620 keeps the source line clear of
// two-line bilingual subtitles). doc_code.py passes the image size as p._img [w, h].
// Not screen_step: no browser frame, no dimming, no arrows; a still read as a document, not an operation.
// p.scroll [{y, at, dur}]: a long stitched page (doc_evidence.py) read like a scroll: the crop is the window, and at each
// stop the page glides (dur, default 1.2 s) until source row y is at the window's top; marks ride along. No push-in then
// (show more of the page or the whole news item, not one sentence).
SCENES.web_evidence = p => {
  const [iw, ih] = p._img, [cx0, cy0, cw, ch] = p.crop || [0, 0, iw, ih];
  const H = p.maxh || 700, k = Math.min(1600 / cw, H / ch), w = cw * k, h = ch * k, x = 960 - w / 2, y = 110 + (H - h) / 2;
  const t = at(p.at, .2);
  const card = document.createElement("div");
  Object.assign(card.style, { position: "absolute", left: x + "px", top: y + "px", width: w + "px", height: h + "px",
    overflow: "hidden", borderRadius: "6px", background: "#fff", boxShadow: "0 14px 40px rgba(0,0,0,.28)", opacity: 0 });
  const inner = document.createElement("div");
  Object.assign(inner.style, { position: "absolute", left: 0, top: 0, width: w + "px", height: h + "px", transformOrigin: "50% 50%" });
  const img = document.createElement("img"); img.src = p.src;
  Object.assign(img.style, { position: "absolute", left: (-cx0 * k) + "px", top: (-cy0 * k) + "px", width: (iw * k) + "px", height: (ih * k) + "px" });
  inner.appendChild(img); card.appendChild(inner); CONTENT.appendChild(card);
  tl.set(card, { y: 24 }, t); tl.to(card, { opacity: 1, y: 0, duration: .45, ease: "power2.out" }, t);
  if (p.scroll) p.scroll.forEach(s =>
    tl.to(inner, { y: -(s.y - cy0) * k, duration: s.dur || 1.2, ease: "power2.inOut" }, at(s.at, t + .5)));
  else tl.fromTo(inner, { scale: 1 }, { scale: p.push || 1.03, duration: D, ease: "none", immediateRender: false }, 0);
  (p.marks || []).forEach(m => {
    const [mx, my, mw, mh] = m.box, hl = document.createElement("div");
    Object.assign(hl.style, { position: "absolute", left: ((mx - cx0) * k - 4) + "px", top: ((my - cy0) * k - 2) + "px",
      width: "0px", height: (mh * k + 4) + "px", background: cv("--must"), opacity: .45, mixBlendMode: "multiply", borderRadius: "3px" });
    inner.appendChild(hl);
    tl.to(hl, { width: (mw * k + 8) + "px", duration: .35, ease: "power2.out" }, at(m.at, t + .6)); sfx("marker", at(m.at, t + .6));
  });
  const s = box(p.source, { x, y: y + h + 22, size: 30 });
  Object.assign(s.style, { fontFamily: "var(--font-ui)", opacity: 0 });
  tl.to(s, { opacity: .85, duration: .4 }, t + .3);
};
