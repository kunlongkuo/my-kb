# 共用 Agent 技能包

這個目錄是給多個 Agent 共用的技能鏡像區，目標是讓 `OpenCode`、`AntiGravity` 與其他支援讀取本機技能的 Agent，都能用同一套短影音製作知識。

## 目前結構

- `skills/`：原始來源，之後的內容更新請以這裡為準。
- `.opencode/skills/`：OpenCode 使用的鏡像。
- `.agents/skills/`：其他 Agent 共用的鏡像。

## 已同步的技能

1. `video-production-workflow`
2. `video-autopilot`

## 使用方式

- 先看 `video-production-workflow`：用來判斷影片類型、平台、長度、字幕風格與剪輯策略。
- 再看 `video-autopilot`：用來實際執行剪輯、自動化與輸出。
- 如果需要更快上手，先讀各技能底下的 `references/` 文件，再回到 `SKILL.md`。

## 維護原則

- 以 `skills/` 作為單一來源。
- 內容更新後，同步到 `.agents/skills/` 與 `.opencode/skills/`。
- 所有說明文件與提示詞維持繁體中文。
- 不要刪除原始技能檔，除非有明確需求。

## OpenCode 設定

`opencode.json` 已加入這兩個技能的允許設定，讓 OpenCode 可以直接載入與使用。

## 給其他 Agent 的一句話

這份共用包的核心原則是「先規劃，再執行」。`video-production-workflow` 負責定義策略，`video-autopilot` 負責落地執行。
