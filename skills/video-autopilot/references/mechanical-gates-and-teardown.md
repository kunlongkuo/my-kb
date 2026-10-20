# 機械閘門與競品拆解規範（Fail-Closed Gates & Teardown）

> 依據 `FreeTWAI/video-autopilot-kit`（v0.23.0）最新同構生產線標準制定。

---

## 核心精神：機械閘門（Fail-Closed Mechanical Gates）

不依賴人類或 Agent 記憶，由程式碼在出片前強制攔截：
- **Fail-Closed 原則**：不合規直接退出（Exit != 0），絕不靜默 fallback。
- **無數據不發布**：查無出處的數據、未經審查的行話、過載的文字直接擋出片。

---

## 三條同構生產線與專屬閘門

| 生產線 | 核心任務 | 機械閘門 | 檢核重點 |
| :--- | :--- | :--- | :--- |
| **教學長片**<br>`longform_maker` | 講清楚核心觀念，維持資訊密度與邏輯留存 | `script_gate` | - 觀眾語言過濾（行話/生僻詞 Fail）<br>- 節奏長度長條圖預檢（Warn）<br>- 每分鐘核心論點密度 |
| **直式 Shorts / Reels**<br>`shorts_autopilot` | 高留存、前 3 秒抓住眼球、畫面節奏明快 | `shorts_gate` | - **9 條結構與字幕硬性規則**（位置偏中央下、避開平台按鈕安全區）<br>- **平台感知片長帶**（YT Shorts 甜蜜帶 42-55s；IG Reels 則按 Meta 機制走，不生搬硬套）<br>- 換句速率與換句÷剪點節奏 |
| **線上訪談**<br>`interview_autopilot` | 提煉來賓金句與論點 | `interview_gate` | - **I-A ～ I-E 來源閘門**：沒客觀來源與授權的來賓數據「在錄影與剪輯前」就被擋下 |

---

## 競品量化拆解（Teardown Method）

透過客觀數據拆解標竿競品短片，取得實戰參數而非主觀感受：

1. **刀速與刀距分布（Pacing & Cut Interval）**：
   - 計算平均每刀時長（秒/刀）及標準差（節奏變化程度）。
2. **換句速率（Speech cadence）與 換句÷剪點比例**：
   - 「每句話換幾個鏡頭」決定了是視覺驅動還是口播驅動。
3. **音訊正規化（LUFS）**：
   - 確保整合輸出落在標準響度（例如短影音 -14 LUFS，True Peak -1.0 dB），防止聲音忽大忽小或爆音破音。
