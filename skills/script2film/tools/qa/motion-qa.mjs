#!/usr/bin/env node
// motion-qa.mjs — 成片逐格檢查：單幀閃現、≥1s 靜止、硬切、每秒運動曲線（可選：循環接縫）。
//
// 為什麼要有：出片檢查的聯絡表只抽幾格給人看，抽格之間一閃即逝的單幀看不到；
//   freezedetect 只報 ≥2s 全停。這支逐格全看，把可疑時間碼列出來，再回聯絡表／單幀放大確認。
//   只看「畫面有沒有在變」，不懂內容：壓臉、擺位仍靠人看。
//
// 來源：移植自 huashu-motion `cli/lib/qa.js`（MIT，github.com/alchaincyf/huashu-motion @3e92780，2026-10-18）。
//   硬切（14 且 >4×局部）、靜止（0.25）門檻照原作。
//   閃現改成分格：原作用全畫面平均差 >6，實測只抓得到 ≥600×150 的白塊，字卡大小的閃現（400×100）全漏。
//   改切 12×9 格、任一格 min(前,後) >8 且前後兩格在該格差 < 1/3 就報。校準：7 支真片最高 2.8；
//   120×40 白塊突變 21.1；一支真片抓到 2 個真缺陷（22.77s 夾 1 格全黑、76.1s 疊層在切點前掉 1 格）。
//   ⚠ 限制：快速移動的小物件（白板模板的筆）和局部閃一格，只靠格差分不開——試過全畫面門檻、3×3 鄰格、
//   比值三種判別，白板候選比值低到 0.1、真閃現 0.1–0.58 重疊。所以改成密度自檢：真片候選 0–2 支／片
//   （≤0.03/s），白板 71 處／18.2s（3.9/s）；超過 0.5/s 且多於 10 處就判「局部偵測失效」，候選不列、不計入 exit。
//   已知誤報：計數動畫（數字卡 85→87→88 每格換字），另一支真片的 11.33s，抽格看到在跳數字就放行。
//   孤兒格（另一條，用全畫面差）：前後兩次跳變都 >14＝只有一格長的鏡頭（切點中間夾一格黑／別的畫面），
//   抓到 2 個真缺陷的那支 22.77s 兩條都抓到，其他 6 支真片 0 處。
//   第 0 格空白（補移植自 @52467f9）：第 0 格是封面（動態牆、播放器、預覽圖未播放前顯示的那格）。
//   內容＝離中位灰 >16 的像素比例 far、相鄰差 >20 的邊緣比例 edges；far <3% 且 edges <1.2% 判空白，
//   並報第一格 far ≥5% 且 edges ≥1.5% 的時間。門檻照原作（15 支片校準）。只列不擋：淡入開場看起來沒問題，只是封面空。
//   原作同批加的「開場平／整片平」沒移植：門檻來自發布片，跟靜止段同理，不適用畫面會停留的片型（圖示定住、字幕在換）。
//
// 用法：node tools/qa/motion-qa.mjs <video.mp4 | projectDir> [--loop] [--json]
//   給專案資料夾時，取 output/ 版號最大的 vN.mp4，沒有才 output.mp4（同出片檢查）。
//   exit 0＝無單幀閃現與孤兒格；exit 1＝有閃現、孤兒格或（--loop 時）首尾接不上——線索，抽該格看過再判斷，不是 gate；exit 2＝用法／解碼錯誤。
//   靜止段只列不判：門檻來自發布片，有些片型本來就會停留（一支真片實測 15 段都是圖示定住、字幕在換）。
import { spawnSync } from "node:child_process";
import { existsSync, readdirSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const W = 96, H = 54;
export const BX = 12, BY = 9, POP = 8, POP_RATE = 0.5, POP_MIN = 10;
const BW = W / BX, BH = H / BY;

export const diff = (a, b) => { let s = 0; for (let i = 0; i < a.length; i++) s += Math.abs(a[i] - b[i]); return s / a.length; };
const median = (xs) => { const s = [...xs].sort((a, b) => a - b); return s.length ? s[s.length >> 1] : 0; };
// 一格的內容量：離中位灰的像素比例、相鄰邊緣比例（原作 qa.js 的 content）
export const content = (px) => {
  const m = median(px);
  let far = 0, edges = 0;
  for (let i = 0; i < px.length; i++) {
    if (Math.abs(px[i] - m) > 16) far++;
    if (i % W < W - 1 && Math.abs(px[i] - px[i + 1]) > 20) edges++;
  }
  return { far: far / px.length, edges: edges / (H * (W - 1)) };
};
const filled = (c) => c.far >= 0.05 && c.edges >= 0.015;
// 每一格的平均差（BX×BY 個）
const blockDiff = (a, b) => {
  const out = new Float64Array(BX * BY);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) out[Math.floor(y / BH) * BX + Math.floor(x / BW)] += Math.abs(a[y * W + x] - b[y * W + x]);
  return out.map((s) => s / (BW * BH));
};

