---
name: video-use-editor
description: 以對話驅動的 AI 影片剪輯技能，使用 browser-use/video-use 框架。支援自動逐字稿、精準剪接（cut filler words、死空間、口吃）、色彩分級、動態字幕燒錄、動畫疊層。適合 talking head、教學、訪談、旅遊、任何需要「說話精剪」的影片。說「用 video-use 剪」「AI 剪接」「自動逐字稿剪片」「幫我剪掉 uh um」時觸發。
---

# 🎬 video-use-editor

本技能是 [browser-use/video-use](https://github.com/browser-use/video-use) 的 Antigravity 整合入口。

> **這個 Skill 的定位**：處理「以語音為主、需要精準剪輯口播/講話素材」的影片。  
> 它和 `video-autopilot`（CapCut/ffmpeg GUI 路徑）不衝突，兩者互補。

---

## 📂 Repo 位置

```
i:\Mark\my-kb\skills\video-use\
├── SKILL.md        <- 原始上游 Skill（含詳細 Hard Rules）
├── helpers/        <- 核心腳本（transcribe.py, render.py, grade.py...）
├── install.md
└── .env            <- ELEVENLABS_API_KEY 存放於此
```

**啟動前必查**：

```powershell
# 1. 確認 ffmpeg 存在
ffmpeg -version

# 2. 確認 ElevenLabs API Key 已設定
Get-Content i:\Mark\my-kb\skills\video-use\.env

# 3. 確認 Python deps 已安裝
python -c "import librosa, PIL, numpy; print('OK')"
```

---

## 快速進場流程

### 第一步：確認素材位置

請使用者告訴你影片資料夾，例如：

```
i:\Videos\2026-09-23-lecture\
```

### 第二步：自動逐字稿（Transcribe）

```powershell
cd i:\Mark\my-kb\skills\video-use
python helpers/transcribe_batch.py "i:\Videos\2026-09-23-lecture"
python helpers/pack_transcripts.py --edit-dir "i:\Videos\2026-09-23-lecture\edit"
```

### 第三步：讀取 takes_packed.md，對話確認策略

- 讀取 `edit/takes_packed.md`，用白話告訴使用者：素材有哪些 take？哪些可以剪？主要問題是什麼（filler words？死空間？重複跑）？
- 詢問：目標長度？平台（IG / YouTube / TikTok）？風格偏向？必保留的段落？

### 第四步：提出策略（4-8 句）並等待確認

策略包含：
- 剪接方向（保留什麼、砍掉什麼）
- 字幕風格（幾個字一段、大寫/正常？）
- 色彩分級（warm cinematic / neutral / 自訂）
- 動畫疊層（是否需要？）
- 估算輸出時長

**策略未確認前，不得執行任何剪接。**

### 第五步：執行

```powershell
# render.py 根據 edl.json 做：片段抽取 -> concat -> overlays -> 字幕（最後上）
python helpers/render.py "i:\Videos\folder\edit\edl.json" -o "i:\Videos\folder\edit\final.mp4"

# 預覽版（720p 快速）
python helpers/render.py ... --preview
```

### 第六步：自評（展示給使用者前必做）

每個剪接點 ±1.5s 做 `timeline_view` 視覺檢查，確認：
- 無視覺跳幀/閃爍
- 無音訊 pop（30ms fade 有無生效）
- 字幕未被疊層蓋住
- 動畫沒跑錯幀

---

## 常用 Helpers 速查

| Helper | 功能 | 範例 |
|--------|------|------|
| `transcribe.py <video>` | 單檔逐字稿（ElevenLabs Scribe） | `python helpers/transcribe.py take1.mp4` |
| `transcribe_batch.py <dir>` | 4 工作者並行逐字稿 | `python helpers/transcribe_batch.py i:\Videos\folder` |
| `pack_transcripts.py` | JSON -> `takes_packed.md` | `python helpers/pack_transcripts.py --edit-dir edit/` |
| `timeline_view.py <video> <start> <end>` | 視覺+波形 PNG 鑽取 | `python helpers/timeline_view.py v.mp4 10 13` |
| `render.py <edl.json> -o <out>` | 主渲染（含字幕、疊層） | 見上方 |
| `grade.py <in> -o <out>` | 色彩分級 | `python helpers/grade.py clip.mp4 -o graded.mp4 --preset warm_cinematic` |

---

## Hard Rules（來自上游，不可違反）

1. **字幕最後上**，在所有疊層之後，否則字幕會被蓋住（靜默失敗）。
2. **逐段抽取 -> lossless concat**，不做單次 filtergraph，否則每段都被重新編碼。
3. **每個剪接點前後 30ms audio fade**（`afade=t=in:st=0:d=0.03`）。
4. **動畫疊層使用 `setpts=PTS-STARTPTS+T/TB`** 確保幀從正確時間點開始。
5. **SRT offset = output timeline 時間**，不是源碼時間。
6. **不得切在單字中間**，必須對齊 Scribe 字邊界。
7. **每個剪接點前後 pad 30-200ms**（Scribe 時間戳漂移吸收）。
8. **僅用 word-level verbatim ASR**（不用 SRT/phrase mode）。
9. **每個源碼逐字稿快取**，不重複呼叫 API。
10. **策略確認前不動剪刀**。
11. **所有輸出寫入 `<videos_dir>/edit/`**，不寫入 video-use repo 目錄。

---

## 與其他 Skill 的關係

```
video-production-workflow      <- 影片類型分類、策略規劃（所有路徑都從這裡開始）
     |
     +-- video-autopilot        <- 路徑 A-E：CapCut / JSON / ffmpeg 人工剪輯
     |
     +-- video-use-editor       <- 路徑 F：AI 對話式精剪（逐字稿驅動、講話素材）
```

---

## 這個 Skill 不適合的情況

- 素材沒有講話聲音（純 B-roll、音樂剪輯）-> 改用 `video-autopilot`
- 需要精細 CapCut 動態字幕效果或貼圖 -> 改用 `video-autopilot`
- 素材格式問題（損壞、非標準 codec）-> 先用 `ffmpeg` 轉換再回來

---

## 初次設定備忘

```powershell
# Clone（已完成）
# i:\Mark\my-kb\skills\video-use\

# 安裝 deps（已完成）
# cd i:\Mark\my-kb\skills\video-use
# python -m pip install -e .

# 設定 ElevenLabs API Key
# 在 i:\Mark\my-kb\skills\video-use\.env 中加入：
# ELEVENLABS_API_KEY=your_key_here
```

取得 API Key：https://elevenlabs.io/app/settings/api-keys
