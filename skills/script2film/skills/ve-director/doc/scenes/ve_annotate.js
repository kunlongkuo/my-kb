// ve_annotate — a VE shot plays, freezes on one frame, gets marked (ring → arrow → one label), then plays on
// (never freeze before the shot has played, and mark one thing per freeze).
// p.src (a VE clip in the project, e.g. ve_collage/shot5.mp4) · p.in (source second the shot starts from, default 0)
// p.freeze (beat time: seconds or a phrase) · p.hold (seconds held, default 2.2) · p.rings: [{x, y, r, ry}] · p.arrows:
// [{from: [x, y], to: [x, y], bend}] · p.note {text, x, y}: the one label per freeze (not "label": that name is the shared
// label layer). Coordinates are 1920 x 1080 frame pixels.
// doc_code.py cuts the clip into vean.mp4 (play, the same frame held for hold s, play on) and passes p._ve {freeze, hold}.
SCENES.ve_annotate = p => {
  const V = p._ve, t0 = V.freeze, t1 = V.freeze + V.hold, RED = cv("--red");   // the accent: --hi is pale on photos (collage)
  const v = document.getElementById("vean");
  // the punch below gives #content a transform, i.e. its own stacking context: lift it over the video (z 3), still under
  // the vignette / dim / flash layers (30+)
  CONTENT.style.zIndex = 4;
  // freeze entry (telestrator §6): flash, the picture and the marks punch in together, colour drops
  tl.to(".flash", { opacity: .55, duration: .05 }, t0); tl.to(".flash", { opacity: 0, duration: .12 }, t0 + .05); sfx("shutter", t0);
  tl.fromTo([v, CONTENT], { scale: 1.035 }, { scale: 1, duration: .35, ease: "power2.out", immediateRender: false }, t0);
  tl.set(v, { filter: "saturate(.58)" }, t0); tl.set(v, { filter: "none" }, t1);
  const gone = [];
  let t = t0 + .3;                                            // ring (who) → arrow (what) → label (the finding), §6 draw order
  (p.rings || []).forEach(r => {
    const ry = r.ry || r.r;
    const ring = stroke(`M ${r.x - r.r} ${r.y} a ${r.r} ${ry} 0 1 0 ${2 * r.r} 0 a ${r.r} ${ry} 0 1 0 ${-2 * r.r} 0`, 8, RED, 1);
    draw(ring, t, .4); gone.push(ring); t += .35;
  });
  (p.arrows || []).forEach(a => {
    const [x1, y1] = a.from, [x2, y2] = a.to, line = stroke(arc(x1, y1, x2, y2, a.bend ?? -40), 8, RED, 1);
    const ang = Math.atan2(y2 - ((y1 + y2) / 2 + (a.bend ?? -40)), x2 - (x1 + x2) / 2) * 180 / Math.PI;
    const head = el("path", { d: "M 0 0 L -26 -14 L -26 14 Z", fill: RED, opacity: 0 });
    head.setAttribute("transform", `translate(${x2} ${y2}) rotate(${ang})`);
    draw(line, t, .4); tl.to(head, { opacity: 1, duration: .05 }, t + .36); gone.push(line, head); t += .45;
  });
  if (p.note) {
    const b = box(p.note.text, { x: p.note.x, y: p.note.y, cls: "card", size: 44, rot: -1 });
    b.style.fontWeight = 800; popIn(b, t); gone.push(b);
  }
  tl.to(gone, { opacity: 0, duration: .25 }, t1 - .25);
};
