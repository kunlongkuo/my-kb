# 統一濾鏡庫與畫面美學規範（Unified Filter Registry）

> 依據 `FreeTWAI/video-autopilot-kit`（v0.23.0 / 架構 7.0）之統一濾鏡規範整理。

---

## 統一濾鏡契約（Filter Contract）

長片、Shorts 與 Reels 共享統一的濾鏡庫註冊表（Registry），禁止將調色 LUT、轉場效果與全螢幕模板混為一談：

1. **調色唯一性與順序（Color Science First）**：
   - 全片調色（LUT / Purity grade）在管線中**只能套用一次**。
   - **調色必須先於字幕、圖卡、動態文字與貼圖**，嚴禁將字幕一起被濾鏡染色。
2. **轉場語意動機（Transition Motivation）**：
   - 轉場效果（如 torn paper、zoom blur 等）必須具備**剪輯動機**（如：章節切換、話題翻篇、時空轉換）。
   - 沒有敘事動機的切鏡，一律退回乾淨跳切（Clean Cut）。
3. **主體濾鏡與遮罩（Subject & Masking）**：
   - 人物主體強調、光影遮罩必須基於驗證後的 Track 數據或 Mask，避免邊緣殘破或抖動。
4. **安全區與視覺一致性**：
   - 保持 9:16（1080x1920）與 16:9（1920x1080）各自的頂部標題安全區與底部互動按鈕安全區。
