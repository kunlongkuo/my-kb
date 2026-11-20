// quote_card — a full-screen quotation with its source (scripture, a speech, a paper's key sentence).
// p.text · p.by (attribution) · p.at · p.size (default 64) · p.photo: one still {src, rect, rot, cap, push} or two [{...}, {...}].
// Leave rect / rot out to use the layout below: one still upper left, two stills upper left and lower right at
// opposite tilts; the quote strip overlaps them in the middle. Stills without rect slowly push in (push 1.05).
// p.reveal "blur": the card comes in with the words as a faint blur (opacity .15; a card left empty until the voice reached
// the quote read as a blank strip, 2026-11-20 demo: 2.7 s) and they come out of it one character after another, following
// the voice: the text is cut at its punctuation and each part starts when the narration says its first (up to) four characters,
// 0.05 s between characters; a part the narration does not say keeps going at the same pace from the part before it (at
// most 0.06 s a character, 2.5 s for the whole text). The characters are inline spans, so the lines break exactly as they
// would without the reveal (no transform on them: an inline-block per character would lose the punctuation line rules).
const QUOTE_PHOTOS = {
  1: [{ rect: [90, 150, 780, 439], rot: 3 }],
  2: [{ rect: [70, 90, 760, 428], rot: -3 }, { rect: [1090, 450, 740, 416], rot: 4 }],
};
SCENES.quote_card = p => {
  drift(p);
  const t = at(p.at, .3), ph = p.photo ? [].concat(p.photo) : [];
  if (ph.length > 2) throw new Error("quote_card: photo takes one or two stills");
  ph.forEach((o, i) => {
    const d = QUOTE_PHOTOS[ph.length][i], auto = !o.rect;
    const w = photo({ src: o.src, rect: o.rect || d.rect, rot: o.rot ?? (auto ? d.rot : 0), cap: o.cap });
    photoIn(w, t - .2 + i * .25); sfx("paper", t - .2 + i * .25); capIn(w, t + .2 + i * .25);
    const push = o.push ?? (auto ? 1.05 : null);
    if (push) tl.fromTo(w.inner, { scale: 1 }, { scale: push, duration: D, ease: "none", immediateRender: false }, 0);
  });
  const cx = ph.length === 1 ? 1080 : 960, y = ph.length === 2 ? 400 : 300;
  const q = box(p.text, { cx, y, w: ph.length === 1 ? 1100 : ph.length === 2 ? 1300 : 1400, cls: "card", size: p.size || 64, rot: -1 });
  Object.assign(q.style, { fontFamily: "var(--font-big)", fontWeight: 800, lineHeight: 1.35, textAlign: "center" });
  q.style.left = (cx - q.offsetWidth / 2) + "px"; popIn(q, t); sfx("whoosh", t);
  const done = p.reveal === "blur" ? blurReveal(q, p.text, t + .15) : t;
  if (p.by) {
    const b = box(p.by, { cx, y: q.offsetTop + q.offsetHeight + 40, size: 36 });
    // two stills: the second one sits under this line, so lift it above the photos on a paper pill (2026-11-06, 第 60 集 Taher 的出處被蓋掉)
    // the pill is paper-coloured in every palette, so its ink is fixed too: a dark palette's light text vanished on it (2026-11-14 lecture-story)
    if (ph.length === 2) Object.assign(b.style, { zIndex: 22, background: "#f4ecd8", color: "#1d1a17", padding: "6px 18px", borderRadius: "6px" });
    popIn(b, Math.max(t + .5, Math.min(done, D - TAIL - 1)));
  }
};
function blurReveal(q, text, t0) {
  const chars = [...String(text)], per = Math.min(.06, 2.5 / Math.max(1, chars.length));
  q.innerHTML = chars.map(c => `<span class="rv">${c === "<" ? "&lt;" : c === "&" ? "&amp;" : c}</span>`).join("");
  const spans = [...q.children], parts = [];
  let cur = [];                                  // a part: the characters up to and including its closing punctuation
  chars.forEach((c, k) => { cur.push(k); if (/[，。；：！？、,.;:!?…）」』]/.test(c)) { parts.push(cur); cur = []; } });
  if (cur.length) parts.push(cur);
  let next = t0;
  parts.forEach(ix => {
    const head = tok(ix.map(k => chars[k]).join("")).slice(0, 4).join(LANG === "zh" ? "" : " ");
    const said = head ? T(head, null) : null, gap = said != null ? .05 : per;
    let t = said != null && said >= next - .3 ? said : next;
    ix.forEach(k => { tl.fromTo(spans[k], { opacity: .15, filter: "blur(10px)" },
      { opacity: 1, filter: "blur(0px)", duration: TORN ? .2 : .45, ease: TORN ? "steps(3)" : "power2.out", immediateRender: true }, t);
      t += gap; });
    next = t;
  });
  return next + .45;
}
