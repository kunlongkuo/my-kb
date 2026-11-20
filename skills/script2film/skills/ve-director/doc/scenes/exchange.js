// exchange — two agents (dots at fixed LX/RX/Y) trading moves; consecutive exchange shots hard-cut as one continuous board.
// p.mode:
//   coop      grid fades in, dots appear on p.appear, pale alternating moves from p.loop to the end
//   mirror    each move answered by an identical one: p.a, p.b
//   spiral    a kind move (p.good) misread as an attack (p.bad), retaliation starts (p.revenge) and accelerates (p.loop)
//   forgive   the pile dims; the other agent turns red (p.other); an attack comes (p.attack); it answers with a clearing (p.forgive)
//   reconcile the pile clears (p.start); the two are tied and pulled together (p.pull), then travel up-right together (p.far)
SCENES.exchange = p => {
  const m = p.mode;
  if (m === "coop") {
    const g = grid(); gsap.set(g, { opacity: 0 }); tl.to(g, { opacity: .14, duration: .8 }, 0);
    const L = dot(LX, Y, 30), R = dot(RX, Y, 30); gsap.set([L, R], { scale: 0 });
    const t0 = at(p.appear, 2.5);
    tl.to(L, { scale: 1, duration: .4, ease: "back.out(2)" }, t0); tl.to(R, { scale: 1, duration: .4, ease: "back.out(2)" }, t0 + .2);
    for (let k = 0, t = at(p.loop, 4); t < D - .6; k++, t += .55) {
      const q = k % 2 === 0 ? stroke(arc(LX + 30, Y - 6, RX - 30, Y - 6, -60), 6, FG, .45) : stroke(arc(RX - 30, Y + 6, LX + 30, Y + 6, 60), 6, FG, .45);
      draw(q, t, .3); tl.to(q, { opacity: .06, duration: .5 }, t + .45);
    }
  } else if (m === "mirror") {
    grid(); const L = dot(LX, Y, 30), R = dot(RX, Y, 30);
    const a = stroke(arc(LX + 30, Y - 8, RX - 30, Y - 8, -70), 9, FG, .7), b = stroke(arc(RX - 30, Y + 8, LX + 30, Y + 8, 70), 9, FG, .7);
    const t1 = at(p.a, 3.2), t2 = at(p.b, 4.6);
    draw(a, t1, .35); tl.to(R, { scale: 1.15, duration: .15, yoyo: true, repeat: 1 }, t1 + .35);
    draw(b, t2, .35); tl.to(L, { scale: 1.15, duration: .15, yoyo: true, repeat: 1 }, t2 + .35);
  } else if (m === "spiral") {
    const g = grid(); const L = dot(LX, Y, 30), R = dot(RX, Y, 30);
    const good = stroke(arc(LX + 30, Y - 8, RX - 30, Y - 8, -70), 7, FG, .35);
    const tg = at(p.good, .9), tb = at(p.bad, 2.2), tr = at(p.revenge, 3.2), tloop = at(p.loop, 4.4);
    draw(good, tg - .4, 1.4, "sine.inOut");
    const bad = stroke("M 790 452 L 850 430 L 880 448 L 930 418 L 975 440 L 1020 414 L 1065 436 L 1130 452", 13, FG, .9);
    draw(bad, tb, .25, "power3.in"); tl.to(good, { opacity: 0, duration: .2 }, tb + .2); recoil(R, tb + .25, 16);
    let t = tr;
    mess(14).forEach((q, k) => {
      draw(q, t, .22, "power3.in"); recoil(k % 2 === 0 ? R : L, t + .2, k % 2 === 0 ? 12 : -12);
      t += Math.max(.18, (k < 2 ? (tloop - tr) / 2 : .42 - k * .02));
    });
    const fog = el("ellipse", { cx: 960, cy: Y, rx: 420, ry: 200, fill: FG, opacity: 0, filter: "url(#wash)" });
    tl.to(fog, { opacity: .3, duration: 2.2 }, tloop); tl.to(g, { opacity: .03, duration: 1.5 }, tloop);
  } else if (m === "forgive") {
    const L = dot(LX, Y, 30), R = dot(RX, Y, 30);
    const msg = el("g", {}); mess(14).map(shown).forEach(q => msg.appendChild(q));
    const fog = el("ellipse", { cx: 960, cy: Y, rx: 420, ry: 200, fill: FG, opacity: .3, filter: "url(#wash)" });
    svg.appendChild(L); svg.appendChild(R);
    const t0 = at(p.other, .4), t1 = at(p.attack, 2), t2 = at(p.forgive, 3);
    tl.to([msg, fog], { opacity: .4, duration: .8 }, t0);
    tl.to(R.core, { attr: { fill: RED }, duration: .6 }, t0 + .3); tl.to(R, { scale: 1.12, duration: .3, yoyo: true, repeat: 1 }, t0 + .3);
    const inc = stroke(arc(LX + 30, Y - 10, RX - 40, Y - 10, -80), 12, FG, .85); draw(inc, t1, .4, "power3.in");
    const clear = el("circle", { cx: RX, cy: Y, r: 10, fill: BG, opacity: 0, filter: "url(#wash)" });
    const blush = el("circle", { cx: RX, cy: Y, r: 70, fill: RED, opacity: 0, filter: "url(#wash)" }); svg.appendChild(R);
    tl.set(clear, { opacity: .92 }, t2); tl.to(clear, { attr: { r: 300 }, duration: 1.6, ease: "expo.out" }, t2);
    tl.to(blush, { opacity: .22, duration: 1 }, t2 + .2); tl.to(inc, { opacity: .2, duration: 1 }, t2 + .3);
  } else if (m === "reconcile") {
    const L = dot(LX, Y, 30), R = dot(RX, Y, 30); R.core.setAttribute("fill", RED);
    const msg = el("g", { opacity: .4 }); mess(14).map(shown).forEach(q => msg.appendChild(q));
    const fog = el("ellipse", { cx: 960, cy: Y, rx: 420, ry: 200, fill: FG, opacity: .12, filter: "url(#wash)" });
    const clear = el("circle", { cx: RX, cy: Y, r: 300, fill: BG, opacity: .92, filter: "url(#wash)" });
    svg.appendChild(L); svg.appendChild(R);
    const t0 = at(p.start, .3), t1 = at(p.pull, 2.2), t2 = at(p.far, D - 2.2);
    tl.to([msg, fog], { opacity: 0, duration: 1.3 }, t0); tl.to(clear, { opacity: 0, duration: 1.3 }, t0 + .3);
    const tie = stroke(`M ${LX + 30} ${Y} L ${RX - 30} ${Y}`, 5, FG, .5); draw(tie, t0 + .2, .9);
    tl.to(L, { x: 880, duration: 1.1, ease: "power2.inOut" }, t1); tl.to(R, { x: 1040, duration: 1.1, ease: "power2.inOut" }, t1);
    tl.to(tie, { attr: { d: `M 910 ${Y} L 1010 ${Y}` }, duration: 1.1, ease: "power2.inOut" }, t1);
    draw(stroke("M 330 820 L 1820 75", 4, FG, .35), t2 - .3, 1.6, "sine.inOut");   // the road up-right: hands over to a path shot
    tl.to([L, R, tie], { x: "+=420", y: "-=210", duration: D - t2, ease: "sine.inOut" }, t2);
    tl.to([L, R], { scale: .55, duration: D - t2, ease: "sine.inOut" }, t2);
  } else throw new Error(`exchange: unknown mode ${m}`);
};
