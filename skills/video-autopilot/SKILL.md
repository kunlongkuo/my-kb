---
name: video-autopilot
description: 依據 Editkin v4 剪輯合約與機械閘門，執行短影音與長片製作落地流程，整合 CapCut JSON 原子編輯、ffmpeg 處理、統一濾鏡庫與發布 QA。適用於策略確認後的影片落地、輸出、審片與迭代自動化。
---

# 短影音與長片自動執行（Video Autopilot）

本技能依據 `FreeTWAI/video-autopilot-kit`（v0.23.0 / 架構 7.0）標準，以 **Editkin v4 唯一合約** 與 **機械閘門（Fail-Closed Gates）** 為核心，負責將前期策略企劃與素材證據轉化為高完成度的發布套件。

本技能負責「精密執行與品質把關」，不代替使用者臆造未經證實的故事；若策略或素材不明確，先由 `video-production-workflow` 釐清，不硬切盲剪。

---

## 🧭 四大核心運作原則（Operating Contract）

1. **證據為先（Evidence-First）**：
   - 畫面陳述的任何數據、價格、功能與論點，必有客觀來源（Citation-First）。
   - 缺乏素材證據時，退回乾淨切鏡（Clean Cut）或定格，不憑空捏造。
2. **唯一剪輯合約（Editkin v4）**：
   - 標準流程：`素材證據查核 → 企劃編譯 (edit-plan/v4) → 機械閘門審查 (Gate Audit) → 原子套用 (Atomic Apply) → 渲染輸出`。
3. **機械閘門嚴控（Fail-Closed Gates）**：
   - 閘門不合規即刻攔截（Exit != 0），絕不靜默出片。
4. **統一濾鏡與視覺調色（Color & Filter Rule）**：
   - 全片調色（LUT / Purity）在流程中僅套用一次，且**必須先於字幕、圖卡與貼圖**。
   - 轉場必須具備敘事動機（章節翻頁、話題轉換），無動機則維持自然跳切。

---

## 🏭 三條同構生產線

| 生產線 | 專屬閘門 | 檢核核心 |
| :--- | :--- | :--- |
| **教學長片** (`longform_maker`) | `script_gate` | 觀眾語言過濾（行話/生僻詞攔截）、留存率節奏波形預檢。 |
| **直式 Shorts / Reels** (`shorts_autopilot`) | `shorts_gate` | 9 條結構硬規則、平台感知片長帶（YT 甜蜜帶不生搬至 IG）、換句÷剪點節奏。 |
| **線上訪談** (`interview_autopilot`) | `interview_gate` | I-A～I-E 數據來源審核：未經官方查證的來賓數據不上鏡。 |

---

## 🛠️ 作業模式與落地路徑

### 作業模式
- **模式 A（Plan）**：依主題或頻道目標，由素材證據出發，產出腳本、分鏡、剪輯計畫與發布包。
- **模式 B（Log Outcome）**：發布後記錄播放成效、留存曲線與觀眾回饋。
- **模式 C（Optimize Patterns）**：自歷史數據學習，提煉最佳 Title/縮圖框架與節奏模式。

### 落地工具鏈
- **CapCut JSON 原子編輯**：字幕、花字樣式、貼圖圖層原生處理。
- **ffmpeg & ffprobe**：影格抽檢、音訊測量（-14 LUFS）、格式轉碼與純剪備援。
- **競品量化拆解（Teardown）**：精準計算競品之每分鐘刀數、換句率與視覺切換節奏。

---

## 📚 參考指引

- [Editkin v4 剪輯合約規範](references/editkin-v4-contract.md)
- [機械閘門與競品拆解規範](references/mechanical-gates-and-teardown.md)
- [統一濾鏡庫與畫面美學規範](references/unified-filter-library.md)
- [CapCut 自動化 SOP](references/capcut-automation-sop.md)
- [CapCut JSON 直接編輯指南](references/capcut-json-direct-edit.md)
- [CapCut Agent Brief 模板](references/capcut-agent-brief-template.md)
- [工作流程摘要](references/video-autopilot-workflow.md)
