// screen_step — a recorded screen (doc_screen.py) or a screenshot, with each step marked as the narration names it:
// the rest of the screen dims, a bright box rings the element, a curved arrow runs from a black label with the step number.
// p.src (png, or the doc_screen webm with p.log) · p.frame "browser" (window bar + p.url_text) | "none" · p.clip [from, to]
// (webm; default: the first step's click lands when its phrase is said) · p.steps: [{n, label, at, box: [x, y, w, h] in the
// 1920 x 1080 recording | step: the log step number}]. doc_code.py resolves boxes into p._screen and places the media.
// p.zoom (optional, e.g. 1.6): the camera pushes in on each step (its box and label) up to this scale, pans to the next
// step, and pulls back to the full window after the last; without it nothing moves.
SCENES.screen_step = p => {
  const S = p._screen, [rx, ry, rw, rh] = S.rect, HI = cv("--hi") || "#ffd166", INK = "#111315";
  const layer = (z) => { const d = document.createElement("div"); d.className = "full"; d.style.zIndex = z; CONTENT.appendChild(d); return d; };
  let bar = null;
  if (S.frame === "browser") {
    bar = layer(4);
    bar.innerHTML = `<div style="position:absolute;left:${rx}px;top:${ry - 56}px;width:${rw}px;height:56px;background:var(--strip);
      border-radius:14px 14px 0 0;box-shadow:0 10px 30px rgba(0,0,0,.18)">
      ${[0, 1, 2].map(i => `<span style="position:absolute;left:${22 + i * 26}px;top:21px;width:14px;height:14px;border-radius:50%;
        background:${["#ff5f57", "#febc2e", "#28c840"][i]}"></span>`).join("")}
      <span style="position:absolute;left:110px;top:11px;height:34px;width:${Math.min(rw - 220, 900)}px;border-radius:17px;
        background:var(--bg);color:var(--muted);font:500 20px/34px var(--font-ui);padding:0 18px;overflow:hidden;
        white-space:nowrap">${S.url_text || ""}</span></div>`;
  }
  const dimC = getComputedStyle(document.querySelector(".dim")).backgroundColor;
  const shade = layer(15), marks = layer(22), drawn = [], shots = [];
  const ov = document.createElementNS(NS, "svg"); ov.setAttribute("viewBox", "0 0 1920 1080"); ov.setAttribute("class", "full");
  shade.appendChild(ov);
  S.marks.forEach((m, k) => {
    const t = at(m.at, .5 + k * 1.5), next = S.marks[k + 1];
    const t2 = Math.min(next ? at(next.at, t + 1.5) : D, m.until != null ? Math.max(m.until, t + .6) : D);   // until: the click left the page
    const [x, y, w, h] = m.box, pad = 10, hx = x - pad, hy = y - pad, hw = w + 2 * pad, hh = h + 2 * pad;
    // dim the screen around the element (even-odd: the hole stays clear)
    const dim = el("path", { d: `M ${rx} ${ry} h ${rw} v ${rh} h ${-rw} Z M ${hx} ${hy} v ${hh} h ${hw} v ${-hh} Z`,
                             fill: dimC, "fill-rule": "evenodd", opacity: 0 }, ov);
    tl.to(dim, { opacity: .55, duration: .3 }, t); tl.to(dim, { opacity: 0, duration: .25 }, t2 - .25);
    const ring = document.createElement("div"); marks.appendChild(ring);
    Object.assign(ring.style, { position: "absolute", left: hx + "px", top: hy + "px", width: hw + "px", height: hh + "px",
      border: `5px solid ${HI}`, borderRadius: "12px", boxShadow: `0 0 0 4px rgba(0,0,0,.25), 0 0 24px ${HI}`, opacity: 0 });
    tl.fromTo(ring, { opacity: 0, scale: 1.12 }, { opacity: 1, scale: 1, duration: .3, ease: "back.out(2)", immediateRender: false }, t);
    sfx("click", t);
    tl.to(ring, { opacity: 0, duration: .25 }, t2 - .25);
    // label on the side of the element with more room, a little above it
    const right = x + w / 2 < rx + rw / 2, lab = document.createElement("div"); marks.appendChild(lab);
    lab.innerHTML = `<span style="display:inline-block;width:52px;height:52px;border-radius:50%;background:var(--red);color:#fff;
      font:900 32px/52px var(--font-ui);text-align:center;margin-right:16px;vertical-align:middle">${m.n}</span>
      <span style="vertical-align:middle">${m.label}</span>`;
    Object.assign(lab.style, { position: "absolute", background: INK, color: "#fff", font: "800 36px var(--font-ui)",
      padding: "12px 26px 12px 12px", borderRadius: "40px", whiteSpace: "nowrap", opacity: 0 });
    const lw = lab.offsetWidth, lh = lab.offsetHeight;
    const lx = Math.max(24, Math.min(1896 - lw, right ? hx + hw + 120 : hx - 120 - lw));
    const ly = Math.max(24, Math.min(1056 - lh, hy - lh - 40));
    lab.style.left = lx + "px"; lab.style.top = ly + "px";
    tl.fromTo(lab, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: .3, immediateRender: false }, t + .1);
    tl.to(lab, { opacity: 0, duration: .25 }, t2 - .25);
    // curved arrow from the label to the ring's near edge
    const ax = right ? lx : lx + lw, ay = ly + lh / 2, bx = right ? hx + hw + 8 : hx - 8, by = hy + hh / 2;
    const arrow = stroke(`M ${ax} ${ay} Q ${(ax + bx) / 2} ${Math.min(ay, by) - 40} ${bx} ${by}`, 6, cv("--red"), 1, "brush");
    ov.appendChild(arrow);
    const head = el("path", { d: `M 0 0 L -22 -12 L -22 12 Z`, fill: cv("--red"), opacity: 0 }, ov);
    head.setAttribute("transform", `translate(${bx} ${by}) rotate(${right ? 180 : 0})`);
    draw(arrow, t + .2, .35); tl.to(head, { opacity: 1, duration: .05 }, t + .5);
    tl.to([arrow, head], { opacity: 0, duration: .25 }, t2 - .25);
    drawn.push({ n: m.n, at: t, rect: [ring.offsetLeft + pad, ring.offsetTop + pad, ring.offsetWidth - 2 * pad, ring.offsetHeight - 2 * pad] });
    shots.push({ t, t2, u: [Math.min(hx, lx), Math.min(hy, ly), Math.max(hx + hw, lx + lw), Math.max(hy + hh, ly + lh)] });
  });
  const media = document.getElementById("screen") || document.querySelector("#root > img");
  if (p.zoom > 1 && shots.length) {
    // one transform on every layer that shows the screen, origin the frame's top-left: a point q lands at z * q + (x, y)
    const cam = [media, bar, shade, marks].filter(Boolean), top = S.frame === "browser" ? ry - 56 : ry;
    cam.forEach(e => gsap.set(e, { transformOrigin: `${-e.offsetLeft}px ${-e.offsetTop}px` }));   // the frame's corner, not each layer's own
    const view = ([x0, y0, x1, y1]) => {
      const z = Math.max(1, Math.min(p.zoom, .8 * 1920 / (x1 - x0), .8 * 1080 / (y1 - y0)));
      // centre the step, then keep the view inside the recording (zoom never shows beyond the screen)
      const fit = (c, lo, hi, W) => z * (hi - lo) >= W ? Math.min(-z * lo, Math.max(W - z * hi, W / 2 - z * c)) : (W - z * (lo + hi)) / 2;
      return { scale: z, x: fit((x0 + x1) / 2, rx, rx + rw, 1920), y: fit((y0 + y1) / 2, top, ry + rh, 1080) };
    };
    shots.forEach(s => tl.to(cam, { ...view(s.u), duration: .6, ease: "power2.inOut" }, s.t));
    const end = shots[shots.length - 1].t2;
    if (end + .6 <= D) tl.to(cam, { scale: 1, x: 0, y: 0, duration: .6, ease: "power2.inOut" }, end);
  }
  window.__marks = { screen: media ? [media.offsetLeft, media.offsetTop, media.offsetWidth, media.offsetHeight] : null,
                     clip: S.clip, marks: drawn };
};
