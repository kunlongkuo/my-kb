// split_duel — a screen frame split down the middle; two dots appear, one strikes, the other strikes back.
// p.appear: phrase (dots appear) · p.hits: [phrase, phrase] (first strike, strike back)
SCENES.split_duel = p => {
  draw(stroke("M 560 250 L 1360 250 L 1360 700 L 560 700 Z", 6, FG, .75), 0, .45);   // done before the first word
  draw(stroke("M 960 270 L 960 680", 4, FG, .3), .3, .4);
  const L = dot(LX, Y, 30), R = dot(RX, Y, 30); gsap.set([L, R], { scale: 0 });
  const t0 = at(p.appear, 1);
  tl.to(L, { scale: 1, duration: .4, ease: "back.out(2)" }, t0); tl.to(R, { scale: 1, duration: .4, ease: "back.out(2)" }, t0 + .2);
  const hit = stroke(arc(LX + 30, Y - 8, RX - 30, Y - 8, -70), 10, FG, .8), back = stroke(arc(RX - 30, Y + 8, LX + 30, Y + 8, 70), 10, FG, .8);
  const [h1, h2] = p.hits || [];
  const t1 = at(h1, 2.2), t2 = at(h2, 3.4);
  draw(hit, t1, .32, "power3.in"); recoil(R, t1 + .3, 14); tl.to(hit, { opacity: .25, duration: .6 }, t1 + .7);
  draw(back, t2, .32, "power3.in"); recoil(L, t2 + .3, -14);
};
