// flow — how something travels: nodes (cards with a filled icon or a picture) joined by links; as each step is said a
// glowing packet runs along its link, the node it reaches lights up with a ripple, and packets keep flowing after that.
// Polished, not bare lines, and four looks that read differently; use a different look for consecutive diagrams in one film:
//   web     light: round badges on a faint grid, dashed links that march, a reached node turns red (spread / infection)
//   pipe    tiles on one glowing rail, times above the tiles (a path taken in order; made for bg_video tone "dark", on a
//           light palette the tiles stay dark and the text around them takes the palette's own ink)
//   streams ribbons of different widths and colours pouring from sources into one sink, a counter on each ribbon
//   lanes   two parallel tracks; p.block drops a shutter on one, packets keep running on the other
// p.nodes [{id, x, y, label, sub, icon, src, at, hot, time, color}] — icon: laptop ai container stamp chain wallet target
//   lock shield coin; src: a picture (VE still) instead of an icon; at: when it appears (default: when its first link arrives);
//   hot: lights up red when reached; time: a time card above (pipe)
// p.links [{from, to, at, color, w, count: {value, prefix, suffix, decimals, at}, dur, bend, label}] — at: when the packet
//   leaves (the link draws then); w: ribbon width (streams); count: number counting up on the ribbon; bend: curve (px)
// p.tag {text, at, color} pill top-left · p.block {link, at, label, u} shutter on that link (lanes) · p.note small caption
//   (bottom-right; lanes: centred, red), p.note_at, p.note_xy [cx, y]
SCENES.flow = p => {
  drift(p, 1.04);
  // sounds: doc_sfx keeps at most 3 per beat, so collect them and keep the 3 that matter most (shutter, a node getting hit,
  // the first link, the first node), in time order
  const SND = [], snd = (kind, t, rank) => SND.push({ kind, t, rank });
  const look = p.look || "web", dark = look === "pipe" || look === "streams";
  const MUST = cv("--must") || "#efca66", STRIP = cv("--strip") || "#fff", MUTED = cv("--muted") || FG;
  // the theme "red" is its accent (blue in lecture-light), so a reached / attacked node uses a real red; dark looks light up gold
  const ALARM = "#e2463b", GOLD = cv("--hi") && dark ? cv("--hi") : "#f5b800";
  // Text that sits on the page itself (labels under the tiles, time cards, counts, the note) follows the page, not the look:
  // on a light palette the dark looks' white / cyan / gold text all but vanished (2026-11-17 trial: pipe on lecture-food).
  // The tiles stay dark. A dark bg_video wash under the scene keeps the page dark; a light wash is the page colour.
  const rgb = s => { const m = /^#([0-9a-f]{6})$/i.exec(s); return m ? [0, 2, 4].map(i => parseInt(m[1].slice(i, i + 2), 16) / 255) : null; };
  const lum = c => c.map(v => v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4).reduce((s, v, i) => s + v * [.2126, .7152, .0722][i], 0);
  const wash = document.querySelector("#bgv + .full"), page = rgb(BG);
  const onLight = !!page && lum(page) > .4 && (!wash || /var\(--bg\)/.test(wash.getAttribute("style") || ""));
  const ink = dark && !onLight;   // page text in the dark looks' own light colours
  const ALARM_INK = "#c0392b";   // ALARM is under 3:1 on the paler light palettes (collage, lecture-light, -history); this is not
  const defs = svg.querySelector("defs");
  const glow = el("filter", { id: "flowglow", x: "-50%", y: "-50%", width: "200%", height: "200%" }, defs);
  el("feGaussianBlur", { stdDeviation: 7, result: "b" }, glow);
  const m = el("feMerge", {}, glow); el("feMergeNode", { in: "b" }, m); el("feMergeNode", { in: "SourceGraphic" }, m);
  const shadow = el("filter", { id: "flowshadow", x: "-30%", y: "-30%", width: "160%", height: "160%" }, defs);
  el("feDropShadow", { dx: 0, dy: 10, stdDeviation: 12, "flood-color": "#000", "flood-opacity": dark ? .55 : .22 }, shadow);

  if (look === "web") {   // faint grid behind the badges
    const g = el("g", { opacity: .35 });
    for (let x = 0; x <= 1920; x += 48) el("path", { d: `M${x} 0V1080`, stroke: MUTED, "stroke-width": 1, opacity: .25 }, g);
    for (let y = 0; y <= 1080; y += 48) el("path", { d: `M0 ${y}H1920`, stroke: MUTED, "stroke-width": 1, opacity: .25 }, g);
    tl.fromTo(g, { opacity: 0 }, { opacity: .35, duration: .6, immediateRender: false }, 0);
  }
  const linkG = el("g", {}), nodeG = el("g", {}), pktG = el("g", {});
  const N = {}; (p.nodes || []).forEach(n => N[n.id] = n);
  const links = (p.links || []).map((l, i) => ({ ...l, i, t: at(l.at, .4 + i * .9) }));
  // when each node shows: its own at, else when the first link reaching it arrives, else when the first link leaves it
  const travel = l => l.dur || (look === "streams" ? 1.1 : .8);
  (p.nodes || []).forEach(n => {
    const inn = links.filter(l => l.to === n.id).map(l => l.t + travel(l)), out = links.filter(l => l.from === n.id).map(l => l.t - .3);
    n.t = n.at != null ? at(n.at, .2) : inn.length ? Math.min(...inn) - .25 : out.length ? Math.max(.1, Math.min(...out)) : .2;
    n.reach = inn.length ? Math.min(...inn) : null;
  });

  // ── icons: filled shapes in a 120×120 box centred on 0,0 ──
  function icon(name, g, c, hotc) {
    const f = (tag, a) => el(tag, a, g);
    switch (name) {
      case "laptop":
        f("rect", { x: -46, y: -40, width: 92, height: 62, rx: 8, fill: c });
        f("rect", { x: -38, y: -32, width: 76, height: 46, rx: 4, fill: dark ? "#0b1830" : "#dfeaf6" });
        f("rect", { x: -32, y: -26, width: 40, height: 6, rx: 3, fill: hotc, opacity: .8 });
        f("rect", { x: -32, y: -14, width: 56, height: 5, rx: 2.5, fill: c, opacity: .35 });
        f("path", { d: "M-60 26H60L52 38H-52Z", fill: c }); break;
      case "ai":
        f("polygon", { points: "0,-56 48,-28 48,28 0,56 -48,28 -48,-28", fill: MUST });
        f("polygon", { points: "0,-40 35,-20 35,20 0,40 -35,20 -35,-20", fill: "none", stroke: "#fff", "stroke-width": 3, opacity: .6 });
        const t = f("text", { y: 13, "text-anchor": "middle", "font-size": 38, "font-weight": 900, fill: "#272e40", "font-family": "Noto Sans TC" }); t.textContent = "AI"; break;
      case "container":
        f("rect", { x: -54, y: -34, width: 108, height: 68, rx: 6, fill: c });
        for (let k = -36; k <= 36; k += 18) f("rect", { x: k - 3, y: -28, width: 6, height: 56, rx: 3, fill: "#fff", opacity: .35 });
        f("rect", { x: -54, y: -34, width: 108, height: 10, rx: 5, fill: "#fff", opacity: .25 }); break;
      case "stamp":
        f("path", { d: "M-16 -50h32v26c0 8 26 10 26 26v8h-84v-8c0-16 26-18 26-26z", fill: MUST });
        f("rect", { x: -48, y: 14, width: 96, height: 16, rx: 4, fill: MUST }); f("rect", { x: -40, y: 36, width: 80, height: 10, rx: 5, fill: hotc }); break;
      case "chain":
        [-40, 0, 40].forEach((x, k) => { f("rect", { x: x - 17, y: -17, width: 34, height: 34, rx: 6, fill: c, opacity: 1 - k * .15 });
          if (k < 2) f("rect", { x: x + 17, y: -3, width: 6, height: 6, fill: c }); }); break;
      case "wallet":
        f("rect", { x: -50, y: -34, width: 100, height: 72, rx: 12, fill: c });
        f("rect", { x: 14, y: -12, width: 40, height: 28, rx: 8, fill: dark ? "#0b1830" : "#fff", opacity: .9 });
        f("circle", { cx: 28, cy: 2, r: 6, fill: MUST }); break;
      case "target":
        f("circle", { r: 50, fill: hotc }); f("circle", { r: 34, fill: "#2a0b0b" }); f("circle", { r: 18, fill: hotc });
        f("path", { d: "M0 -60V-40M0 40V60M-60 0H-40M40 0H60", stroke: hotc, "stroke-width": 6, "stroke-linecap": "round" }); break;
      case "lock":
        f("path", { d: "M-24 -8v-16a24 24 0 0 1 48 0v16", fill: "none", stroke: MUST, "stroke-width": 10 });
        f("rect", { x: -36, y: -10, width: 72, height: 56, rx: 10, fill: MUST }); f("circle", { cy: 14, r: 8, fill: "#272e40" }); break;
      case "shield":
        f("path", { d: "M0 -56L46 -38V2C46 30 24 48 0 58C-24 48 -46 30 -46 2V-38Z", fill: c });
        f("path", { d: "M-18 2L-4 16L22 -14", fill: "none", stroke: "#fff", "stroke-width": 9, "stroke-linecap": "round" }); break;
      case "coin":
        f("circle", { r: 46, fill: MUST }); f("circle", { r: 34, fill: "none", stroke: "#fff", "stroke-width": 4, opacity: .6 }); break;
    }
  }

  // ── nodes ──
  const NODE = {};
  (p.nodes || []).forEach(n => {
    const c = n.color || (dark ? "#69dff9" : "#557fe1"), g = el("g", {}, nodeG); gsap.set(g, { x: n.x, y: n.y, opacity: 0, scale: .6, transformOrigin: "0px 0px" });
    const sz = n.size || (look === "streams" && !n.sink ? 74 : look === "web" ? 112 : 100);
    let frame;
    if (look === "web" || n.sink) {
      frame = el("circle", { r: sz, fill: dark ? "#14172b" : STRIP, stroke: c, "stroke-width": 8, filter: "url(#flowshadow)" }, g);
    } else {
      const w = look === "streams" ? 240 : sz * 2, h = look === "streams" ? 110 : sz * 2;
      frame = el("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: 24, fill: dark ? "#0d1426" : STRIP, stroke: c, "stroke-width": 5, filter: "url(#flowshadow)" }, g);
      el("rect", { x: -w / 2 + 6, y: -h / 2 + 6, width: w - 12, height: h * .38, rx: 18, fill: "#fff", opacity: dark ? .05 : .5 }, g);
    }
    const ig = el("g", {}, g); gsap.set(ig, { scale: look === "streams" && !n.sink ? .55 : 1, x: look === "streams" && !n.sink ? -70 : 0 });
    if (n.src) {
      const r = look === "web" || n.sink ? sz - 12 : sz - 14, cp = el("clipPath", { id: `fc${n.id}` }, defs);
      if (look === "web" || n.sink) el("circle", { r }, cp); else el("rect", { x: -r, y: -r, width: 2 * r, height: 2 * r, rx: 16 }, cp);
      el("image", { href: n.src, x: -r, y: -r, width: 2 * r, height: 2 * r, preserveAspectRatio: "xMidYMid slice", "clip-path": `url(#fc${n.id})` }, ig);
    } else icon(n.icon || "laptop", ig, c, ALARM);
    if (look === "web" || n.sink) gsap.set(ig, { scale: sz / 90 });
    if (look === "streams" && !n.sink && n.label) {
      const t = el("text", { x: -22, y: 12, "font-size": 34, "font-weight": 800, fill: dark ? "#fff" : FG, "font-family": "Noto Sans TC" }, g); t.textContent = n.label;
    }
    tl.to(g, { opacity: 1, scale: 1, duration: .5, ease: "back.out(1.8)" }, n.t); snd("pop", n.t, 4);
    // label card under (web: right of small badges if n.side)
    if (n.label && !(look === "streams" && !n.sink)) {
      const html = `<div style="font-weight:800">${n.label}</div>${n.sub ? `<div style="font-size:.66em;font-weight:500;opacity:.8;margin-top:4px">${n.sub}</div>` : ""}`;
      const below = n.side !== "right", bx = box(html, below ? { cx: n.x, y: n.y + sz + 22, size: 42 } : { x: n.x + sz + 26, y: n.y - 44, size: 42 });
      if (below) bx.style.textAlign = "center";
      if (ink) bx.style.color = n.hot ? GOLD : "#fff"; else if (dark && n.hot) bx.style.color = ALARM_INK;
      popIn(bx, n.t + .15);
    }
    if (n.time) { const tc = box(`<span class="num">${n.time}</span>`, { cx: n.x, y: n.y - sz - 96, size: 50 });
      tc.style.color = n.hot ? (dark && !ink ? ALARM_INK : GOLD) : (ink ? "#7de3f2" : MUTED); popIn(tc, n.reach ?? n.t); }
    NODE[n.id] = { n, g, frame, c };
    if (n.reach == null && n.hot) {   // a hot node nothing reaches (where it starts) is marked as soon as it shows
      const hc = dark ? GOLD : ALARM; tl.to(frame, { attr: { stroke: hc }, duration: .3 }, n.t + .3);
      const halo = el("circle", { r: sz + 8, fill: hc, opacity: 0, filter: "url(#flowglow)" }, g); g.insertBefore(halo, g.firstChild);
      tl.to(halo, { opacity: .25, duration: .5 }, n.t + .3);
    }
    // reached: ripple, glow; hot nodes turn red (web) or gold (dark looks)
    if (n.reach != null) {
      const hc = n.hot ? (dark ? GOLD : ALARM) : c;
      for (let k = 0; k < 2; k++) {
        const rp = el("circle", { r: sz, fill: "none", stroke: hc, "stroke-width": 6, opacity: 0 }, g);
        tl.fromTo(rp, { attr: { r: sz }, opacity: .8 }, { attr: { r: sz + 70 }, opacity: 0, duration: .9, ease: "power2.out", immediateRender: false }, n.reach + k * .25);
      }
      if (n.hot) { tl.to(frame, { attr: { stroke: hc }, duration: .2 }, n.reach); frame.setAttribute("filter", "url(#flowshadow)");
        const halo = el("circle", { r: sz + 8, fill: hc, opacity: 0, filter: "url(#flowglow)" }, g); g.insertBefore(halo, g.firstChild);
        tl.to(halo, { opacity: .35, duration: .4 }, n.reach); tl.to(halo, { opacity: .18, duration: 1.2, yoyo: true, repeat: 7, ease: "sine.inOut" }, n.reach + .4);
        snd(dark ? "chime" : "marker", n.reach, 2); }
      tl.to(g, { scale: 1.08, duration: .15, yoyo: true, repeat: 1, ease: "power1.out" }, n.reach);
    }
  });

  // ── links ──
  const LINK = [];
  links.forEach(l => {
    const a = N[l.from], b = N[l.to]; if (!a || !b) return;
    const c = l.color || (look === "web" ? ALARM : dark ? "#69dff9" : "#557fe1");
    const ra = look === "streams" ? 120 : (a.size || 100), rb = b.size || 100;
    let x1 = a.x + (b.x > a.x ? ra : 0), y1 = a.y, x2 = b.x - (b.x > a.x ? rb : 0), y2 = b.y;
    if (look === "web") { const dx = b.x - a.x, dy = b.y - a.y, L = Math.hypot(dx, dy); x1 = a.x + dx / L * ra; y1 = a.y + dy / L * ra; x2 = b.x - dx / L * rb; y2 = b.y - dy / L * rb; }
    const mx = (x1 + x2) / 2, d = look === "streams" || look === "web"
      ? `M${x1} ${y1} C${mx} ${y1 + (l.bend || 0)} ${mx} ${y2 + (l.bend || 0)} ${x2} ${y2}` : `M${x1} ${y1} L${x2} ${y2}`;
    const w = l.w || (look === "streams" ? 24 : look === "web" ? 7 : 12);
    if (look === "lanes") {   // a road under each lane, so the track reads before anything runs on it
      const road = el("rect", { x: Math.min(x1, x2) - 20, y: y1 - 38, width: Math.abs(x2 - x1) + 40, height: 76, rx: 38, fill: c, opacity: 0 }, linkG);
      linkG.insertBefore(road, linkG.firstChild); tl.to(road, { opacity: .13, duration: .4 }, Math.min(a.t, l.t));
      for (let x = Math.min(x1, x2) + 40; x < Math.max(x1, x2) - 20; x += 60)
        tl.to(el("rect", { x, y: y1 - 3, width: 28, height: 6, rx: 3, fill: c, opacity: 0 }, linkG), { opacity: .35, duration: .2 }, Math.min(a.t, l.t) + .2);
    }
    const tube = el("path", { d, fill: "none", stroke: c, "stroke-width": w + (look === "streams" ? 0 : 16), opacity: 0, "stroke-linecap": "round" }, linkG);   // hidden until its link starts (2026-11-04: a faint line showed before its nodes)
    const core = el("path", { d, fill: "none", stroke: c, "stroke-width": w, "stroke-linecap": look === "streams" ? "butt" : "round", opacity: look === "streams" ? .85 : 1,
      filter: look === "web" ? "" : "url(#flowglow)" }, linkG);
    if (look !== "web") {   // the glow region in frame pixels around the link: #flowglow's region is a share of the path's
      // box, which a level link (height 0) has none of, so its core vanished (2026-11-17, pipe; a 1 px slope showed a 2 px sliver)
      const bb = core.getBBox(), pad = w + 40, f = defs.appendChild(glow.cloneNode(true));
      Object.entries({ id: `flowglow${l.i}`, filterUnits: "userSpaceOnUse", x: bb.x - pad, y: bb.y - pad, width: bb.width + 2 * pad,
        height: bb.height + 2 * pad }).forEach(([k, v]) => f.setAttribute(k, v));
      core.setAttribute("filter", `url(#flowglow${l.i})`);
    }
    const len = core.getTotalLength();
    core.setAttribute("stroke-dasharray", `${len} ${len}`); core.setAttribute("stroke-dashoffset", len);
    tl.fromTo(tube, { opacity: 0 }, { opacity: look === "streams" ? 0 : .14, duration: .3, immediateRender: false }, l.t);
    const op = core.getAttribute("opacity"); core.setAttribute("opacity", 0); tl.set(core, { attr: { opacity: op } }, l.t);   // a round cap would show as a dot
    tl.to(core, { strokeDashoffset: 0, duration: travel(l), ease: "power1.inOut" }, l.t); snd("whoosh", l.t, l.i ? 5 : 3);
    if (look === "web") {   // after drawing, the link turns dashed and marches
      tl.set(core, { attr: { "stroke-dasharray": "18 12", "stroke-dashoffset": 0 } }, l.t + travel(l));
      tl.to(core, { attr: { "stroke-dashoffset": -30 * 20 }, duration: 20, ease: "none" }, l.t + travel(l));
    }
    // packets: a bright head with a soft tail, looping along the link until the end of the shot
    const n = look === "streams" ? 4 : 2, per = look === "streams" ? 1.6 : 1.3;
    for (let k = 0; k < n; k++) {
      const pk = el("g", { opacity: 0 }, pktG);
      el("circle", { r: look === "web" ? 14 : 16, fill: c, opacity: .35, filter: "url(#flowglow)" }, pk);
      el("circle", { r: look === "web" ? 8 : 7, fill: look === "web" ? c : "#fff" }, pk);
      const st = { u: 0 }, start = l.t + (k ? travel(l) + k * per / n : 0);
      const place = () => { const q = core.getPointAtLength(st.u * len); pk.setAttribute("transform", `translate(${q.x} ${q.y})`); };
      place();
      tl.set(pk, { opacity: 1 }, start);
      const reps = Math.max(0, Math.floor((D - start) / per) - 1);
      tl.fromTo(st, { u: 0 }, { u: 1, duration: k ? per : travel(l), ease: k ? "none" : "power1.inOut", repeat: k ? reps : 0, onUpdate: place, immediateRender: false }, start);
      if (!k) tl.set(pk, { opacity: 0 }, start + travel(l));
    }
    if (l.label) { const q = core.getPointAtLength(len / 2), lb = box(l.label, { cx: q.x, y: q.y - 70, size: 30, cls: "card" });
      lb.style.borderRadius = "10px"; popIn(lb, l.t + .3); }
    if (l.count) {   // number counting up beside the ribbon's start
      const q = look === "streams" ? { x: x1 + 24, y: y1 - 6 } : core.getPointAtLength(len * .18), cn = box(`<span class="num"></span>`, { x: q.x + 10, y: q.y - 68, size: 46 });
      cn.style.color = dark && !ink ? FG : c; cn.style.textShadow = ink ? "0 2px 12px rgba(0,0,0,.8)" : "none";
      const s = cn.querySelector(".num"), o = { v: 0 }, dec = l.count.decimals || 0;
      const show = () => s.textContent = `${l.count.prefix || ""}${o.v.toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec })}${l.count.suffix || ""}`;
      show(); const tc = at(l.count.at, l.t + .2); popIn(cn, tc);
      tl.to(o, { v: l.count.value, duration: 1.2, ease: "power2.out", onUpdate: show }, tc);
    }
    LINK.push({ l, core, len });
  });

  // ── shutter on a lane ──
  if (p.block) {
    const L = LINK[p.block.link || 0]; if (L) {
      const q = L.core.getPointAtLength(L.len * (p.block.u ?? .5)), tb = at(p.block.at, 2);
      const sh = el("g", {}, nodeG); gsap.set(sh, { x: q.x, y: q.y });
      const door = el("g", {}, sh);
      el("rect", { x: -70, y: -110, width: 140, height: 220, rx: 12, fill: "#557fe1", filter: "url(#flowshadow)" }, door);
      for (let y = -78; y <= 82; y += 32) el("rect", { x: -70, y, width: 140, height: 6, fill: "#cadff0", opacity: .7 }, door);
      const lk = el("g", {}, door); icon("lock", lk, MUST, RED); gsap.set(lk, { scale: .55 });
      gsap.set(door, { y: -360, opacity: 0 });
      tl.to(door, { opacity: 1, duration: .1 }, tb); tl.to(door, { y: 0, duration: .45, ease: "bounce.out" }, tb); snd("shutter", tb + .3, 1);
      tl.to(L.core, { opacity: .25, duration: .4 }, tb + .3);
      if (p.block.label) { const lb = box(p.block.label, { cx: q.x, y: q.y + 130, size: 32 }); lb.style.fontWeight = 800; recentre(lb, q.x); lb.style.color = MUTED; popIn(lb, tb + .4); }
    }
  }
  SND.sort((x, y) => x.rank - y.rank || x.t - y.t).slice(0, 3).sort((x, y) => x.t - y.t).forEach(o => sfx(o.kind, o.t));
  if (p.tag) {
    const t = box(p.tag.text, { x: 64, y: 48, size: 34 });
    Object.assign(t.style, { fontWeight: 800, padding: "10px 22px", borderRadius: "12px", background: p.tag.color || (dark ? "#69dff9" : "#272e40"),
      color: dark ? "#020101" : MUST, boxShadow: "0 8px 24px rgba(0,0,0,.25)" });
    popIn(t, at(p.tag.at, .1));
  }
  if (p.note) { const [nx, ny] = p.note_xy || (look === "lanes" ? [960, 790] : [1440, 790]), t = box(p.note, { cx: nx, y: ny, size: look === "lanes" ? 32 : 24 }); t.style.opacity = 0; t.style.color = ink ? "#9aa3b8" : MUTED; if (look === "lanes") { t.style.fontWeight = 800; t.style.color = ALARM; recentre(t, nx); } popIn(t, at(p.note_at, 1)); }
};
