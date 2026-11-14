# 共用 Agent 技能包

這個目錄是給多個 Agent 共用的技能鏡像區，目標是讓 `OpenCode`、`AntiGravity` 與其他支援讀取本機技能的 Agent，都能用同一套短影音製作知識。

## 目前結構

- `skills/`：原始來源，之後的內容更新請以這裡為準。
- `.opencode/skills/`：OpenCode 使用的鏡像。
- `.agents/skills/`：其他 Agent 共用的鏡像。

## 已同步的技能

0. `social-post`（社群平台貼文規劃、撰寫、修訂與審慎成效分析）
1. `video-production-workflow`（前期策略與類型分類）
2. `video-autopilot`（Editkin v4、CapCut/ffmpeg 剪輯落地與機械閘門）
3. `video-use-editor`（對話式 AI 逐字稿精剪與贅詞消除）
4. `motion-explainer` 系列（原理解說動畫、圖片加強版、H3 AI 影片加強版、`motion-design`、`review-loop`）
5. `shanshiba-drama`（AI 短劇編劇，預設 9:16 直式 Shorts / 指定 16:9 橫式、MiniMax H3、試映讀本與鏡表創作）
6. `blender-previs`（Blender 預演與交付包，3D 白模鎖定機位與空間運鏡）
7. `hunyuan-browser-3d-animation`（混元網頁建模與角色動畫，Browser Use 圖片轉 3D、Mixamo 綁骨、Blender 修整）
8. `veo_promo_animation`（Flow/Veo 宣傳動畫影片工作流，貼文海報轉 1080p 影片、Google Flow / Gemini Veo 片段生成）
9. `ai-vlog`（AI 自動剪旅遊 Vlog，相簿照片與影片丟進去，用講的剪成 9:16 直式滿版 Vlog、細字排版、HEIC/HDR 防灰、預覽圖自檢、FFmpeg 一鍵輸出）

## 使用方式

- 社群平台貼文：使用 `social-post`；依授權樣本校準個人語氣，草稿與發布分開，沒有當輪確認與可用工具時不執行發布。
- 貼文／海報轉宣傳影片：明確提到「使用flow」或「使用veo」時調用 `veo_promo_animation`（分鏡確認、無字插圖、圖生影片、金色光帶轉場、片尾捲動名單）。
- 先看 `video-production-workflow`：用來判斷影片類型、平台、長度、字幕風格與剪輯策略。
- 原理解說與動畫製作：調用 `motion-explainer` / `motion-explainer-images` / `motion-explainer-video`。
- 短劇劇情創作與拆鏡：調用 `shanshiba-drama`。
- 3D 空間機位與運鏡預演：調用 `blender-previs`。
- 圖片轉 3D 角色模型與動畫：調用 `hunyuan-browser-3d-animation`（Browser Use 操作混元 3D 官網，串接 Mixamo 綁骨與 Blender 修整）。
- 實際剪輯與輸出：調用 `video-autopilot` 執行自動化（Editkin v4 唯一合約）。
- 如為口播/訪談/教學等說話素材：可調用 `video-use-editor` 進行逐字稿精準精剪。
- 如果需要更快上手，先讀各技能底下的 `references/` 文件，再回到 `SKILL.md`。

## 維護原則

- 以 `skills/` 作為單一來源。
- 內容更新後，同步到 `.agents/skills/` 與 `.opencode/skills/`。
- 所有說明文件與提示詞維持繁體中文。
- 不要刪除原始技能檔，除非有明確需求。

## OpenCode 設定

`opencode.json` 已加入這三個技能的允許設定（`allow`），讓 OpenCode 可以直接載入與使用。

## 給其他 Agent 的一句話

這份共用包的核心原則是「先規劃，再執行」。`video-production-workflow` 負責定義策略，`video-autopilot` 與 `video-use-editor` 負責落地執行。
