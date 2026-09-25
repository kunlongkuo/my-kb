---
name: video-use
description: 以對話驅動的 AI 影片剪輯框架。支援自動逐字稿、精準剪接（cut filler words、死空間、口吃）、色彩分級、動態字幕燒錄、動畫疊層。適合 talking head、教學、訪談、旅遊、任何需要「說話精剪」的影片。說「用 video-use 剪」「AI 剪接」「自動逐字稿剪片」「幫我剪掉 uh um」時觸發。
---

# video-use 繁體中文使用說明

> 整合入口：[`video-use-editor`](file:///i:/Mark/my-kb/.agents/skills/video-use-editor/SKILL.md)
> Repo：`i:\Mark\my-kb\skills\video-use\`
> 適用版本：browser-use/video-use（2026-09-23 clone）

---

## 一、這個工具是什麼？

`video-use` 是一個「用說話剪影片」的 AI 剪輯框架。你不用學 CapCut、不用學時間軸，只需要：

1. 把原始素材丟進一個資料夾
2. 告訴 AI 你要剪成什麼
3. AI 讀完逐字稿、提出剪接策略，你確認後自動產出 `final.mp4`

**最適合的素材類型**：口播影片、講座、訪談、教學錄影、Vlog 旁白、多 take 說話素材。

**不適合**：純 B-roll 剪接、音樂卡點、大量視覺特效 → 改用 `video-autopilot`。

---

## 二、核心原則

1. **AI 從逐字稿推理，不掃描影片。** 唯一保留的衍生產物是字詞級逐字稿（`takes_packed.md`），其餘—贅詞標記、重拍偵測、鏡頭分類—都在決策時即時推導。
2. **音訊為主，畫面為輔。** 切點候選來自語音邊界與靜音間隔，只在決策點才鑽入畫面。
3. **詢問 → 確認 → 執行 → 迭代 → 記憶。** 策略未確認前絕不動刀。
4. **不預設影片類型。** 先看素材，再問使用者，最後才剪。
5. **自評後才給使用者看。** 不會出貨的輸出不會展示。

---

## 三、環境確認（每次開工前）

```powershell
# 1. ffmpeg 是否在 PATH
ffmpeg -version

# 2. Python deps 是否安裝
python -c "import librosa, PIL, numpy; print('OK')"

# 3. ElevenLabs API Key 是否存在
Get-Content i:\Mark\my-kb\skills\video-use\.env
# 應顯示：ELEVENLABS_API_KEY=sk_...
```

全部 OK 才能開始。如果 Key 遺失，重新填入 `.env` 即可。

---

## 四、完整工作流程（8 個步驟）

### 步驟 1：建立素材資料夾，放入原始檔

把所有要剪的影片放進同一個資料夾，例如：

```
i:\Videos\2026-09-23-tutorial\
├── take_01.mp4
├── take_02.mp4
└── take_03.mp4
```

**原始檔永遠不會被修改**，所有輸出都在子資料夾 `edit/` 裡。

輸出目錄結構：

```
edit/
├── project.md               <- session 記憶，每次追加
├── takes_packed.md          <- 字詞級逐字稿，AI 的主要讀取視角
├── edl.json                 <- 剪接決策清單
├── transcripts/<name>.json  <- 快取的原始 Scribe JSON
├── animations/slot_<id>/    <- 各動畫的素材 + 渲染結果
├── clips_graded/            <- 含色彩分級與 fade 的逐段抽取
├── master.srt               <- 輸出時間軸字幕
├── preview.mp4
└── final.mp4
```

---

### 步驟 2：自動逐字稿（Transcribe）

切換到 video-use 目錄，呼叫 ElevenLabs Scribe：

```powershell
cd i:\Mark\my-kb\skills\video-use

# 多檔並行（建議，4 個 worker 同時跑）
python helpers/transcribe_batch.py "i:\Videos\2026-09-23-tutorial"

# 單檔（有多個說話者時加 --num-speakers N）
python helpers/transcribe.py "i:\Videos\2026-09-23-tutorial\take_01.mp4" --num-speakers 2
```

逐字稿會快取在 `edit/transcripts/take_01.json`。**同一個源碼檔只會打一次 API，不重複計費。**

---

### 步驟 3：打包成可讀逐字稿

```powershell
python helpers/pack_transcripts.py --edit-dir "i:\Videos\2026-09-23-tutorial\edit"
```

這個指令把所有 JSON 逐字稿合併成一份 `edit/takes_packed.md`，格式如下：

```
## take_01  (duration: 43.0s, 8 phrases)
  [002.52-005.36] S0 這樣做的話效率可以提升九成。
  [006.08-006.74] S0 我們解決了這個問題。
```

每一行前面的 `[秒數-秒數]` 是精確的字級時間戳，AI 靠這個決定在哪裡切。靜音 ≥ 0.5 秒或說話者切換時斷句。

---

### 步驟 4：對話確認剪接策略

AI（Antigravity）讀完 `takes_packed.md` 之後，會用白話告訴你：

- 每個 take 的內容是什麼
- 有哪些 uh/um/贅詞/死空間/重複跑
- 哪個 take 的某句話講得最好
- 建議的剪接結構（例如：HOOK → 問題 → 解決方案 → CTA）

然後 AI 會詢問你：

- 目標長度多少秒？
- 要放到哪個平台（橫向 16:9 / 直向 9:16 / 方形）？
- 需要字幕嗎？什麼風格？
- 需要色彩分級嗎？
- 需要動畫疊層嗎？

**在你說「可以」之前，AI 不會動任何一刀。**

---

### 步驟 5：執行剪接

你確認策略後，AI 會：

1. 產生 `edit/edl.json`（剪接決策清單）
2. 呼叫 `render.py` 執行：抽段 → 串接 → 疊層 → 字幕（字幕最後上）

```powershell
# 預覽版（720p，速度快）
python helpers/render.py "i:\Videos\folder\edit\edl.json" `
  -o "i:\Videos\folder\edit\preview.mp4" --preview

# 正式版（原始解析度）
python helpers/render.py "i:\Videos\folder\edit\edl.json" `
  -o "i:\Videos\folder\edit\final.mp4"

# 同時產生 master.srt
python helpers/render.py ... --build-subtitles
```

---

### 步驟 6：AI 自評（展示前自動執行）

渲染完成後，AI 會在每個剪接點前後 1.5 秒做 `timeline_view` 視覺檢查：

```powershell
# 鑽取特定時段的影格 + 音波圖（秒）
python helpers/timeline_view.py "i:\Videos\folder\edit\preview.mp4" 10.5 13.0
```

自評檢查項目：
- 視覺跳幀/閃爍
- 切接點有 pop 聲（30ms fade 沒生效）
- 字幕被動畫蓋住（Hard Rule 1 違反）
- 動畫跑錯幀（Hard Rule 4 違反）

同時抽查：開頭 2 秒、結尾 2 秒、中間 2-3 個點，確認色彩分級一致性與字幕可讀性。

**只有自評通過，AI 才會把預覽給你看。最多自評 3 次，3 次後仍有問題直接回報，不無限循環。**

---

### 步驟 7：迭代修改

看完預覽，直接用說的給回饋，例如：

> 「第 15 秒那個停頓太長，剪短一點」
> 「最後 CTA 那句換成 take_03 的版本」
> 「字幕改成正常大小寫，不要全大寫」

AI 會更新 `edl.json` 並重新渲染，**不會重新打逐字稿 API**。

---

### 步驟 8：最終輸出，更新 project.md

確認滿意後：

```powershell
python helpers/render.py ... -o final.mp4
```

AI 會在 `edit/project.md` 追加本次 session 的決策紀錄，下次打開同一個資料夾時可以無縫接手。

---

## 五、Helpers 完整速查表

| 指令 | 功能 | 常用參數 |
|------|------|----------|
| `transcribe.py <影片>` | 單檔逐字稿（ElevenLabs Scribe） | `--num-speakers 2` |
| `transcribe_batch.py <資料夾>` | 多檔 4 worker 並行逐字稿 | 無 |
| `pack_transcripts.py` | 所有 JSON → `takes_packed.md` | `--edit-dir <dir>` |
| `timeline_view.py <影片> <開始秒> <結束秒>` | 影格+音波圖 PNG（鑽取用） | 只在需要時使用，非掃描工具 |
| `render.py <edl.json> -o <輸出>` | 主渲染（抽段/串接/疊層/字幕） | `--preview`、`--build-subtitles` |
| `grade.py <輸入> -o <輸出>` | 色彩分級 | `--preset warm_cinematic`、`--list-presets` |

所有腳本都在 `i:\Mark\my-kb\skills\video-use\helpers\` 下。

---

## 六、色彩分級（選用）

| Preset | 風格 | 適合場景 |
|--------|------|----------|
| `warm_cinematic` | 暖調復古，teal/orange 分離色，輕微降飽和 | 口播、技術教學、講座 |
| `neutral_punch` | 最小校正：提對比 + S 曲線，不偏色 | 原始畫質已不錯時 |
| `none` | 不處理，直接輸出 | 預設值，使用者未要求時 |

自訂色調：

```powershell
python helpers/grade.py input.mp4 -o graded.mp4 --filter "eq=brightness=0.1:saturation=1.2"
```

注意：色彩分級在「抽段」時就做好，不是在最後渲染時做，避免二次重編碼。預設按 CDL 模型：`out = (in * slope + offset) ** power`，再套整體飽和度。

---

## 七、字幕（選用）

預設字幕風格（`bold-overlay`）：2 個字一段、全大寫、白字黑邊、距底部 35px。適合 IG Reels、TikTok、社群短影音。

```
FontName=Helvetica,FontSize=18,Bold=1,
PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,
BorderStyle=1,Outline=2,Shadow=0,
Alignment=2,MarginV=35
```

改成「自然句子式字幕」（適合 YouTube 教學）→ 告訴 AI「字幕改成 4-7 個字一組、正常大小寫」。

**字幕規則（不可違反）**：字幕永遠最後才上，在所有動畫疊層之後。

---

## 八、動畫疊層（選用）

| 引擎 | 適合場景 | 執行方式 |
|------|----------|----------|
| **PIL + PNG 序列** | 文字卡、計數器、簡單條形圖 | 純 Python，最快迭代 |
| **HyperFrames** | HTML/CSS/GSAP 動態排版、UI 展示、資料驅動動畫 | `npx --yes hyperframes` |
| **Remotion** | React 元件動畫、已有 React 品牌系統 | `npx create-video@latest` |
| **Manim** | 數學圖表、狀態機、方程式演示 | 見 `skills/manim-video/SKILL.md` |

使用規則：
- 多個動畫同時並行產生（不是依序），總時間 ≈ 最慢那個的時間
- 動畫輸出路徑：`edit/animations/slot_1/render.mp4`
- 動畫疊層的時間偏移用 `setpts=PTS-STARTPTS+T/TB`（Hard Rule 4）
- easing 一律用 cubic，不用 linear（`ease_out_cubic` 單次出現，`ease_in_out_cubic` 連續繪製）

**動畫時長規則**：
- 同步旁白說明卡：最少 3 秒，一般 5-7 秒，複雜圖表 8-14 秒
- 節奏卡點型（音樂、快剪）：0.5-2 秒
- 旁白播完後 hold ≥ 1 秒再切
- 不同時出現兩個新元素（眼睛追不上）

---

## 九、輸出格式規格

| 平台 | 解析度 | 幀率 |
|------|--------|------|
| YouTube / 橫向 | 1920×1080 | 24fps（電影感）或 30fps（螢幕錄製） |
| IG / TikTok 直向 | 1080×1920 | 30fps |
| IG 方形 | 1080×1080 | 30fps |
| 4K | 3840×2160 | 24fps |

預設會輸出 1080p，有需要調整直接告訴 AI。

---

## 十、EDL 格式說明

`edl.json` 是 AI 的剪接決策清單：

```json
{
  "version": 1,
  "sources": {
    "take_01": "i:/Videos/folder/take_01.mp4",
    "take_02": "i:/Videos/folder/take_02.mp4"
  },
  "ranges": [
    {
      "source": "take_01",
      "start": 2.42,
      "end": 6.85,
      "beat": "HOOK",
      "quote": "這樣做效率可以提升九成",
      "reason": "最乾淨的一次，take_02 同段有口誤"
    }
  ],
  "grade": "warm_cinematic",
  "overlays": [
    {"file": "edit/animations/slot_1/render.mp4", "start_in_output": 0.0, "duration": 5.0}
  ],
  "subtitles": "edit/master.srt",
  "total_duration_s": 87.4
}
```

你可以手動修改這個檔案，然後重新執行 `render.py`。

---

## 十一、session 記憶（project.md）

每次剪輯結束，AI 會在 `edit/project.md` 追加：

```markdown
## Session 1 — 2026-09-23

**策略**：保留 take_02 的開場 + take_01 的核心講解，砍掉所有 uh/um 和 14 秒的死空間。
**決策**：HOOK 用 take_02 因為節奏更緊湊；結尾 CTA 用 take_01 因為語氣更自然。
**待辦**：下次可以加入字幕動畫版本。
```

下次打開同一個資料夾，AI 會先讀 `project.md`，一句話告訴你上次做到哪，問要不要繼續。

---

## 十二、絕對禁止的操作（Hard Rules）

這些是技術正確性規則，不是品味問題，違反會導致靜默失敗：

| # | 規則 | 違反後果 |
|---|------|----------|
| 1 | 字幕最後才上，在所有疊層之後 | 字幕被動畫蓋住，無聲失敗 |
| 2 | 逐段抽取 → lossless concat，不做單次 filtergraph | 每段被二次重編碼，畫質劣化 |
| 3 | 每個切接點前後 30ms audio fade | 切接點有爆音 pop |
| 4 | 動畫用 `setpts=PTS-STARTPTS+T/TB` 偏移 | 動畫從錯誤的幀開始播 |
| 5 | SRT 時間軸用輸出時間軸 offset，不是源碼時間 | 字幕在 concat 後對不齊 |
| 6 | 不得切在單字中間 | 字被切斷，聽起來奇怪 |
| 7 | 每個切接點 pad 30-200ms | Scribe 時間戳漂移，沒 pad 會切到字中間 |
| 8 | 只用 word-level verbatim ASR | SRT/phrase mode 沒有次秒級間隔資訊 |
| 9 | 逐字稿快取，不重複打 API | 浪費 ElevenLabs 費用 |
| 10 | 策略確認前不執行任何剪接 | — |
| 11 | 所有輸出寫入 `<videos_dir>/edit/`，不寫進 video-use repo | 污染 Skill 目錄 |

---

## 十三、剪接技法（Cut Craft）

- **音訊優先**：切點候選來自字邊界與靜音間隔。
- **保留情緒峰值**：笑聲、點睛句、強調拍，延伸保留反應鏡頭——笑聲本身就是節拍。
- **說話者交接**：兩人說話間留 400-600ms 的空氣，節奏緊湊時縮短，電影感時拉長。
- **靜音間隔是切點候選**：≥ 400ms 最乾淨；150-400ms 需視覺確認；< 150ms 不安全（可能在詞中間）。
- **切點 padding 範例**：保留字前 50ms，最後字後 80ms。節奏快則收緊，紀錄片風格則放寬，維持在 30-200ms 的工作窗口內。
- **音訊與畫面不能獨立推理**：每一刀必須兩軌都成立。

---

## 十四、常見陷阱（別踩）

- 用 Whisper 本地跑逐字稿 → 速度慢、會正規化 uh/um（失去剪接訊號）
- 動畫用 linear easing → 看起來機械感
- 字幕在 overlay 之前燒入底圖 → 被蓋住（Hard Rule 1）
- 多個動畫依序產生（不並行）→ 浪費時間
- 每次開 session 都重新打逐字稿 → 浪費 API 費用
- 還沒確認策略就開始剪 → 永遠不要這樣做
- 預設影片類型 → 先看素材、再問，最後才剪

---

## 十五、快速觸發方式（跟 Antigravity 說）

```
「用 video-use 剪 i:\Videos\2026-09-23-tutorial\」
「幫我剪掉這支影片的 uh 跟 um，資料夾在 i:\Videos\talk\」
「AI 剪接，多 take 素材，資料夾：...」
「自動逐字稿剪片」
「幫我剪掉 uh um」
```

Antigravity 會自動讀取 `video-use-editor` Skill，走完上面八個步驟。
