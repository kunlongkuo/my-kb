---
name: veo_promo_animation
description: 僅在使用者明確說「使用veo」或「使用flow」（大小寫、空格不拘，例如「使用 Veo」「使用Flow」）時觸發；只說「製作動畫」「宣傳影片」等未提到 veo／flow 的要求不觸發。一條龍完成：分鏡腳本 → Codex 生成無字構圖圖（逐鏡確認）→ Gemini 生成無人聲背景音樂 → Gemini TTS 旁白（先試聽）→ 圖生影片讓每鏡真的動起來（預設 Google Flow，其次 Gemini Veo，由使用者選）→ 程式疊上金字標題、資訊標籤、對齊旁白的字幕、粒子與金色光帶轉場 → 片尾名單 → 串接混音 → 1080p 成品與社群／手機版。以 2026-11 嘉義市教育 AI 績優成果宣傳片為範本。
---

# Flow 製作影片工作流（Agent Skill）

範本：嘉義市 115 年教育 AI 及數位學習績優成果宣傳片（1 分 51 秒，10 鏡＋片尾名單）。
`<skill>` = 本 skill 資料夾；`<專案>` = 使用者的專案根目錄。新產物一律放 `<專案>/Codex/`。

## 核心原則

1. **要真的會動**：每鏡都用 Flow／Veo 圖生影片，不是圖片輪播＋推拉。
2. **插圖不含字**：所有中文（標題、校名、教案名、數字）由程式疊上，避免 AI 寫錯字。
3. **事實照原文**：校名、人名、教案名逐字取自使用者提供的貼文／海報；兩份來源不一致時（例如「宣信」與「宜信」）要問使用者。
4. **逐步確認**：分鏡 → 構圖圖 → 旁白試聽 → 第一鏡審查版，每一步都先給使用者看。使用者說「直接做到成品」後，才連續做完。
5. 交辦外部 AI（Codex、Gemini、Flow）會用到使用者的帳號額度，先說明要做什麼並取得同意。

## 流程

### 1. 分鏡腳本（先確認）
寫 `<專案>/Codex/分鏡腳本.md`：8～12 鏡、每鏡 7～12 秒，欄位包含畫面構圖、疊字內容、旁白。
- 第 1 鏡做開場，第 2 鏡交代背景，接著是總成績和各獎項，最後一鏡是感謝或結尾，片尾再接名單捲動（約 16 秒）。
- 名單太長、旁白念不完時，正片旁白只念重點，全部名單放片尾。
- 配色參考使用者給的海報（範本是紅、藏青、金，配米白底）。

### 2. 構圖圖（Codex 生圖；分派前取得同意並請使用者選模型）
- 先說明要交給 Codex、建議的模型與思考程度，等使用者同意。可用模型見 `~/.codex/models_cache.json`。
- 依 `references/prompts_example.json` 的格式寫 `prompts.json`：一段共用 style，加上每鏡的畫面描述。
- `python "<skill>/scripts/storyboard_images.py" --prompts prompts.json --out "<專案>/Codex/images/storyboard" --model <模型> --effort <程度>`
  - 腳本會依序生成。長任務用背景執行，約 1 分鐘一張；先生第 1 張確認畫風，再生其餘。
- 用 ffmpeg xstack 拼成總覽圖再審（省 token）。檢查四件事：有沒有文字、地標是否正確（台灣城市不能出現高樓或台北 101）、人物有沒有臉、各鏡畫風是否一致。
- 要修改時，用 `--edit` 加 edits.json（以原圖當底圖），檔名會加上 `v2`。修好後傳總覽圖給使用者確認。

### 3. 背景音樂（Gemini，無人聲）
使用者沒提供音樂時，依 `references/browser_gemini_flow.md` 到 Gemini 生成 MP3，存到 `Codex/audio/`。Claude 聽不到聲音，「無人聲」要請使用者試聽確認。

### 4. 旁白（任一 TTS，例如 Gemini TTS）
- 先只生成第 1 鏡給使用者試聽，確認聲線後才批次生成；音檔存成 `<id>.mp3`。
- 生成後跑：`python "<skill>/scripts/voice_timing.py" --manifest <配音清單.json> --audio-dir <mp3資料夾> --out "<專案>/Codex/anim/voice_timing.json"`
- 每鏡片長 ≈ delay（0.4～0.6 秒）＋ 旁白長 ＋ 0.6 秒。

