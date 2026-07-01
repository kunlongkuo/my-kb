> 來自 video-autopilot-kit 開源知識庫 · MIT 授權
> 原始檔：https://github.com/Hao0321/video-autopilot-kit/blob/main/knowledge/capcut-automation-sop.md

CapCut Desktop GUI 操作 SOP — Computer Use agent 在 CapCut 套字體 / 模板 / 特效 / Export 的封裝知識庫。

**觸發詞**：「用 CapCut 套模板」「CapCut 加字幕」「agent 剪片」「跑 CapCut」「Export v[N]」「換 CapCut 字體」「字醜」「沒綜藝感」「Pro paywall」。

---

## 用戶說什麼 → 做什麼

| 用戶說 | 動作 |
|---|---|
| 「跑 CapCut」「agent 剪片」 | Load `capcut-agent-brief-template.md` 拉模板 |
| 「Export v[N]」「匯出」 | 走 5 分鐘最短 Export path（Path A）|
| 「字醜」「換字體」「綜藝風不對」 | 換模板策略（見下方 M43 RULE）|
| 「Pro paywall」「卡關」 | 見下方避雷地圖 |
| 「不要 agent / 直接改」 | Load `capcut-json-direct-edit.md` skip GUI 走 JSON |

---

## Path A-E 快速選擇

### Path A: Export only（最快，最便宜）
**ETA**: 5-8 分鐘 / 約 40 tool calls / 低 token

用於：JSON 已 patched，只需開 CapCut 點 Export。

### Path B: 套單一 text template + Export
**ETA**: 25-40 分鐘 / ~140 tool calls / 中 token

用於：全部 caption 套同一花字（如 Dynamic white crayon）。

### Path C: 多模板 + 套貼圖 + Export
**ETA**: 60-90 分鐘 / ~300 tool calls / 高 token

用於：marker / main / sub 各套不同模板 + 重點段加貼圖。
⚠️ **可能撞 daily limit（每日凌晨重置）**

### Path D: JSON direct edit ⭐（最 efficient，0 GUI）
**ETA**: <1 分鐘 / 0 agent tool calls / 極低 token

用於：(1) 換 caption 文字內容（保留現有 effects）/ (2) 換 font_path 或 font_size / (3) 換 transform.y position。
**不能做**：套新模板（template_id 需要從雲端下載）/ 加貼圖。

### Path E: 純 ffmpeg（完全跳過 CapCut）
**ETA**: ~90 sec / 0 GUI / 極低 token

用於：用戶 OK 接受 ffmpeg drawtext 字幕（無動畫 / 無 CapCut 花字）。

---

## 黃金規則 — 寫進 agent brief 必含

1. **「絕對不問用戶任何問題」** — autopilot preference 鐵則
2. **「絕不點菱形💎圖示」** — Pro paywall，會在 Export 時 block
3. **「絕不動 timeline 上 transition 4px icon」** — M33 點不中，只能 Ctrl+Z
4. **「絕不開「智能 / AI / 自動 X」按鈕」** — Pro 鎖
5. **「Screenshot 經濟用」** — 起始 1 張 + 每完成 5 步 1 張 + Export 1 張，不要 step by step screenshot
6. **「Bash > Screenshot」** — verify 用 ffprobe / ls 直接驗證檔案，不用 screenshot
7. **「Pro paywall 早期偵測」** — 套完 5 個 effect 後試一次 Export，跳警告 → Ctrl+Z 退最後一個 → 換 free template
8. **「daily limit 撞 2 次就停」** — 不要 force retry，寫 partial report

---

## ✍️ M43 RULE — 字體選擇規則

### ❌ 禁用 / 退避字體（沒個性 / 醜）
- ~~`kaiu.ttf`~~ 標楷體（教科書感）
- ~~`mingliu.ttc`~~ 細明體 default（太細）
- ~~`NotoSansTC-Bold.otf`~~ 太 generic（除非搭配 effect / 模板）
- ~~`SmileySans-Oblique.ttf`~~ 中文 coverage 不全 → fallback 笑臉

### ✅ 好看字體 whitelist

| 用途 | 字體 | 路徑 |
|---|---|---|
| **Vlog narrative / sub** | **Noto Serif CJK Bold** | `<專案>/assets/fonts/NotoSerifCJK-Bold.ttc` |
| **Marker title** | 套 CapCut 文字模板（FOOD VLOG / Coffee Time）| 走 agent path |
| **Decorative dynamic text** | 套 CapCut 文字模板 速度寫 + 動畫 | 走 agent path |
| **Emergency fallback** | NotoSansTC-Black | 系統字型目錄 / `NotoSansTC-Black.otf` |