// 純函式：frames 是等長灰階陣列序列，fps 為幀率。
export function analyze(f, fps, { loop = false } = {}) {
  const d = f.slice(1).map((x, i) => diff(x, f[i]));
  const bd = f.slice(1).map((x, i) => blockDiff(x, f[i]));
  const t = (i) => +(i / fps).toFixed(2);
  // 單幀閃現（分格）：某一格第 i 格跟前後都差很多，但前後兩格在該格彼此很像；回報最嚴重那格的位置
  const pops = [];
  for (let i = 1; i < f.length - 1; i++) {
    const around = blockDiff(f[i - 1], f[i + 1]);
    let best = 0, at = -1;
    for (let k = 0; k < BX * BY; k++) {
      const m = Math.min(bd[i - 1][k], bd[i][k]);
      if (m > POP && around[k] < m / 3 && m > best) { best = m; at = k; }
    }
    if (at >= 0) pops.push({ at: t(i), jump: +best.toFixed(1), x: +(((at % BX) + 0.5) / BX).toFixed(2), y: +((Math.floor(at / BX) + 0.5) / BY).toFixed(2) });
  }
  // 候選太密＝畫面有持續移動的小物件，局部偵測失效（見檔頭）
  const seconds = Math.max(1, (f.length - 1) / fps);
  const suppressed = pops.length > POP_MIN && pops.length / seconds > POP_RATE;
  // 孤兒格：進這格、出這格都是大跳變＝一格長的鏡頭
  const orphans = [];
  for (let i = 1; i < d.length; i++) if (Math.min(d[i - 1], d[i]) > 14) orphans.push({ at: t(i), jump: +Math.min(d[i - 1], d[i]).toFixed(1) });
  // 硬切：遠高於局部運動量、且不回頭的跳變
  const cuts = [];
  for (let i = 0; i < d.length; i++) {
    const local = median(d.slice(Math.max(0, i - 6), i).concat(d.slice(i + 1, i + 7)));
    if (d[i] > 14 && d[i] > 4 * (local + 1) && !pops.some((p) => Math.abs(p.at - t(i + 1)) < 0.05)) cuts.push(t(i + 1));
  }
  // 靜止：連續 ≥1s 幾乎沒變
  const dead = [];
  let run = 0;
  for (let i = 0; i <= d.length; i++) {
    if (i < d.length && d[i] < 0.25) run++;
    else { if (run / fps >= 1) dead.push({ from: t(i - run), to: t(i), seconds: +(run / fps).toFixed(2) }); run = 0; }
  }
  const perSec = [];
  for (let s = 0; s * fps < d.length; s++) {
    const seg = d.slice(Math.round(s * fps), Math.round((s + 1) * fps));
    if (seg.length) perSec.push(+(seg.reduce((a, b) => a + b, 0) / seg.length).toFixed(1));
  }
  const mean = perSec.reduce((a, b) => a + b, 0) / (perSec.length || 1);
  const sd = Math.sqrt(perSec.reduce((a, b) => a + (b - mean) ** 2, 0) / (perSec.length || 1));
  const loopGap = f.length ? +diff(f[0], f[f.length - 1]).toFixed(2) : 0;
  // 第 0 格（封面）有沒有內容；空的話報畫面在幾秒填滿（只找前 10 秒）
  const c0 = f.length ? content(f[0]) : { far: 0, edges: 0 };
  let contentAt = null;
  for (let i = 0; i < f.length && i < fps * 10; i++) if (filled(content(f[i]))) { contentAt = t(i); break; }
  const firstFrame = { far: +c0.far.toFixed(3), edges: +c0.edges.toFixed(3), empty: c0.far < 0.03 && c0.edges < 0.012, contentAt };
  return {
    frames: f.length, pops: suppressed ? [] : pops, popCandidates: pops.length, suppressed, orphans, cuts, dead, firstFrame,
    motion: { perSecond: perSec, mean: +mean.toFixed(2), contrast: +(sd / (mean + 1e-6)).toFixed(2) },
    loop: { firstLastDiff: loopGap, seamless: loopGap < 1.5, checked: loop },
  };
}

