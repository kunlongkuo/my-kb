# veo_promo_animation：Flow 製作影片工作流（Agent Skill）

把一篇成果貼文或活動海報做成 1080p 成果影片：分鏡腳本、無字插圖、Google Flow／Gemini Veo 生成影片片段、標題與字幕、旁白、背景音樂與片尾名單，每一步都先給你確認。
作者：奕鈞老師（IJUN AI）｜範例：嘉義市 115 年教育 AI 及數位學習績優成果影片

## 安裝

1. 把整個 `veo_promo_animation` 資料夾放到 `~/.claude/skills/`（Windows：`C:\Users\<你的帳號>\.claude\skills\`）。
2. 重新開啟 Claude Code，對 Claude 說「**使用flow** 把這篇貼文做成影片」或「**使用veo** …」即可啟動；做到影片片段時，AI 會請你選擇 Flow（建議）或 Gemini。
   觸發詞只有「使用veo」「使用flow」。

## 需要的環境

| 項目 | 用途 |
|---|---|
| Python 3.11+、Pillow | 加上標題與字幕、製作片尾名單、比對下載的影片 |
| ffmpeg／ffprobe | 放大、變速、串接、混音 |
| 思源黑體／思源宋體 TC（Noto Sans TC、Noto Serif TC 可變字型） | 中文字幕與標題（`scripts/fxlib.py` 開頭可改字型路徑） |
| Claude in Chrome 擴充功能 | 操作 Flow、Gemini 網頁（圖生影片與背景音樂） |
| Google 帳號（Flow 或 Gemini 可用 Veo） | 生成影片片段、背景音樂 |
| Codex CLI（選用） | 生成插圖；也可以改用其他生圖工具，只要插圖不含文字 |
| 任一 TTS（例如 Gemini TTS） | 旁白配音，每句一個 `<id>.mp3` |

## 資料夾內容

- `SKILL.md`：給 Claude 的完整流程（分鏡 → 構圖圖 → 音樂 → 旁白 → Flow／Veo 影片片段 → 標題與字幕 → 串接 → 交付）。
- `scripts/`：
  - `storyboard_images.py`：用 Codex 依序生成或修改插圖
  - `voice_timing.py`：偵測旁白停頓，讓字幕對齊
  - `identify_clips.py`：比對影片的第一個畫面，把下載的影片對應到分鏡順序
  - `render_overlay.py`、`fxlib.py`：標題、標籤、字幕與轉場效果
  - `render_clip.py`：每段影片放大、調整速度，加上標題與字幕
  - `credits.py`：片尾名單捲動
  - `assemble.py`：串接、延長音樂、混音
  - `veo_browser.js`：操作 Flow／Gemini 的 JS 輔助片段
- `references/`：製作注意事項、Flow／Gemini 操作步驟、範例設定（project.json、scenes.py、生圖提示詞）。

## 注意

- Flow、Gemini、Codex 都會使用你自己的帳號額度或點數；預設建議用 Flow，Gemini 的 Veo 每日次數較少。
- Chrome 預設會擋住同一網站連續下載多個檔案，Flow 下載前請先允許「自動下載多個檔案」。
- 插圖一律不含文字，中文由程式疊上；校名、人名請以原始公告為準並自行校對。
