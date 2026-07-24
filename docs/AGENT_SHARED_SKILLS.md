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

## 技能分工

### `video-production-workflow`

負責前期規劃與策略判斷，包括：

- 影片類型分類
- 平台與受眾判斷
- 拍攝與剪輯策略
- 字幕、節奏、封面與腳本規劃

### `video-autopilot`

負責實際執行與輸出，包括：

- 剪輯流程落地
- `CapCut` / `ffmpeg` / JSON 編輯
- 產出、QA 與紀錄
- 可重複使用的自動化流程

## 建議使用順序

1. 先讀 `video-production-workflow`
2. 再讀 `video-autopilot`
3. 若要交給其他 Agent，先看 `.agents/README.md`

## 維護原則

- 更新內容時，以 `skills/` 為來源。
- 同步時要一起更新 `.agents/skills/` 與 `.opencode/skills/`。
- 保持繁體中文，讓各 Agent 的理解一致。

## 補充

如果後續還要擴充新的短影音技能，建議沿用這個結構新增：

- `skills/<新技能>/`
- `.agents/skills/<新技能>/`
- `.opencode/skills/<新技能>/`

