---
name: video-autopilot
description: >
  YouTube / 短影音自動化製作技能（CapCut + ffmpeg + 腳本）。
  當使用者說「幫我規劃一支影片」「剪這支片」「CapCut 自動化」「autopilot 一支X」「Export」「換字幕」「ffmpeg」「短影音」「Shorts」「Reels」「audio mix」時觸發。
  整合腳本生成、CapCut JSON 操作、ffmpeg pipeline、交付前 QA 四大工作流。
---

# 🎬 video-autopilot

> 從「一句題目」到「可上傳的 mp4」。整合腳本規劃、CapCut 自動化、ffmpeg pipeline。
> 核心知識來自 [video-autopilot-kit](https://github.com/Hao0321/video-autopilot-kit)（MIT 授權）。

---

## ⚡ 30 秒決策樹 — 使用者說什麼，走哪條路？

| 使用者說 | 走哪裡 |
|---|---|
| 「規劃一支X」「autopilot」「全部你來」 | **Mode A** → 9 步完整套件 |
| 「發了 #N，數據是...」 | **Mode B** → 紀錄 outcome |
| 「review 表現」「optimize 預設」 | **Mode C** → pattern retrospective |
| 「跑 CapCut」「agent 剪片」「套模板」 | **CapCut Path B/C** → 讀 references/capcut-automation-sop.md |
| 「Export」「匯出 v[N]」 | **CapCut Path A** → Export only（最快）|
| 「換字幕文字」「換字體」「換位置」 | **CapCut Path D** → JSON direct edit（0 GUI）|
| 「靜音 vlog」「pure ffmpeg」 | **CapCut Path E** → ffmpeg only |
| 「字醜」「Pro paywall」「卡關」 | 讀 references/capcut-automation-sop.md 診斷表 |

---

## ☠️ 5 條鐵則（任何模式都適用）

1. **不編造數字** — 每個數字必有來源（WebSearch / 使用者 / 畫面）。沒 source → 寫 generic。
2. **先看畫面再寫文案** — 跑 `ffmpeg` 抽 frames 看過後，才寫對應 overlay 文案。
3. **字幕統一中央偏下** — Shorts: y=1280-1400；長片: y=820-930。不跳位。
4. **動態文字 / sticker → CapCut native，絕不 ffmpeg drawtext**。
5. **跑完先 self-critique** — 任一項未過 = 還沒完成。

---

## Mode A — Plan（一句題目 → 完整 publish 套件）

**觸發**：「規劃我下一支X」「我想拍X 全部你來」「autopilot」「end-to-end」

**最少需要**：
1. **題目**（X 是什麼）
2. **Angle**：工具 demo / 教學（High-Demo）/ 自我反思（High-Reflective）/ vlog / Shorts
3. **同時做 Shorts?**（預設 Y）

資訊不夠 → 最多問 1-2 個最關鍵問題，不要問 5 個。

**9 步工作流**：

```
1. Pre-flight         → 評分 ⭐⭐⭐⭐⭐ 五級，≤3⭐ 立刻停，列 3 個強化方向
2. 跨平台規劃         → 平台選擇 + 配比 + 長度甜蜜帶 + 結構框架
3. 腳本生成           → 依題目 + voice profile 生草稿，套對應 Register
                         Open loop + mini-promise + retention 結構
4. 腳本精簡           → 砍 20-25% 贅詞（lean preference）+ 招牌密度檢查
5. 留存預檢           → 預測 30s / 1min / 3min / 結尾 retention
6. Packaging War Room → TOP 1 title + 2 A/B 變體（不給 buffet）
                        TOP 1 thumbnail concept + 2 變體
7. 包裝補完           → Description / Hashtag / Tags
                        🎬 畫面規劃：依 script 段落映射視覺 cue（script-anchored）
8. 寫入 video_log.md  → 新 entry，編號 +1
9. 排監控時程         → 48-72h 提醒觸發 Mode B；1 週後 Mode C
```

**預設值（不問使用者）**：
- 發文時間：你的歷史實測最佳時段
- YT A/B Test：3 variants 並行 2 週
- 教學頻道 KPI 基準：CTR 6%+ / AVP 45%+ / 1-min retention 60%+
- 平台配比：1 長片 + 1-2 支 Shorts

---

## Mode B — Log Outcome（發布後紀錄）

**觸發**：「我發了 #N 數據是 CTR X% / AVD X」「記錄 #N 表現」

**步驟**：
1. 讀 video_log.md，補對應 entry 的 outcome
2. Tag ✅ what worked + ❌ what didn't
3. 自動路由：
   - 48-72h 後 → 跑 Analytics Decode（數據判讀）
   - 1 週後 → 跑 Iteration Engine

---

## Mode C — Optimize Patterns（從歷史學習）

**觸發**：「review 我的表現」「optimize 預設值」「retrospective」

≥5 個 outcome entry 才有意義。分析：
- 哪些 title 框架 CTR 最高？
- 哪些 thumbnail 贏 A/B Test 比例最高？
- 哪些發文時間表現好？

找到強 pattern → 主動 propose 更新本技能的預設值。

---

## CapCut Edit Pipeline — Path A-E

| Path | 用途 | ETA | Token 成本 |
|---|---|---|---|
| **A: Export only** | JSON 已 patched，純 Export | 5-8 分鐘 | 最低 |
| **B: 套單一模板 + Export** | 全部 caption 套同花字 | 25-40 分鐘 | 中 |
| **C: 多模板 + 貼圖 + Export** | marker/main/sub 分不同模板 | 60-90 分鐘⚠️ | 高 |
| **D: JSON direct edit** ⭐ | 換文字 / font / position，0 GUI | <1 分鐘 | 極低 |
| **E: 純 ffmpeg** | 靜音 vlog / CapCut 不可用時 | ~90 秒 | 極低 |

**Vlog autopilot 預設**：Path D + Path A（JSON edit → Export only）
- ❌ 不要反射 Path C（易撞 daily limit + Pro paywall）
- ✅ 純靜音 vlog → Path E

**Agent spawn 上限 = 2 / task**。連 2 個 agent 失敗 → 停止，改 Path D 或 user manual。

細節操作規則 → 讀 [references/capcut-automation-sop.md](references/capcut-automation-sop.md)
CapCut agent brief 模板 → 讀 [references/capcut-agent-brief-template.md](references/capcut-agent-brief-template.md)
JSON 直接編輯指南 → 讀 [references/capcut-json-direct-edit.md](references/capcut-json-direct-edit.md)

---

## 與 video-production-workflow 技能的分工

| 階段 | 技能 |
|---|---|
| 影片類型分流 / 腳本規劃 / 分鏡設計 | `video-production-workflow` |
| **腳本 → 完整 publish 套件 / 數據優化** | **`video-autopilot` Mode A-C** |
| **CapCut 自動化 / JSON 編輯 / ffmpeg pipeline** | **`video-autopilot` CapCut Path A-E** |
| 語音克隆配音 | `voxcpm2-voice-cloner` |

---

## 持續優化閉環

```
[題目] → Mode A → publish 套件
                ↓
          [錄製 raw 素材]
                ↓
    Edit Pipeline (Path A-E)
                ↓
        [polish + upload]
                ↓
         Mode B (Log Outcome)
                ↓
    ┌────────────┴────────────┐
    ↓                         ↓
48-72h Analytics          累積數據
1 週 Iteration         (≥5 entry → Mode C)
                              ↓
                    Pattern → 更新預設值
                              ↓
                        [越用越聰明 ✨]
```
