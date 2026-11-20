import test from "node:test";
import assert from "node:assert/strict";

import { analyze, W, H } from "../motion-qa.mjs";

const N = W * H;
const flat = (v) => new Uint8Array(N).fill(v);
// 緩慢漸變：每格 +1 亮度，相鄰差 1（> 靜止門檻 0.25、< 閃現門檻 6）
const ramp = (n, start = 50) => Array.from({ length: n }, (_, i) => flat(start + i));

test("全靜止 2 秒：報一段靜止，無閃現無硬切", () => {
  const r = analyze(Array.from({ length: 60 }, () => flat(100)), 30);
  assert.equal(r.pops.length, 0);
  assert.equal(r.cuts.length, 0);
  assert.equal(r.dead.length, 1);
  assert.ok(r.dead[0].seconds >= 1.9);
});

test("中間插一格白：報單幀閃現，不算硬切", () => {
  const f = ramp(60);
  f[30] = flat(255);
  const r = analyze(f, 30);
  assert.deepEqual(r.pops.map((p) => p.at), [1]);
  assert.equal(r.cuts.length, 0);
});

test("亮度跳變後不回頭：報硬切，不算閃現", () => {
  const f = [...ramp(30, 20), ...ramp(30, 200)];
  const r = analyze(f, 30);
  assert.equal(r.pops.length, 0);
  assert.deepEqual(r.cuts, [1]);
});

test("持續緩變：無靜止", () => {
  const r = analyze(ramp(60), 30);
  assert.equal(r.dead.length, 0);
});

test("循環：首尾相同判 seamless，不同判不接", () => {
  assert.equal(analyze([flat(10), flat(80), flat(10)], 30, { loop: true }).loop.seamless, true);
  assert.equal(analyze([flat(10), flat(80), flat(90)], 30, { loop: true }).loop.seamless, false);
});

test("小區塊閃一格（一格 8×6 全白）：分格抓得到，並回報位置", () => {
  const f = ramp(60);
  const g = new Uint8Array(f[30]);
  for (let y = 48; y < 54; y++) for (let x = 40; x < 48; x++) g[y * W + x] = 255;
  f[30] = g;
  const r = analyze(f, 30);
  assert.equal(r.pops.length, 1);
  assert.ok(r.pops[0].y > 0.9);
});

test("小物體持續移動（像白板的筆）：候選太密 → 判偵測失效，不列不計", () => {
  const f = Array.from({ length: 300 }, (_, i) => {
    const g = flat(250);
    const x0 = (i * 7) % (W - 4);                // 每格往右 7px，到底再從左邊進來（10 秒）
    for (let y = 20; y < 26; y++) for (let x = x0; x < Math.min(W, x0 + 4); x++) g[y * W + x] = 0;
    return g;
  });
  const r = analyze(f, 30);
  assert.equal(r.suppressed, true);
  assert.ok(r.popCandidates > 0);
  assert.equal(r.pops.length, 0);
});

test("兩段之間夾一格別的畫面：報孤兒格", () => {
  const f = [...ramp(30, 20), flat(0), ...ramp(30, 200)];
  const r = analyze(f, 30);
  assert.deepEqual(r.orphans.map((o) => o.at), [1]);
});

test("一般硬切：不是孤兒格", () => {
  assert.equal(analyze([...ramp(30, 20), ...ramp(30, 200)], 30).orphans.length, 0);
});

// 突變自檢：把閃現格改成「不回頭」，閃現必須消失（確認判定真的看前後兩格）
test("突變自檢：閃現格之後不回到原亮度 → 不報閃現", () => {
  const f = ramp(60);
  for (let i = 30; i < 60; i++) f[i] = flat(255);
  assert.equal(analyze(f, 30).pops.length, 0);
});

test("第 0 格全平、1 秒後才畫上：報空白封面與填滿時間", () => {
  const drawn = new Uint8Array(N).fill(240);
  for (let i = 0; i < N; i++) if ((i % W) % 8 < 2) drawn[i] = 20;   // 直條紋：far 25%、edges 夠多
  const f = [...Array.from({ length: 30 }, () => flat(240)), ...Array.from({ length: 30 }, () => drawn)];
  const r = analyze(f, 30);
  assert.equal(r.firstFrame.empty, true);
  assert.equal(r.firstFrame.contentAt, 1);
});

test("第 0 格就有內容：不報空白", () => {
  const drawn = new Uint8Array(N).fill(240);
  for (let i = 0; i < N; i++) if ((i % W) % 8 < 2) drawn[i] = 20;
  const r = analyze(Array.from({ length: 30 }, () => drawn), 30);
  assert.equal(r.firstFrame.empty, false);
  assert.equal(r.firstFrame.contentAt, 0);
});
