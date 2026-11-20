// Shared helpers for doc-mode code shots. Globals from the template: D, TOKENS, LANG, THEME, TORN, PH_EASE, P, tl (created after this file).
const SCENES = {};   // scene templates register here (scenes/*.js)
const css = getComputedStyle(document.documentElement), cv = n => css.getPropertyValue(n).trim();
// scene elements go in #content: with side.beats (stage "left") doc_code scales that layer into the left 1220 px
const CONTENT = document.getElementById("content");
const FG = cv("--fg"), RED = cv("--red"), BG = cv("--bg-solid") || cv("--bg"), LX = 760, RX = 1160, Y = 470;
// rising / falling colours (lecture themes; doc.json "rise" picks red-up or green-up); other themes fall back to red / ink
const UP = cv("--up") || RED, DOWN = cv("--down") || FG;

// Timing. TOKENS = [[token, seconds from shot start], ...]: one CJK character each (zh) or one lower-case word (en).
const tok = s => LANG === "zh" ? [...s].filter(c => /[一-鿿0-9A-Za-z]/.test(c))
                               : s.toLowerCase().replace(/[^a-z0-9' ]+/g, " ").split(/\s+/).filter(Boolean);
function T(phrase, fallback, nth = 0) {          // when the phrase starts being spoken
  const q = tok(phrase), words = TOKENS.map(t => t[0]);
  let seen = 0;
  for (let i = 0; i + q.length <= words.length; i++)
    if (q.every((w, k) => words[i + k] === w) && seen++ === nth) return TOKENS[i][1];
  return fallback;
}
// A time parameter: number (seconds) | "phrase" | {w: "phrase", d: offset, f: fallback}
function at(v, fallback = 0) {
  if (v == null) return fallback;
  if (typeof v === "number") return v;
  if (typeof v === "string") return T(v, fallback);
  if (typeof v !== "object" || typeof v.w !== "string") return fallback;   // anything else: not a time
  return T(v.w, v.f ?? fallback) + (v.d || 0);
}
// Sound effects: a scene marks the second a visual action lands; doc_code reads window.__sfx after
// building the page and doc_sfx.py turns the marks into the beat's sounds (kinds: doc/sfx_map.json)
window.__sfx = [];
function sfx(kind, t) { if (Number.isFinite(t)) window.__sfx.push({ kind, t: Math.round(t * 1000) / 1000 }); }

let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647, (seed - 1) / 2147483646);
const NS = "http://www.w3.org/2000/svg", svg = document.getElementById("ink");
function el(tag, attrs, parent = svg) { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); parent.appendChild(e); return e; }
function dot(x, y, r, color = FG) {
  const grp = el("g", {}); el("circle", { r: r * 2, fill: color, opacity: .10, filter: "url(#wash)" }, grp);
  const core = el("circle", { r, fill: color, filter: "url(#bleed)" }, grp);
  gsap.set(grp, { x, y, transformOrigin: "50% 50%" }); grp.core = core; return grp;
}
function stroke(d, w, color = FG, op = .8, filter = "brush") {
  const p = el("path", { d, fill: "none", stroke: color, "stroke-width": w, "stroke-linecap": "round", opacity: op, filter: `url(#${filter})` });
  const len = p.getTotalLength(); p.setAttribute("stroke-dasharray", len); p.setAttribute("stroke-dashoffset", len); return p;
}
const draw = (p, t, dur = .4, ease = "power2.inOut") => tl.to(p, { strokeDashoffset: 0, duration: dur, ease }, t);
const shown = p => (p.setAttribute("stroke-dashoffset", 0), p);
const arc = (x1, y1, x2, y2, bend) => `M ${x1} ${y1} Q ${(x1 + x2) / 2} ${(y1 + y2) / 2 + bend} ${x2} ${y2}`;
const recoil = (d, t, dx) => tl.to(d, { x: `+=${dx}`, duration: .07, yoyo: true, repeat: 1, ease: "power1.out" }, t);
function grid(op = .14) {
  const g = el("g", { opacity: op });
  for (let x = 560; x <= 1360; x += 100) el("path", { d: `M ${x} 270 L ${x} 690`, stroke: FG, "stroke-width": 2, filter: "url(#brush)" }, g);
  for (let y = 270; y <= 690; y += 70) el("path", { d: `M 560 ${y} L 1360 ${y}`, stroke: FG, "stroke-width": 2, filter: "url(#brush)" }, g);
  return g;
}
function mess(n = 14) {                        // the pile of retaliation strokes: identical in every shot that shows it
  seed = 31; const out = [];
  for (let k = 0; k < n; k++) {
    const fromL = k % 2 === 0, bend = (fromL ? -1 : 1) * (40 + rnd() * 110), w = 9 + k * 1.1;
    const y1 = Y + (rnd() - .5) * 60, y2 = Y + (rnd() - .5) * 60;
    out.push(stroke(fromL ? arc(LX + 30, y1, RX - 30, y2, bend) : arc(RX - 30, y1, LX + 30, y2, bend), w, FG, .55 + rnd() * .3));
  }
  return out;
}
function setText(sel, main, sub) { const e = document.querySelector(sel); if (!e) return;
  if (e.querySelector(".main")) { e.querySelector(".main").textContent = main || ""; e.querySelector(".sub").textContent = sub || ""; } else e.textContent = main || ""; }

