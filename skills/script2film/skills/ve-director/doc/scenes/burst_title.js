// burst_title — the climax: the frame dims during the breath before the downbeat, holds still, then bursts on p.word:
// flash, ring, scattered fragments, the big anchor word (p.big) and the term below it (p.term, p.term_sub in italics).
// Collage theme puts red paper behind the word: a disc when the word fits, a strip when it is wide. Start this shot right after the previous line ends (beat "after_prev").
SCENES.burst_title = p => {
  setText("#big", p.big); setText("#term", p.term, p.term_sub);
  const tw = at(p.word, .8);
  tl.to(".dim", { opacity: .66, duration: Math.max(.3, tw - .2), ease: "power2.in" }, 0);
  tl.set(".dim", { opacity: 0 }, tw); tl.set(".flash", { opacity: .75 }, tw);
  tl.to(".flash", { opacity: 0, duration: .55, ease: "power2.out" }, tw + 1 / 30);
  const halo = el("circle", { cx: 960, cy: 400, r: 330, fill: FG, opacity: 0, filter: "url(#wash)" });
  tl.to(halo, { opacity: .14, duration: .3, ease: "power2.out" }, tw);
  const ring = el("circle", { cx: 960, cy: 400, r: 230, fill: "none", stroke: FG, "stroke-width": 34, opacity: .55, filter: "url(#bleed)" });
  gsap.set(ring, { opacity: 0 });
  tl.set(ring, { opacity: .55 }, tw); tl.to(ring, { attr: { r: 620, "stroke-width": 6 }, opacity: 0, duration: 1.5, ease: "expo.out" }, tw);
  for (let k = 0; k < 16; k++) {
    const ang = k / 16 * Math.PI * 2 + rnd() * .3, dist = 360 + rnd() * 200, s = dot(960 + Math.cos(ang) * 240, 400 + Math.sin(ang) * 150, 5 + rnd() * 12);
    gsap.set(s, { scale: 0 });
    tl.to(s, { scale: 1, x: 960 + Math.cos(ang) * dist, y: 400 + Math.sin(ang) * dist * .62, duration: .7, ease: "expo.out" }, tw);
    tl.to(s, { opacity: .45, duration: .8 }, tw + .7);
  }
  if (THEME === "collage") {                     // red paper behind the word: a disc when the word fits, else a strip
    const big = document.getElementById("big"), span = document.createElement("span");
    span.textContent = p.big; big.textContent = ""; big.appendChild(span);
    const r = span.getBoundingClientRect(), cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    const back = r.width < 800 ? el("circle", { cx, cy, r: 250, fill: RED, filter: "url(#bleed)" })
      : el("rect", { x: cx - r.width / 2 - 70, y: cy - r.height * .62, width: r.width + 140, height: r.height * 1.24, fill: RED,
                     transform: `rotate(-1.5 ${cx} ${cy})`, filter: "url(#bleed)" });
    gsap.set(back, { scale: 0, transformOrigin: `${cx}px ${cy}px` });
    tl.set(back, { scale: 1.35 }, tw); tl.to(back, { scale: 1, duration: .35, ease: "steps(4)" }, tw);
    big.style.color = "var(--hi)";
  }
  tl.fromTo("#big", { opacity: 0, scale: 1.25 }, { opacity: 1, scale: 1, duration: .18, ease: "power4.out", immediateRender: false }, tw);
  tl.to("#big", { scale: 1.015, duration: 1.1, yoyo: true, repeat: 1, ease: "sine.inOut" }, tw + .3);
  tl.fromTo("#term", { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: .5, ease: "power2.out", immediateRender: false }, tw + .6);
};
