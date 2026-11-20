// seed_dot — hook: one dot lands with a pale trail; a wash breathes in and out; the dot pulses on the anchor word.
// p.sigh: [phrase, phrase] (wash rises, falls) · p.pulse: phrase
SCENES.seed_dot = p => {
  tl.fromTo("#stage", { scale: 1 }, { scale: 1.06, duration: D, ease: "none" }, 0);
  const a = dot(860, 470, 46); gsap.set(a, { scale: 0 });
  tl.to(a, { scale: 1, duration: .9, ease: "power3.out" }, .15);
  draw(stroke("M 905 485 C 1000 530, 1120 515, 1230 462", 24, FG, .32), .35, .9);
  const sigh = el("ellipse", { cx: 1060, cy: 490, rx: 230, ry: 95, fill: FG, opacity: 0, filter: "url(#wash)" });
  const [s1, s2] = p.sigh || [];
  tl.to(sigh, { opacity: .13, duration: 1.1, ease: "sine.inOut" }, at(s1, 1));
  tl.to(sigh, { opacity: .03, duration: 1.1, ease: "sine.inOut" }, at(s2, 2.3));
  if (p.pulse) tl.to(a, { scale: 1.12, duration: .25, yoyo: true, repeat: 1, ease: "sine.inOut" }, at(p.pulse, D - 1.5));
};
