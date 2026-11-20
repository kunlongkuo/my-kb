// object_draw — a single object drawn stroke by stroke in empty space (the closing image), slow push-in.
// p.preset: "chair" | p.paths: [svg path d, ...] · p.shadow: true
const PRESETS = {
  chair: ["M 900 380 L 905 560", "M 1010 380 L 1005 560", "M 900 395 L 1010 395", "M 902 440 L 1008 440",
          "M 880 560 L 1035 560", "M 890 562 L 885 690", "M 1025 562 L 1030 690", "M 925 575 L 922 660", "M 990 575 L 994 660"],
};
SCENES.object_draw = p => {
  tl.fromTo("#stage", { scale: 1 }, { scale: 1.05, duration: D, ease: "none" }, 0);
  const paths = p.paths || PRESETS[p.preset];
  paths.forEach((d, k) => draw(stroke(d, k === 4 ? 9 : 6, FG, .8), .05 + k * .07, .25));
  if (p.shadow !== false) { const sh = el("ellipse", { cx: 960, cy: 700, rx: 120, ry: 16, fill: FG, opacity: 0, filter: "url(#wash)" }); tl.to(sh, { opacity: .12, duration: 1 }, 1.2); }
};