// Photos (archival stills: never animate real faces with a video model)
const layer = document.getElementById("photos");
function torn(n = 9, j = 1.4) {
  const s = seed, pts = []; seed = 101 + Math.floor(rnd() * 999);
  for (let i = 0; i <= n; i++) pts.push([i / n * 100, rnd() * j]);
  for (let i = 0; i <= n; i++) pts.push([100 - rnd() * j, i / n * 100]);
  for (let i = n; i >= 0; i--) pts.push([i / n * 100, 100 - rnd() * j]);
  for (let i = n; i >= 0; i--) pts.push([rnd() * j, i / n * 100]);
  seed = s; return `polygon(${pts.map(([x, y]) => `${x.toFixed(2)}% ${y.toFixed(2)}%`).join(",")})`;
}
function photo({ src, rect, rot = 0, cap = null, fg = null, leak = false }) {
  const [x, y, w, h] = rect, wrap = document.createElement("div"); wrap.className = "phwrap";
  Object.assign(wrap.style, { left: x + "px", top: y + "px", width: w + "px", height: h + "px" });
  if (TORN) wrap.style.filter = "drop-shadow(5px 8px 0 rgba(40,28,14,.28))";
  const ph = document.createElement("div"); ph.className = "ph"; if (TORN) ph.style.clipPath = torn();
  const inner = document.createElement("div"); inner.className = "inner"; inner.style.backgroundImage = `url("${src}")`;
  ph.appendChild(inner); if (TORN) { const t = document.createElement("div"); t.className = "tone"; ph.appendChild(t); }
  if (fg) { const f = document.createElement("div"); f.className = "inner"; f.style.backgroundImage = `url("${fg}")`; f.style.filter = "none";
    ph.appendChild(f); wrap.fg = f; }
  if (leak) { const l = document.createElement("div");
    Object.assign(l.style, { position: "absolute", inset: "-20%", mixBlendMode: "screen", opacity: 0, pointerEvents: "none",
      background: "radial-gradient(ellipse 38% 55% at 50% 50%, rgba(255,170,70,.85), rgba(255,90,40,.35) 45%, rgba(0,0,0,0) 70%)" });
    ph.appendChild(l); wrap.leak = l; }
  wrap.appendChild(ph); wrap.inner = inner;
  if (TORN) { const tp = document.createElement("div"); tp.className = "tape"; wrap.appendChild(tp); }
  if (cap) { const c = document.createElement("div"); c.className = "cap"; c.innerHTML = `<span class="bar"></span>${cap}`;
    Object.assign(c.style, TORN ? { left: "24px", top: (h - 22) + "px" } : { left: "0px", top: (h + 18) + "px" }); c.style.opacity = 0; wrap.appendChild(c); wrap.cap = c; }
  layer.appendChild(wrap); gsap.set(wrap, { rotation: rot, opacity: 0 }); wrap.rot = rot;
  // A caption under the photo that would reach the bottom 200 px (README: kept free for subtitles) goes inside the photo's
  // lower-left corner instead (a full-width photo's caption sat under the subtitle box)
  if (cap && !TORN && y + h + 18 + wrap.cap.offsetHeight > 1080 - 200)
    Object.assign(wrap.cap.style, { left: "24px", top: (h - wrap.cap.offsetHeight - 24) + "px" });
  return wrap;
}
function photoIn(wrap, t) {
  if (TORN) { tl.set(wrap, { opacity: 1, y: 70, rotation: wrap.rot - 7 }, t); tl.to(wrap, { y: 0, rotation: wrap.rot, duration: .45, ease: "steps(5)" }, t); }
  else tl.to(wrap, { opacity: 1, duration: .5, ease: "power2.out" }, t);
}
function capIn(wrap, t) { if (wrap.cap) { tl.set(wrap.cap, { x: TORN ? 0 : -14 }, t); tl.to(wrap.cap, { opacity: 1, x: 0, duration: TORN ? .2 : .4, ease: PH_EASE }, t); } }
function accent(wrap, t) {
  if (!wrap.cap) return; const b = document.createElement("div");
  Object.assign(b.style, { position: "absolute", left: wrap.cap.style.left, top: (parseFloat(wrap.cap.style.top) + 58) + "px", height: TORN ? "14px" : "4px", width: "0px", background: RED, transform: TORN ? "rotate(-1.5deg)" : "none" });
  wrap.appendChild(b); tl.to(b, { width: wrap.cap.offsetWidth + "px", duration: .45, ease: TORN ? "steps(4)" : "power2.out" }, t);
}
function quote(text, cx, top) {
  const q = document.createElement("div"); q.className = "quote"; q.textContent = text; CONTENT.appendChild(q);
  q.style.top = top + "px"; q.style.left = (cx - q.offsetWidth / 2) + "px"; gsap.set(q, { y: 16 }); return q;
}