### 5. 圖生影片（預設 Flow，其次 Gemini Veo；先讓使用者選）
- 進到這一步前，先問使用者要用哪一個，Flow 列為建議：
  - **Google Flow（建議）**：可指定首幀、一次排入多鏡、可選模型與數量；Veo 3.1 Fast 每支 8 秒、720p，用 Flow 點數。
  - **Gemini（Veo）**：每支約 10 秒，但每日可生成的次數很少。
  - 觸發詞是「使用flow」時預設 Flow，「使用veo」時預設 Gemini，但仍請使用者確認。
  - 選定的工具額度或點數用完時，先告知使用者，再改用另一個。
- 操作步驟、JS 輔助片段和額度判斷，見 `references/browser_gemini_flow.md` 與 `scripts/veo_browser.js`。
- 動作提示詞用英文，固定開頭和結尾（見 prompts_example 的 `veo_motion_common`）。
  - 要疊標籤對位的鏡頭，一定加「locked-off static camera」。
  - 結尾城市鏡要禁止新增建築和人物。
- 一般流程：先做第 1 鏡給使用者審，再一次排入其餘各鏡（Flow 可在同一專案連續送出；Gemini 用多個分頁並行）。
- 下載後歸位：`python "<skill>/scripts/identify_clips.py" --config project.json --refs <構圖圖資料夾>`。先預覽比對結果，確認無誤再加 `--apply`。
- 每支影片抽頭、中、尾三格檢查有沒有變形、多出的建築、人物換臉；有問題就重生。

### 6. 疊加層（scenes.py）
- 複製 `references/project_example.json` 到 `<專案>/Codex/anim/project.json`，改路徑和每鏡的 dur、delay、voice。快速動作的鏡加 `"interp": "dup"`。
- 複製 `references/scenes_example.py` 到 `<專案>/Codex/anim/scenes.py` 改寫。可用的元件見 `scripts/fxlib.py`：
  - Title、Ribbon、Panel：標題、緞帶副標、標題卡
  - Tag：學校與教案資訊標籤
  - AwardBadge：獎項光環加數字跳動
  - voice_caption：對齊旁白停頓的字幕
  - Particles、GoldSweep：金色光點、金色光帶轉場
- 版面位置依實際 Flow／Veo 影片的擷取畫面決定。原則見 scenes_example.py 開頭說明。
- 產生疊加層：`python "<skill>/scripts/render_overlay.py" --config project.json --all`（或用 `--scene s01` 只做一鏡）
- 合成每鏡畫面：`python "<skill>/scripts/render_clip.py" --config project.json --all`
  - 補幀方式：放慢 1.15 倍以內直接複製畫格，超過就用畫格混合。**禁用 minterpolate**，插畫人物會糊掉。
- 第一鏡審查版：可先用 assemble 時只放一鏡的 project.json 輸出，或直接把 parts/s01.mp4 混旁白後給使用者看。

### 7. 片尾與串接
- 把最後一鏡的最後一格存成 `credits.bg`：`ffmpeg -sseof -0.2 -i <最後一鏡>_veo.mp4 -frames:v 1 -vf scale=1920:1080 <bg.png>`
- 片尾名單：`python "<skill>/scripts/credits.py" --config project.json`
- 先檢查時間軸：`python "<skill>/scripts/assemble.py" --config project.json --dry-run`
  - 看 voice_gaps，不能有負數（負數代表旁白重疊）。
- 正式輸出：`python "<skill>/scripts/assemble.py" --config project.json`
  - 各鏡在金色光帶下溶接，旁白依時間軸擺放。
  - 背景音樂太短時會自動延長（重複中段並交叉淡化），旁白出現時自動壓低，最後統一響度到 -15 LUFS。

### 8. 驗收與交付
- 用 ffprobe 確認長度和規格；用 ebur128 確認響度約 -15 LUFS、峰值 ≤ -1.5；用 silencedetect 確認除片尾外沒有長段靜音。
- 抽轉場處和每鏡中段的畫面拼成一張圖檢查。
- 另外輸出兩個版本：
  - 社群版：`-crf 23 -maxrate 6M -bufsize 12M`
  - 手機預覽版：720p、1.8Mbps，控制在 30MB 以內，用 SendUserFile 傳給使用者
- 如實回報：Claude 看不到完整影片、也聽不到聲音，哪些只做了技術檢查要講清楚；並列出 Flow／Veo 原片本身的瑕疵。

## 參考
- `references/lessons.md`：這次踩過的坑，動工前務必先讀。
- `references/browser_gemini_flow.md`：Flow、Gemini 的操作步驟，以及下載被擋時的處理方式。
- `references/scenes_example.py`、`references/project_example.json`、`references/prompts_example.json`：範本專案的實際設定。