export function report(r) {
  const L = [`${r.file}  ${r.width}×${r.height}  ${r.fps.toFixed(2)}fps  ${r.duration.toFixed(2)}s`];
  L.push(r.suppressed
    ? `· local flash detection disabled: ${r.popCandidates} candidates (>${POP_RATE}/s and >${POP_MIN}), something small keeps moving in the picture (e.g. a whiteboard pen); candidates are not listed and do not count toward the exit code; check by eye`
    : r.pops.length
      ? `✗ ${r.pops.length} single-frame flashes: ${r.pops.slice(0, 12).map((p) => `${p.at}s (${p.y < 0.34 ? "top" : p.y < 0.67 ? "middle" : "bottom"} ${p.x < 0.34 ? "left" : p.x < 0.67 ? "center" : "right"})`).join(", ")}${r.pops.length > 12 ? "…" : ""} — look at that frame; usually an element appears one frame early, or fromTo draws its start state first`
      : "✓ no single-frame flashes");
  L.push(r.orphans.length
    ? `✗ ${r.orphans.length} orphan frames: ${r.orphans.slice(0, 12).map((o) => o.at + "s").join(", ")} — shots one frame long, usually a splice that caught one black or stray frame`
    : "✓ no orphan frames");
  L.push(r.dead.length
    ? `· still ≥1s: ${r.dead.map((x) => `${x.from}–${x.to}s`).join(", ")} — listed, not blocking: whether the format wants such holds is judged elsewhere, not by this tool`
    : "✓ nothing still for ≥1s");
  L.push(r.firstFrame.empty
    ? `· frame 0 is almost empty (far ${r.firstFrame.far}, edges ${r.firstFrame.edges})${r.firstFrame.contentAt != null ? `, content only from ${r.firstFrame.contentAt}s` : ", not filled in the first 10 seconds"} — it is the cover (the frame a feed or preview shows before playing); listed, not blocking; to use it as the cover, have the subject in the picture from the start`
    : `✓ frame 0 has content (far ${r.firstFrame.far}, edges ${r.firstFrame.edges})`);
  L.push(`· ${r.cuts.length} hard cuts${r.cuts.length ? ": " + r.cuts.slice(0, 20).join(", ") + "s" : ""} (average shot ${(r.duration / (r.cuts.length + 1)).toFixed(1)}s)`);
  L.push(`· motion per second: ${r.motion.perSecond.join(" ")} (variation ${r.motion.contrast}${r.motion.contrast < 0.35 ? " — very flat, the pace may drag; mix fast and slow" : ""})`);
  if (r.loop.checked) L.push(r.loop.seamless ? `✓ first and last frames match (difference ${r.loop.firstLastDiff})` : `✗ first and last frames differ by ${r.loop.firstLastDiff} — the loop will jump`);
  return L.join("\n");
}

function probe(file) {
  const r = spawnSync("ffprobe", ["-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate,width,height:format=duration", "-of", "json", file], { encoding: "utf8" });
  if (r.status !== 0) throw new Error(`ffprobe cannot read ${file}: ${(r.stderr || "").trim()}`);
  const j = JSON.parse(r.stdout), s = j.streams[0];
  const [n, dd] = s.r_frame_rate.split("/").map(Number);
  return { fps: n / dd, width: s.width, height: s.height, duration: Number(j.format.duration) };
}

function decode(file) {
  const r = spawnSync("ffmpeg", ["-v", "error", "-i", file, "-vf", `scale=${W}:${H},format=gray`, "-f", "rawvideo", "-"], { maxBuffer: 1 << 30 });
  if (r.status !== 0) throw new Error(`ffmpeg could not decode ${file}: ${(r.stderr || "").toString().trim()}`);
  const size = W * H, out = [];
  for (let i = 0; i + size <= r.stdout.length; i += size) out.push(r.stdout.subarray(i, i + size));
  return out;
}

function locate(arg) {
  const p = resolve(arg);
  if (!existsSync(p)) throw new Error(`not found: ${arg}`);
  if (!statSync(p).isDirectory()) return p;
  const vdir = join(p, "output");
  if (existsSync(vdir)) {
    const vs = readdirSync(vdir).map((f) => /^v(\d+)\.mp4$/.exec(f)).filter(Boolean).map((m) => +m[1]).sort((a, b) => b - a);
    if (vs.length) return join(vdir, `v${vs[0]}.mp4`);
  }
  const fallback = join(p, "output.mp4");
  if (!existsSync(fallback)) throw new Error(`${arg} has no output/vN.mp4 or output.mp4`);
  return fallback;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const argv = process.argv.slice(2);
  const target = argv.find((a) => !a.startsWith("--"));
  if (!target) { console.error("usage: node tools/qa/motion-qa.mjs <video.mp4 | projectDir> [--loop] [--json]"); process.exit(2); }
  try {
    const file = locate(target);
    const info = probe(file);
    const r = { file, ...info, ...analyze(decode(file), info.fps, { loop: argv.includes("--loop") }) };
    console.log(argv.includes("--json") ? JSON.stringify(r, null, 2) : report(r));
    const bad = r.pops.length > 0 || r.orphans.length > 0 || (r.loop.checked && !r.loop.seamless);
    process.exit(bad ? 1 : 0);
  } catch (e) { console.error(e.message); process.exit(2); }
}
