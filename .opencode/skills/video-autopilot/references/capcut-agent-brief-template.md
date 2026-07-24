> 來自 video-autopilot-kit 開源知識庫 · MIT 授權
> 原始檔：https://github.com/Hao0321/video-autopilot-kit/blob/main/knowledge/capcut-agent-brief-template.md

Spawn Computer Use agent 跑 CapCut 操作時，brief 必含的 6 個區塊。
從多支 vlog 專案 20+ agent spawn 經驗提煉（M32 / M33 / M40 教訓）。

---

## 🎯 何時 spawn agent

| 條件 | 動作 |
|---|---|
| 連 ≥2 輪 programmatic patch 用戶仍罵 | spawn agent（**不要 spawn 第 3 次**）|
| 用戶提及「全自動」「agent」「Computer Use」 | spawn agent |
| JSON edit 無法達成（要 GUI 動 timeline / 套新模板）| spawn agent |
| Export only（JSON 已 patched）| spawn agent Path A |

**Hard cap：spawn 上限 = 2 agents / task**。連 2 個失敗 → 停止 spawn，改 Path D (JSON edit) 或 user manual。

---

## 📋 Brief 必含 6 區塊（缺一就 spawn 失敗）

### 1. 起始狀態 + 已做了什麼

```
專案：<專案資料夾名稱>
路徑：<CapCut Projects 目錄>\<專案資料夾名稱>\
當前狀態：v<N> 已套 25 個 crayon + 3 個 gold marker，BGM 已 ffmpeg force-mix
要 agent 做：把 28 個 caption 全部改 bubble style（effect_id <effect-id>）+ Export
```

### 2. 用戶具體吐槽歷史（每條 actionable，不是抽象抱怨）

```
- v18: 要求動態文字走 CapCut native，不要用 ffmpeg drawtext
- v20: 「字醜」→ 換用戶 favorited 花字（effect_id <effect-id>）
- v22: 用戶手動加 canvas_blur 11 個 portrait → 不要 JSON 覆蓋回 uniform
```

### 3. raw assets + 參考檔案路徑

```
raw：<raw 素材目錄>\（49 MOV + 60 HEIC）
Export 路徑：<export 輸出目錄>\
BGM：<bgm 目錄>\<bgm-檔名>.mp3
cut-plan：<專案目錄>/cut-plan-<專案>-v<N>.md
user canonical state backup：<專案目錄>/user_final_state/
```

### 4. 操作步驟 8-10 步（含 Hook + 字幕 + 轉場 + KenBurns + 濾鏡 + 音訊 verify + Export）

```
Step 1: 開 CapCut Desktop → load <專案> project
Step 2: Screenshot 起始狀態 → verify project loaded OK
Step 3: 文字 tab → 花字 sub-tab → ⭐ filter → 找 effect_id <effect-id>
Step 4: 套到 caption seg #0（第一段 caption）→ Ctrl+S → screenshot verify
Step 5: 若 Step 4 渲染 OK → JSON 複製 effect 到剩 27 個 caption（不要 GUI 操作 28 次）
Step 6: ⚠️ 先試一次 Export 確認 Pro paywall（套 5+ effects 後）→ 若跳警告，Ctrl+Z 退最後一個
Step 7: 套完 → Ctrl+S → 螢幕截圖 timeline 全貌
Step 8: 點 Export 按鈕 → 選 1080p 30fps H.264 / AAC default
Step 9: 等 Export 完成（不要動鼠標，CapCut 跑 background ~3-5 min）
Step 10: 螢幕截圖 Export 完成畫面 → 確認 mp4 落在 <export 輸出目錄>
```

### 5. Export 路徑 + 報告檔

```
Export 落點：<export 輸出目錄>\<專案>_v<N>.mp4
報告檔：<專案目錄>/edit-report-agent-<N>.md
報告必含：
- 起始 / 結束 timestamp
- Tool calls 數
- 卡關處（哪步停下用 Ctrl+Z 退）
- Pro paywall blocker（若有）
- daily limit 撞牆（若有）
- Final Export 檔案大小 + duration verify (ffprobe)
```

### 6. 鐵則（絕不違反）

```
1.  絕對不問用戶任何問題 — autopilot preference 鐵則
2.  絕不點菱形💎圖示 — Pro paywall，會在 Export 時 block
3.  絕不動 timeline 上 transition 4px icon — M33 點不中只能 Ctrl+Z
4.  絕不開「智能 / AI / 自動 X」按鈕 — Pro 鎖
5.  Screenshot 經濟用 — 起始 1 張 + 每 5 步 1 張 + Export 1 張（不要 step by step）
6.  Bash > Screenshot — verify 用 ffprobe / ls 不用 screenshot
7.  Pro paywall 早期偵測 — 套 5 effects 後試一次 Export，跳警告 → Ctrl+Z 退 → 換 free template
8.  daily limit 撞 2 次就停 — 不要 force retry，寫 partial report
9.  動態文字 / sticker MUST use CapCut native，NEVER ffmpeg drawtext (M42)
10. User 已 favorited 的花字（star icon）優先使用
11. Session start 第一個 PowerShell command 必 minimize 所有 Chrome window（M70 — Chrome focus-steal 吃 50% tool calls）
12. CapCut foreground 後必 MoveWindow resize 到 1400×900（M71 — 1400×900 = universal size）
13. Post-Export rename mp4 用 Copy-Item → Kill CapCut → Remove duplicate（M72 — file lock 不能 Move/Rename）
14. 中文字幕選語言時必選「中文（繁體）」/「Traditional Chinese」（M66 — CapCut AI default 出簡體）
```

---

## 🚨 Brief Anti-patterns（spawn 後立刻失敗的寫法）

| Anti-pattern | 為什麼壞 | 修正 |
|---|---|---|
| 「剪一支 vlog」 | 太抽象 agent 不知做什麼 | 列具體 step 8-10 步 |
| 「修一下字幕」 | 沒指定哪些 caption / 套什麼 effect | 「caption seg #0-#27 套 effect_id X」|
| 「跑完 Export 給我」 | 沒指定 Export 路徑 / format | 列 5 區塊「Export 落點」 |
| 「有問題就停下問用戶」 | 違反 autopilot rule | 「絕不問用戶任何問題」必含鐵則 |
| 「順便加個轉場」 | 模糊 → agent 點到 Pro icon 卡關 | 列具體 transition name + 確認 free |
| 「按你判斷做」 | agent context 無 user history | 列吐槽歷史 + canonical state path |

---

## 💼 Spawn 參數 default

```python
Agent(
    description="<短描述 3-5 字>",
    subagent_type="general-purpose",  # 預設用 general（有 computer-use tools 子集）
    run_in_background=True,  # 30-60 min 操作，主 Claude 同時處理其他事
    prompt="<brief 6 區塊完整內容>",
)
```

---

## 🪟 M48: CapCut window-hidden 後 SetForegroundWindow workaround

**症狀**：`open_application("CapCut")` 回 success 但 screenshot 仍是上一個 frontmost app

**Fix（PowerShell SetForegroundWindow Win32 API）**：
```powershell
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class Win {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
}
'@
$hwnd = [Win]::FindWindow($null, "剪映")
[Win]::SetForegroundWindow($hwnd)
```
