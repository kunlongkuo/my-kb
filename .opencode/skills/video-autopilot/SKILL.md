---
name: video-autopilot
description: 在策略已確定後，執行短影音製作流程，包含 `CapCut`、`JSON` 直接編輯與 `ffmpeg`。適用於使用者要落地、輸出、QA、紀錄或發布自動化，並建議搭配 `video-production-workflow` 先完成規劃。
---

# 短影音自動執行

這個技能只負責執行，不負責決定故事怎麼講。
如果需求仍然不夠明確，請先停下來，只問最必要的補充資訊，不要直接開始剪。

## 如何使用

1. 先讓 `video-production-workflow` 幫你判斷影片類型與 preset。
2. 再決定要走 `CapCut`、`JSON` 直接編輯，還是 `ffmpeg` 路徑。
3. 如果任務還沒講清楚，先補最少必要資訊，不要急著動剪。
4. 完成輸出後，記得做 QA 和結果紀錄。

## 這個技能負責的事

- 執行 `CapCut` GUI 工作流程。
- 視情況進行 `JSON` 直接編輯。
- 使用 `ffmpeg` 做裁切、合成、混音與備援輸出。
- 處理預覽、QA、輸出、紀錄與模式迭代。

## 這個技能不負責的事

- 不負責決定內容類型。
- 不取代 `video-production-workflow`。
- 不會在需求不清楚時偷偷切換路徑。

## 工作橋接

1. 先用 `video-production-workflow` 分類需求並選 preset。
2. 策略確定後，再交給 `video-autopilot` 執行。
3. 如果是發布型任務，輸出後要補紀錄。

詳見 [video-autopilot-workflow.md](references/video-autopilot-workflow.md) 的模式與路徑摘要。

## 核心規則

- 需要 GUI 視覺樣式時，字幕、貼圖、動態文字盡量留在 `CapCut`。
- `ffmpeg` 用於裁切、串接、縮放、混音與字幕燒錄備援。
- 遇到付費牆、上傳步驟或每日限制時，必須明確取得使用者同意。
- 如果動作跨過安全、預算或工具邊界，要停下並回報。

## 作業模式

- 模式 A：從主題或頻道目標規劃發布包。
- 模式 B：發布後記錄結果。
- 模式 C：依歷史結果優化模式。

## 路徑對照

- 路徑 A：只輸出。
- 路徑 B：字幕或模板加輸出。
- 路徑 C：更深度的樣式處理加輸出。
- 路徑 D：`JSON` 直接編輯後再以 GUI 輸出。
- 路徑 E：純 `ffmpeg`。

## 建議起手式

1. 先用 `video-production-workflow` 分類任務。
2. 選擇對應的模式與路徑。
3. 產出剪輯結果或輸出檔。
4. 驗證輸出。
5. 如果是發布型任務，再補上紀錄。
