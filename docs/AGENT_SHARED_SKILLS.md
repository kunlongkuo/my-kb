# Agent 共用技能同步說明

這份文件是本次短影音技能同步的總覽，記錄目前已經完成的共用結構。

## 同步目標

- 讓短影音技能可以被 `OpenCode` 使用。
- 讓 `AntiGravity` 與其他 Agent 也能共同使用。
- 保持中文說明一致，避免每個 Agent 看到不同版本。

## 目前狀態

- `skills/` 已整理成繁體中文版本，作為主要來源。
- `.opencode/skills/` 已建立鏡像，供 OpenCode 讀取。
- `.agents/skills/` 已建立鏡像，供其他 Agent 共用。
- `opencode.json` 已加入技能權限設定。
- `social-post` 為社群貼文技能，涵蓋規劃、依授權樣本校準語氣、撰稿與審慎成效分析；不宣稱具備自動發布能力。

## 技能分工

### `social-post`

負責 Facebook、Instagram、Threads、YouTube、X 等社群內容的規劃、撰稿、修稿與成效檢視。個人語氣只依使用者可讀取且授權的樣本校準；樣本少或資料不足時標示不確定性，不推論保證觸及的公式。發布及留言操作須有可用工具、明確範圍與當輪確認。

### `video-production-workflow`

負責前期規劃與策略判斷，包括：

- 影片類型分類
- 平台與受眾判斷
- 拍攝與剪輯策略
- 字幕、節奏、封面與腳本規劃

### `video-autopilot`

負責實際執行與輸出，包括：

- 剪輯流程落地（Editkin v4 唯一合約）
- `CapCut` / `ffmpeg` / JSON 原子編輯
- 機械閘門（Fail-Closed Gates）與產出 QA、紀錄
- 可重複使用的自動化流程與統一濾鏡庫

### `video-use-editor`

負責對話驅動的 AI 影片語音精剪（基於 ElevenLabs Scribe / browser-use/video-use）：

- 口播、教學、訪談等講話素材的精準剪接
- 自動逐字稿、刪除贅詞（filler words、uh、um）、死空間與口吃
- 逐字級對齊、無損拼接、音訊淡入淡出（30ms audio fade）與字幕燒錄

### `motion-explainer` 系列（原理解說動畫與 AI 影片）

基於 HeyGen 開源 HyperFrames（HTML + GSAP → MP4）的原理解說動畫生成流水線，由 mathruffian-dot 開源：

- **`motion-explainer`**（基本版）：繁中 edge-tts 旁白、字幕逐句高亮、三色主題配色、源石黑體粗體自動瘦身。
- **`motion-explainer-images`**（圖片加強版）：基本版 ＋ Wikimedia Commons 授權照片「證據卡」（自動雙色濾鏡）＋ Codex 生成示意圖「氛圍背景」。
- **`motion-explainer-video`**（影片加強版）：圖片加強版 ＋ **MiniMax H3 AI 生成影片** ＋ `fix_voice.py` 唸錯字整句等比時長修復工具。
- **`motion-design`**：動畫品味規則（緩動、節奏、停留、中文排版、三色配色數值化）。
- **`review-loop`**：自我審查迴圈（Contact sheet 截圖拼接檢查表）。

### `blender-previs`（3D 空間預演）

山獅霸 AI 短劇的 Blender 預演與交付包，專注於鏡位契約、白模空間防漂移、布置圖檢查與相機軌道運鏡規範。

### `hunyuan-browser-3d-animation`（圖片轉 3D 角色建模與動畫）

以 Browser Use 操作騰訊混元 3D 官網（`3d.hunyuan.tencent.com`），將單張人物圖片製成 3D 模型，接續 Mixamo 綁骨、套動作與 Blender 修整匯出。預設將繁重建模工作派給 subagent，主對話只派工與驗收成果。

### `veo_promo_animation`（Flow/Veo 宣傳動畫影片工作流）

將得獎貼文、活動海報一條龍轉為 1080p 成果影片與社群版。分鏡腳本 → Codex 無字構圖圖 → Gemini 背景音樂與 TTS 旁白 → Google Flow / Gemini Veo 圖生影片 → 程式疊加金字標題、資訊標籤與對齊字幕 → 金色光帶轉場與片尾捲動名單。嚴格落實「每一步先確認才做」與「插圖不含文字」。

## 建議使用順序

1. 先讀 `video-production-workflow`：決定影片類型、平台、長度、受眾與策略。
2. 依任務類型分流執行：
   - 原理解說動畫、三色教學片、公式原理展示 ➔ 調用 **`motion-explainer`** 系列（可依需求選基本版、圖片版或 H3 影片版）
   - 得獎公告、活動海報轉 1080p 宣傳短片（使用者指定「使用flow」或「使用veo」） ➔ 調用 **`veo_promo_animation`**
   - 需要範本花字、貼圖、CapCut/ffmpeg 剪輯、Editkin v4 自動化或無說話素材 ➔ 調用 **`video-autopilot`**
   - 說話口播、訪談、教學且需依逐字稿自動精剪贅詞與死空間 ➔ 調用 **`video-use-editor`**
3. 若要交給其他 Agent，先看 `.agents/README.md`

## 維護原則

- 更新內容時，以 `skills/` 為來源。
- 同步時要一起更新 `.agents/skills/` 與 `.opencode/skills/`。
- 保持繁體中文，讓各 Agent 的理解一致。

## 整合歷程

- **2026-10-21**：引進 mathruffian-dot 之 **`claude-motion-explainer` 系列技能**（基本版、圖片加強版、影片加強版、`motion-design` 與 `review-loop`），建立 HyperFrames 動畫與 H3 AI 影片生成能力，完成跨 Agent 三重鏡像（`skills/`、`.agents/skills/`、`.opencode/skills/`）與 `opencode.json` 授權。
- **2026-10-20**：整合上游/共創倉庫 [FreeTWAI/video-autopilot-kit](https://github.com/FreeTWAI/video-autopilot-kit)（v0.23.0 / 架構 7.0）規範：
  - 確立 **Editkin v4** 唯一剪輯合約（證據 → 企劃 → 審計 → 原子套用 → 渲染）。
  - 確立三條同構生產線：教學長片（`script_gate`）、直式短影音（`shorts_gate` 含平台感知片長帶）、線上訪談（`interview_gate` 證據閘門）。
  - 引進機械閘門（Fail-Closed Gates）、競品拆解標準（Teardown）與統一濾鏡規範（Unified Filter Registry）。
  - 已全數鏡像同步至 `skills/`、`.agents/skills/` 與 `.opencode/skills/`。

## 補充

如果後續還要擴充新的短影音技能，建議沿用這個結構新增：

- `skills/<新技能>/`
- `.agents/skills/<新技能>/`
- `.opencode/skills/<新技能>/`


