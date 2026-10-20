# Editkin v4 剪輯合約規範

> 本規範依據 `FreeTWAI/video-autopilot-kit`（v0.23.0 / 架構 7.0）的核心合約制定，為短影音與長片剪輯自動化之唯一執行標準。

---

## 核心哲學：證據為先（Evidence-First）

1. **唯一 Editor Contract**：
   - 流程：`素材證據（Source Evidence）→ 剪輯計畫（Edit Plan / v4）→ 機械審查（Gate Audit）→ 原子套用（Atomic Apply）→ 最終渲染（Render）`。
   - 舊版的 CapCut GUI 點擊、未經審查的草稿 JSON 或 Path A-E 僅作為基準與底層驅動，不得繞過審查合約。
2. **決策必有證據**：
   - 影片中對產品、功能、數據、價格、成效、人物言論或授權的陳述，**必須有可查證的素材證據或官方來源**（Citation-First）。
   - 缺乏證據支撐時，**一律退回乾淨切鏡（Clean Cut）或乾淨定格（Clean Hold）**，絕不憑空合成或臆造畫面。
3. **不可變收據（Immutable Receipts）**：
   - 每次執行編譯為 `hao.video-autopilot.edit-plan/v4`，套用過程記錄不可變狀態收據；遇中斷時自驗證點安全復原，未確認狀態前不重複執行。

---

## 執行五階段（5-Stage Lifecycle）

```
[原始素材/Prompt]
       │
       ▼
 1. 證據檢驗 (Inspect)      ── 抽格查核 (ffmpeg / ffprobe)、確認真實畫面與來源
       │
       ▼
 2. 企劃編譯 (Compile Plan) ── 生成符合 edit-plan/v4 的 DAG 與時間軸
       │
       ▼
 3. 機械閘門 (Audit Gate)   ── Fail-Closed 機械閘門自動攔截（字句/節奏/平台邊界）
       │
       ▼
 4. 原子套用 (Atomic Apply) ── 批次寫入 CapCut JSON / 調用 ffmpeg 合成
       │
       ▼
 5. 渲染與 QA (Render & QA) ── 驗證音量 LUFS、安全區、字幕對齊，產出 Review Bundle
```

---

## 落地工具鏈與邊界

- **Python & ffmpeg**：跨平台素材分析、正規化、影格抽樣、音訊測量（LUFS）與 QA 支援層。
- **CapCut JSON 編輯**：原生字幕、花字樣式、貼圖圖層的原子寫入。
- **私隱保護**：個人 media、頻道後台數據、API 金鑰與 profiles 一律保留在本機，不進入共用 repo。