// Text blocks: box() places a div (left/top or centred on cx), popIn() brings it in with the theme's motion
function box(html, { x = null, cx = null, y, w = null, cls = "", rot = 0, size = null } = {}) {
  const b = document.createElement("div"); b.className = `blk ${cls}`; b.innerHTML = html;
  if (w) b.style.width = w + "px"; if (size) b.style.fontSize = size + "px";
  CONTENT.appendChild(b); b.style.top = y + "px";
  b.style.left = (cx != null ? cx - b.offsetWidth / 2 : x) + "px";
  if (TORN && b.classList.contains("card")) b.style.boxShadow = "4px 5px 0 rgba(40,28,14,.25)";
  gsap.set(b, { rotation: TORN ? rot : 0 }); return b;
}
// recentre — put a box's centre back on cx after a style that changes its width (font weight) was set on it after box()
// measured it (2026-11-17: list_reveal's title, set to 800 afterwards, sat 30 px right of centre)
const recentre = (b, cx) => (b.style.left = (cx - b.offsetWidth / 2) + "px", b);
function popIn(b, t) {
  if (TORN) { tl.set(b, { opacity: 1, y: 30 }, t); tl.to(b, { y: 0, duration: .3, ease: "steps(4)" }, t); }
  else { tl.set(b, { y: 14 }, t); tl.to(b, { opacity: 1, y: 0, duration: .45, ease: "power2.out" }, t); }
}
// slamIn — a key number lands instead of fading in (feedback: 看起來像 PPT, every block faded in the same
// gentle way, so the numbers that carry the story had no weight). Comes in large and overshoots down, the stage jolts as it
// lands, a stone thud on the landing. Keep it for the 3-5 numbers a film turns on; everything else stays popIn.
function slamIn(b, t) {
  tl.set(b, { scale: 1.9, y: 0 }, t); tl.to(b, { opacity: 1, duration: .08 }, t);
  tl.to(b, { scale: 1, duration: .34, ease: "back.out(2.4)" }, t);
  recoil(CONTENT, t + .12, 10); sfx("stone", t + .12);
}
function hotLine(b, t) {                       // red underline (collage: red tape) under a block
  const u = document.createElement("div"); CONTENT.appendChild(u);
  Object.assign(u.style, { position: "absolute", zIndex: 21, left: b.offsetLeft + "px", top: (b.offsetTop + b.offsetHeight + 6) + "px",
    width: "0px", height: TORN ? "14px" : "5px", background: RED, transform: TORN ? "rotate(-1.2deg)" : "none" });
  tl.to(u, { width: b.offsetWidth + "px", duration: .4, ease: TORN ? "steps(4)" : "power2.out" }, t);
}

// Scenes that would hold still once their animation ends push the whole picture in slowly:
// p.drift = scale (default 1.10; the user could not see 1.03, 2026-10-29) or false. Skipped when a photo already pushes
// (quote_card photo, photos[] with push).
function drift(p, def = 1.10) {
  const pushing = [].concat(p.photo || []).some(o => o.push ?? !o.rect) || (p.photos || []).some(o => o.push);
  if (p.drift === false || pushing) return;
  tl.fromTo("#drift", { scale: 1 }, { scale: p.drift ?? def, duration: D, ease: "none" }, 0);
}