### 推薦下載字體（社群驗證 vlog 用）
- **LXGW WenKai TC**（霞鶩文楷）：`https://github.com/lxgw/LxgwWenKai-TC/releases`
- **獅尾匯潮黑**（modern marketing）
- **Justfont 金萱**（商業需 license）

### JSON 換字體公式
```python
NEW_FONT = "<專案>/assets/fonts/NotoSerifCJK-Bold.ttc"
for t in d.get("materials", {}).get("texts", []):
    t["font_path"] = NEW_FONT
    co = json.loads(t["content"])
    for s in co.get("styles", []):
        s["font"] = {"path": NEW_FONT, "id": "", "cn_name": "", "tw_name": ""}
    t["content"] = json.dumps(co, ensure_ascii=False, separators=(",", ":"))
```

⚠️ 同步 3 處 JSON（M18: root × 2 + Timelines）

---

## 🚫 M42 RULE — 動態文字/貼圖 MUST 用 CapCut native

| 任務 | ✅ 走 CapCut | ❌ 不要 ffmpeg |
|---|---|---|
| 加 caption / 字幕 | CapCut 文字 panel | ~~drawtext overlay~~ |
| 加動態 sticker (✈🍦🏨) | CapCut 貼圖 panel | ~~drawtext emoji overlay~~ |
| 動態 text overlay（彈跳/縮放）| CapCut 文字模板 動畫 | ~~drawtext alpha animation~~ |
| 標題卡 / outro card | CapCut 文字模板 | ~~ffmpeg color+drawtext~~ |

**ffmpeg 仍可用於**：Audio mix / Video concat trim scale / Color grade / Subtitle burning（.srt sidecar 作 fallback）

---

## 🇹🇼 M66 RULE — 中文字幕必繁體中文

CapCut AI 字幕 default 出**簡體**，用繁體中文 audience 必罵。

**任何含 AI 字幕的 brief 必含**：
```
Step X: 選語言「中文（繁體）」/「Traditional Chinese」，永遠不要選 default「中文」
Step X+1: screenshot 字幕 preview，檢查指標字
          簡體: 设/计/开/发/纲/并/创/为/这/还/动/区/划/觉
          繁體: 設/計/開/發/綱/並/創/為/這/還/動/區/劃/覺
          若見簡體 → 寫 partial report 停下，NOT Export
Step X+2 fallback: export .srt → OpenCC s2tw.json 轉 → import 回 CapCut
```

---

## 跨 brief 通用開頭段落（每次 spawn 必含）

```
專案：<專案名稱>
路徑：<CapCut User Data>/Projects/com.lveditor.draft/<專案名稱>/
素材 raw：<專案>/videos/<current>/raw/<素材資料夾>/
Export 路徑：<專案>/videos/<current>/export/
BGM：<專案>/assets/bgm/<bgm 檔名>.mp3
規格：1920×1080 / 30fps / H.264 / AAC

讀知識檔：依任務 load 對應 capcut-*.md 文件
```

---

## 用戶診斷快速查表

| 用戶吐槽 | 真實原因 | 解法 |
|---|---|---|
| 「字醜」 | 套到兒童風 splash 模板 | 換標記為 "vlog-friendly" 的模板 |
| 「沒綜藝感」 | 全部套同一模板 | markers / 重點 / 一般 / 補充分 4 套 |
| 「字幕對不上畫面」 | M9/M34 — 沒做 frame audit | 先用 frame audit 工具看 frame |
| 「Pro paywall」 | M33 — 套到菱形 icon | Ctrl+Z 退 + 換下載 icon |
| 「撞 daily 限制」 | M40 — CapCut Free 套特效次數上限 | 每日凌晨重置，或改 Path D JSON |
| 「字體不夠多變化」 | M39 — ffmpeg drawtext 無 fallback chain | 改 CapCut Path B/C |

---

## 🆕 交付前 QA helpers (M91–M96)

```python
from capcut_helpers import final_delivery_qa, still_blurfill, detect_flash, detect_long_pauses, cut_audio_segments, cut_video_segments, remap_time, contact_sheet
```

| helper | 做什麼 |
|---|---|
| `final_delivery_qa(video, voice, contact_out)` | 交付前一鍵 QA：頻閃 + 死空檔 + 接觸表 |
| `detect_flash` | blackdetect 抓頻閃素材/亮度落差 |
| `detect_long_pauses` / `cut_audio_segments` / `cut_video_segments` / `remap_time` | 句間死空檔三軌同步剪（音/影/字幕）|
| `still_blurfill` | 非滿版圖 → 模糊背景填滿（禁死黑邊、禁 zoompan 抖）|
| `contact_sheet` | 整片接觸表逐格看 chrome/隱私 |