// Layers any scene can carry: p.photos[], p.label, p.quote
function overlays(p) {
  (p.photos || []).forEach(o => {
    const w = photo(o); photoIn(w, at(o.at, .05)); sfx("paper", at(o.at, .05)); capIn(w, at(o.cap_at, at(o.at, .05) + .4));
    if (o.push && w.fg) {   // 2.5D: the cut-out player pushes in faster than the photo behind it, which
      // blurs and dims a little after the photo lands, so the person comes off the page (fg: same size as src, transparent)
      const k = o.push - 1, t1 = at(o.at, .05) + .6;
      tl.fromTo(w.inner, { scale: 1 }, { scale: 1 + k * .5, duration: D, ease: "none", immediateRender: false }, 0);
      tl.fromTo(w.fg, { scale: 1, x: 0 }, { scale: 1 + k * 2.2, x: o.fg_dx ?? -24, duration: D, ease: "sine.inOut", immediateRender: false }, 0);
      tl.fromTo(w.inner, { filter: "blur(0px) brightness(1)" }, { filter: "blur(4px) brightness(.78)", duration: 1.2, ease: "power1.inOut", immediateRender: false }, t1);
    } else if (o.push) tl.fromTo(w.inner, { scale: 1 }, { scale: o.push, duration: D, ease: "none", immediateRender: false }, 0);
    if (w.leak) {   // a warm light leak drifts across once
      tl.fromTo(w.leak, { x: -700, opacity: 0 }, { x: 700, duration: D, ease: "none", immediateRender: false }, 0);
      tl.to(w.leak, { opacity: .55, duration: D * .35, ease: "sine.inOut", yoyo: true, repeat: 1 }, D * .15);
    }
    if (o.accent_at != null) accent(w, at(o.accent_at, D - 1.5));
    if (o.exit) tl.to(w, { x: o.exit.x || 0, y: o.exit.y || 0, scale: o.exit.scale || 1, duration: .8, ease: "power2.inOut" }, at(o.exit.at, D - 1));
  });
  if (p.label && typeof p.label === "object") {
    setText("#label", p.label.text, p.label.sub);
    tl.fromTo("#label", { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: .5, immediateRender: false }, at(p.label.at, .5));
    if (p.label.out !== false) tl.to("#label", { opacity: 0, duration: .4 }, D - TAIL - .6);
  }
  if (p.quote) {
    const q = quote(p.quote.text, p.quote.cx || 960, p.quote.top || 640);
    tl.to(q, { opacity: 1, y: 0, duration: .4, ease: TORN ? "steps(4)" : "power2.out" }, at(p.quote.at, D / 2));
  }
}

// Chart helpers for line_chart, pie, formula, breakdown.
// sectorPath — one slice of a pie (r0 0) or a ring (r0 > 0) as a path d. Angles in radians, 0 at 12 o'clock, clockwise.
// Always starts on the outer arc at a0 (M), outer arc to a1 (A), line to the inner arc at a1 (L), inner arc back to a0 (A), Z;
// with r0 0 the inner arc is the centre: "L cx cy Z". a1 = a0 gives a slice with no area (start = end).
function sectorPath(cx, cy, r0, r1, a0, a1) {
  const r2 = v => Math.round(v * 100) / 100, pt = (r, a) => `${r2(cx + r * Math.sin(a))} ${r2(cy - r * Math.cos(a))}`;
  const big = a1 - a0 > Math.PI ? 1 : 0;
  let d = `M ${pt(r1, a0)} A ${r1} ${r1} 0 ${big} 1 ${pt(r1, a1)}`;
  return d + (r0 > 0 ? ` L ${pt(r0, a1)} A ${r0} ${r0} 0 ${big} 0 ${pt(r0, a0)} Z` : ` L ${r2(cx)} ${r2(cy)} Z`);
}
// polyPath — [[x, y], ...] → "M x0 y0 L x1 y1 ..."
const polyPath = pts => pts.map(([x, y], k) => `${k ? "L" : "M"} ${x} ${y}`).join(" ");
// focusDim — at t, els[i] goes to opacity 1 and the rest to .25 over 0.3 s (relation's focus rule). i may also be a list of
// indexes that all stay lit (breakdown: a node and its path to the root); null entries in els are skipped.
function focusDim(els, i, t) {
  const keep = new Set([].concat(i));
  els.forEach((e, k) => { if (e) tl.to(e, { opacity: keep.has(k) ? 1 : .25, duration: .3 }, t); });
}
