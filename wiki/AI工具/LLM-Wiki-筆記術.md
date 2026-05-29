---
title: LLM Wiki 個人知識庫筆記術
category: METHOD
tags: [AI, 知識管理, PKM, LLM]
sources: [raw/LLM_Wiki_Karpathy.md, cards/AI與卡片盒筆記法實測心得.md, cards/用Agent養Agent.md, raw/obsidian/用Agent養Agent：開關啟動與遠端修復.md, cards/Hermes-Desktop-GUI安裝與功能摘要.md, raw/obsidian/Hermes Desktop 讓 Windows 直接就能安裝使用 Hermes Agent！初學者也能自己搞定.md, cards/默片撈重點-ffmpeg-AI.md, raw/obsidian/我學會了一招：不靠聲音、不靠字幕，從一支默片裡撈出 10 個重點.md, cards/Manus-AI-Agent實戰教學.md, raw/obsidian/【Manus 實戰教學】從研究、簡報到個人網站，帶你掌握普通人也能上手的 AI Agent.md, cards/Edits-影片編輯軟體教學.md, raw/obsidian/Edits 下載方法＋新手使用大全.md, cards/Image-Extraction-抓圖神器教學.md, raw/obsidian/教學／Image Extraction「抓圖神器」免安裝 貼網址1鍵抓整頁圖片.md, cards/OpenCode-AI-Agent地端部署.md, raw/obsidian/OpenCode基本功 EP01：免費 AI Agent 啟手式.md, cards/AI簡報高階工作流-NotebookLM-PDNob.md, raw/obsidian/別再只用一句話叫 AI 生成簡報！學會這個隱藏技巧.md, cards/Codex-Ollama-本地模型串接.md, raw/obsidian/免費無限使用 Codex 桌面版！一個指令，就能透過 Ollama 輕鬆串接本地 AI 模型.md]
status: verified
updated: 2026-05-29
---

# LLM Wiki 個人知識庫筆記術

本頁面整理 OpenAI 共同創辦人 Andrej Karpathy 所分享的 「LLM Wiki」 知識管理方法論，以及如何利用 AI 代理工具（如 Antigravity）自動化建構個人知識庫。

> [!TIP]
> Karpathy 核心哲學：「File Over App」——資料主權高於應用程式，優先使用 Markdown 等通用格式儲存資料，確保知識能跨工具永久保存。

## LLM Wiki 核心特點

| 特點 | 說明 |
| :--- | :--- |
| **自動化編譯** | AI 自動閱讀原始資料，生成摘要、分類概念並建立雙向連結 (Backlinks)。 |
| **預先編譯知識** | 不同於 RAG 每次即時檢索，LLM Wiki 預先將知識結構化，加速複雜問題的回答。 |
| **多元輸出** | 可串接生成 Markdown、Marp 簡報或 Matplotlib 數據圖表。 |
| **資料主權** | 使用 .md、.json 等通用格式，不綁定特定筆記軟體（如 Obsidian 可直接讀取）。 |

## 實作步驟 (使用 Google Antigravity)

1.  **建立環境**：在電腦中建立專屬資料夾（如 `my-kb`）。
2.  **配置指令**：將 [Karpathy 的 LLM Wiki 指令](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 存入該資料夾。
3.  **引導 AI**：開啟 Antigravity，指向該資料夾，並要求其「閱讀指令文件並建立資料架構」。
4.  **執行 Ingest**：將原始文件放入 `raw/` 資料夾，下達指令「請幫我 Ingest [檔案名稱]」。

## 工具對比：LLM Wiki vs. NotebookLM

| 維度 | NotebookLM | LLM Wiki (Karpathy) |
| :--- | :--- | :--- |
| **知識累積** | 每次對話從頭搜尋，無持久結構 | 預先編譯、建立關聯，知識具累積性 |
| **存儲位置** | 雲端平台 (Google) | 本地電腦 (Markdown 檔案) |
| **適用場景** | 單次快速研究、生成 Podcast | 長期深度研究、個人知識體系建構 |
| **檔案主權** | 低 (綁定平台) | 高 (通用格式) |

## Karpathy 的提醒
*   **不代替思考**：工具是用來節省編輯功夫，而非取代閱讀與思考過程。
*   **高品質輸入**：隨意丟入連結會增加 AI 幻覺，應親自閱讀、遴選關鍵資訊後再進行主題化。

## 進階工作流：結合卡片盒筆記法 (Esor Huang 實測)

電腦玩物站長 Esor Huang 在實測中，為這個系統導入了**卡片盒筆記法 (Zettelkasten)** 的工作流。他強調 AI 的價值在於「執行預先設計好的流程」，而非單純的問答。

### 三層架構 (Raw -> Card -> Opinions)
1. **Raw (文獻庫)**：完整抓取原文與來源，保留證據。
2. **Card (暫時筆記)**：針對單篇文獻撰寫摘要、個人觀點與下一步行動。
3. **Opinions (永久筆記)**：核心的第二大腦。強調「更新既有母筆記」而不是「一直新增筆記」。

### 永久筆記的知識分類
他將永久筆記 (Opinions / Wiki) 歸類為三種層級，以提高後續提取的精準度：
- `PROJECT`：正在進行的專案或研究主題。
- `WORKFLOW`：未來可參考的操作步驟與最佳範例 (SOP)。
- `METHOD`：專案與工作流程通用的方法論、理論與證據。

### AI Agent 整理守則
- **回填機制 (Backfill)**：新增 Card 時，AI 必須主動檢查並建議是否要更新現有的 Opinions。
- **防止發散**：建立全新的永久筆記前，必須先取得使用者同意。
- **自動維護地圖**：每次更新後，自動同步維護全域索引 (INDEX) 與知識架構圖 (MAP)。

## 實踐案例：80秒卡通短影音自動化生成工作流 (SOP)
在卡片盒筆記法的 `WORKFLOW` 層級中，這套「從文章到 80 秒卡通短影音」的自動化流程是極具代表性的實踐案例。

### 1. 流水線 (Pipeline) 架構與工具串接
這套工作流透過 4 個專屬 AI 工具進行接力拼貼：
- **剪劇本 (Claude/ChatGPT)**：把長文重組拆解為 23 句字幕（每句限制 20 字以內），維持「Hook -> 緣起 -> 卡點 -> 領悟 -> 教訓 -> CTA」的 7 段式結構。
- **畫場景 (Pollinations.ai / Flux)**：設計 7 張暖色 Q 版插畫背景（Morandi 配色、Flat Illustration 風格），利用相同的 `seed` 與主角特徵描述鎖定角色一致性。
- **配人聲 (MiniMax Voice Cloning)**：利用 1-2 分鐘個人真實錄音克隆聲線，並將繁體字串繁轉簡後送 TTS 生成（以 `speech-02-hd` 模型、`1.1` 倍速、`calm` 情緒進行優化）。
- **拼貼渲染與配樂 (HyperFrames + ffmpeg + Replicate)**：使用開源的 HyperFrames 配合 GSAP 時間軸與 HTML 渲染出 MP4，並由 Python 腳本計算毫秒 `adelay`，透過 ffmpeg 精準混合多段配音與 Replicate Lyria 2 自動生成的商用安全 BGM。

### 2. 核心痛點解決 (避坑指南)
- **繁體咬字問題**：中國模型（MiniMax）對繁體字容易破音或偏陸腔，送 TTS 前必須轉為簡體，回放才自然。
- **首秒黑畫面**：將首張圖的淡入時間設為 `0` 秒以避免黑屏。
- **數字符號發音**：送 TTS 前將所有阿拉伯數字及特殊符號手動改寫為中文漢字（如 `2026` 轉 `二零二六`）。
- **音量淡出**：影片結尾使用 ffmpeg 的 `afade` 做最後兩秒淡出，避免音量硬切。

詳細的實作程式碼、參數設定與避坑細節，請參閱卡片 [[一篇文章到80秒說話卡通片完整製作流程]]。

## 實踐案例：用 Agent 養 Agent 的系統運維哲學 (METHOD)
在個人 AI 系統的日常運作中，「用對話流與 Agent 維護整個系統」是另一個核心的實踐案例，解決了 Agent 工具容易因升級、配置調整而「損壞啟動流程」的致命痛點。

### 1. 核心策略與架構
*   **用強 LLM 養地端 Agent**：傳統運維需要手動修改設定檔、手動更新套件，極易弄壞啟動鏈。策略是找一個夠強大的 LLM（如 ChatGPT 訂閱制 / Claude Code / Codex），由其專門負責地端 Agent（如 OpenClaw、Hermes Agent）的安裝、啟動、檢查與修復，所有設定盡量透過 LLM 進行。
*   **一鍵式終端指令**：在 Claude Code 或 Codex 終端中直接輸入提示詞（如 `幫我安裝 OpenClaw Github`），即可讓 LLM 自動抓取代碼庫、架設虛擬環境並完成設定檔配置。
*   **GUI 桌面伴侶化 (Hermes Desktop)**：隨著地端 Agent 生態的發展，出現了如 **Hermes Desktop**（v0.4.3）之類的圖形化桌面軟體。它為傳統 CLI-only 的 Hermes Agent 提供了引導式的一鍵安裝 GUI，自動處理解析 Python 3.11+、Git 與 uv 等依賴，並整合了串流聊天對話、22 組斜線指令、14 組工具集、16 種訊息平台閘道（如 Telegram, Discord）與 Cron 排程任務等。這極大地消除了初學者在終端機敲打 CLI 指令的門檻（詳細參閱卡片 [[Hermes-Desktop-GUI安裝與功能摘要]]）。但要注意的是，地端 GUI 運行仍受限於「本機電腦關機後即無效」的侷限，因此對於有 24/7 運行需求者，後端仍適合以 Mac 或 Linux 主機運行，而將 Desktop 當作遠端前端 UI 控制端。

### 2. 遠端通道修復與哲學思考
*   **Anthropic Channel 的雙向應用**：Anthropic 的 Channel 功能讓使用者可以直接從外部（如 Telegram）與 Claude 進行對話。這不僅極大地方便了日常控制，也成為修復地端系統的橋樑。當地端 Agent 掛掉時，使用者只需透過 Telegram 傳送修復指令，Claude 便能自動重啟並維護地端 OpenClaw 系統，擺脫了過去必須遠端桌面連回 Mac 電腦的繁瑣。
*   **多 Agent 的存廢思辨**：當外圍的單一 LLM 代理（如 Claude Code）已經強大到能夠通過遠端命令與自動化腳本接管、修復地端系統時，我們是否還需要複雜的「多代理架構」（如養龍蝦 OpenClaw、養馬 Hermes Agent）？這為個人知識庫與自動化架構的演進提供了深刻的思索方向。

### 3. 本地適配與無限量推論 (Codex-Ollama)
*   **Ollama v0.24.0 本地適配**：為解決雲端 API 額度限制與隱私安全痛點，Ollama 於 v0.24.0 中加入了對 Codex 桌面版的本地串接支援。
*   **單指令配對啟用**：只需執行單一終端指令 `ollama launch`，即可讓 Ollama 偵測並將本地開源模型（如 Llama 3 或 Mistral）與地端 Codex 桌面版進行無縫串接，充當其推理大腦。這提供了一個 100% 本地運行、完全免費且保證隱私的開發沙盒，極大便利了地端 Agent 系統的開發除錯。

詳細適配操作與分析，請參閱卡片 [[Codex-Ollama-本地模型串接]]，其他運維哲學請參閱 [[用Agent養Agent]]。

## 實踐案例：OpenCode AI Agent 地端部署與自訂工具架構 (METHOD)
在地端 AI 工具的應用中，除了使用封閉的商業軟體，基於開源框架如 **OpenCode** 在本地電腦部署自主運作的 AI Agent 是極具擴充性的 `METHOD` 實踐。

### 1. Harness Engineering 硬體對齊架構
該架構將 Agent 的各模組以電腦硬體進行精確映射，簡化了地端 AI 自動化的理解門檻：
*   **推理大腦 (CPU)**：底層大語言模型（如 `gpt-4o-mini` 或 `gemini-1.5-flash`）。
*   **快速記憶 (RAM)**：Context Window 與向量資料庫，儲存會話的即時上下文。
*   **系統調度器 (OS)**：Prompt-Engine 與 Task-Scheduler，控制任務的生命週期與 ReAct 思考鏈。
*   **外接周邊 (Peripherals)**：Tool-Registry，外接自訂功能如搜尋（Web Search）或本地安全運算代碼執行器（Python Executor）。

### 2. 八步部署 SOP 與 Custom Tool 擴充
1. 安裝 Python 3.11+ ➔ 2. 克隆 OpenCode 倉庫 ➔ 3. 建立並啟用 `.venv` 虛擬環境 ➔ 4. `pip` 安裝依賴 ➔ 5. 於 `.env` 設定 API 金鑰 ➔ 6. 撰寫 `agent_config.yaml` 配置檔 ➔ 7. 啟動並配合 `--debug` 檢視除錯 ➔ 8. 撰寫擴充工具類別（繼承 `ToolBase` 並加入型態標註）以完成自動化任務排程。

詳細部署指令與 ReAct 除錯方法，請參閱卡片 [[OpenCode-AI-Agent地端部署]]。

## 實踐案例：無聲短影音重點萃取流程 (WORKFLOW)
這套「不靠聲音與字幕從默片撈重點」的流程，是針對快閃字卡短影音或動作示範影片進行知識萃取的實用 SOP。

### 1. 核心流程與技術工具
*   **定時切片抽影格**：針對有規律字卡快閃的影片，利用 `ffmpeg` 按估算的時間中點進行高畫質截圖（例如將 21 秒影片分為 10 段，每 2.14 秒抓一張）：
    ```bash
    ffmpeg -ss 1.0 -i 影片.mp4 -frames:v 1 -q:v 2 keyframe_01.jpg
    ```
*   **場景變化偵測**：針對純動作或畫面變更頻繁的教學片，使用 `ffmpeg` 內建的場景偵測功能，自動提取畫面變化大於 30% 的瞬間，免去人工比對時間：
    ```bash
    ffmpeg -i 影片.mp4 -vf "select='gt(scene,0.3)'" -vsync vfr scene_%03d.jpg
    ```
*   **多模態 AI 整合**：將擷取的影格一次性餵給 ChatGPT、Claude 或 Gemini 等多模態模型，利用提示詞「請依序讀出每張圖上的文字，並整理成清單」，將 30 分鐘的反覆截圖工作壓縮至 5 分鐘內。

### 2. 知彼解己與教育實踐
*   **深度觀察的習慣**：本工作流不只是一項技術，更呼應了柯維的「知彼解己」原則。藉由把影片「拆解、定格、看清」的過程，強迫大腦慢下來，看清每個瞬間。
*   **教學應用**：規劃引導學生拍攝 1 分鐘默片，並使用此流程進行訊息還原，藉此磨練學生的觀察力與「先看清楚、再說話」的溝通習慣。

詳細操作說明與參數設定，請參閱卡片 [[默片撈重點-ffmpeg-AI]]。

## 實踐案例：Manus AI Agent 實戰與 Skill-Creator 自動化 (WORKFLOW / METHOD)
在 AI Agent 的商業與日常實踐中，**Manus** 雲端全託管 Agent 展現了從「對話型 AI」跨越至「任務型 AI」的劃時代特徵。它不僅可以透過 Chat 模式（0 積分）進行點對點討論，更可在 Agent 模式下操縱虛擬機與瀏覽器，自主在網際網路上檢索資料、使用第三方 Connectors (如 GitHub) 部署並解決複雜專案。

### 1. 簡報與網站自動生成工作流
*   **優化簡報大綱 SOP**：不要直接生成簡報！應先讓 AI 對初始 Prompt 進行擴充優化，隨後讓 AI 進行「反向檢查」，詢問人方需補足哪些細節資訊，在 Chat 模式下確認 15 頁大綱架構後再點擊生成。
*   **多模式投影片選擇**：需要微調細節、展示圖表時選用**專業 (HTML) 模式**；偏向概念與情感傳達、需要極高圖片張力時選用**視覺化模式 (GPT / Nano Banana)**。
*   **個人形象網站自動部署**：上傳 Word/PDF/PPT 等不統一格式素材，讓 Agent 解析並整理成高說服力文案，透過 GitHub Connector 授權自動在 GitHub Actions 部署為靜態前端網頁，並能通過對話自動修正手機破版問題與 WebP 圖片壓縮。

### 2. 建立 Skill-Creator 技能重複化
利用指令 `/skill-creator` 將繁瑣的多輪簡報研究或網站微調 SOP 自動打包成重複使用的技能 (Skills) 存於個人帳戶，日後只需給予新主題便會自動按原流程觸發執行。

詳細實戰步驟與點數節省小技巧，請參閱卡片 [[Manus-AI-Agent實戰教學]]。

## 實踐案例：Edits 智慧短影音剪輯與演算法流量密碼 (WORKFLOW)
影片剪輯是「80秒卡通短影音」工作流中的關鍵一環。**Edits** 作為 Instagram 創作者官方於 2025 年 4 月推出的影片剪輯軟體，為 Reels 與短影音創作提供了絕佳的流量加速器。

### 1. 生態系演算法與 AI 特色
*   **流量演算法加權**：擁有 Meta 官方自家人優待，在 IG 享有更高曝光推薦；壓縮演算法強大（檔案小 40% 但畫質更佳，載入極快）。
*   **AI 輔助創作**：支援靜態圖轉影片的 AI 動畫、AI 融合切換、以及自動聽寫並支援 **AI Highlight（突顯關鍵字）**的智慧字幕。
*   **音訊與色彩精修**：配備 AI 環境降噪（夜市噪音濾除 87%）、色輪與 Curves 曲線工具，綠幕合成速度比 CapCut 快 1.8 倍。

### 2. 短影音進階公式與流量時間軸
*   **音效黃金比例**：`環境音 30% + 主音軌 70% + 瞬效音 15%` 混音配置。
*   **三段式流量時間軸**：前 3 秒以「衝突畫面」留人（Hook），每 7 秒插入「動態貼紙」維持視覺刺激，結尾以「互動問句」模板呼籲行動 (CTA)。

詳細新手使用指南與效果對比，請參閱卡片 [[Edits-影片編輯軟體教學]]。

## 實踐案例：Image Extraction 批次素材收集 (WORKFLOW)
高效的知識庫運作離不開圖片素材的支撐。在製作 Marp/Manus 投影片或撰寫 Markdown 筆記時，**Image Extraction** 提供了免安裝、一鍵抓取網頁整頁圖片的高效手段。

### 1. 免安裝抓圖神器 SOP
*   **智能掃描提取**：貼上網址即可自動解析頁面所有 JPEG/PNG/WebP/SVG/GIF 圖片，並自動剔除浮水印、優先顯示 High-Res 高解析版本。
*   **靈活下載與細節預覽**：支援 `Download All` 一鍵打包 ZIP 以及 `Download Selected` 勾選下載。單獨點擊圖片即可查看檔名、尺寸與 Direct URL，能與 [[ChatGPT-圖片下載腳本]] 形成完美的網頁素材抓取工具組合。

詳細使用步驟，請參閱卡片 [[Image-Extraction-抓圖神器教學]]。

## 實踐案例：NotebookLM + PDNob AI 簡報生成與 PDF 後製高階工作流 (WORKFLOW)
在投影片設計中，若主管或公司要求簡報必須完全契合公司的公版簡報模板，則可以使用 **邏輯前置 (3P) + 風格對齊 (NotebookLM) + 精細後製 (PDNob)** 協同工作流。

### 1. 3P 規劃與 NotebookLM 範本套用
*   **邏輯前置 (3P 框架)**：先不要直接生成簡報！應先讓 AI 針對 **用途 (Purposes)**、**受眾 (Persons)** 與 **架構 (Positions)** 進行內容骨架梳理。
*   **對齊公司範本**：上傳公司的 PPT 模板和 3P 規劃內容。先讓 NotebookLM 將各頁排版設計儲存為「記事」，再將此記事「轉換為來源」，以便在點擊右上角生成簡報時能高度對齊公司品牌色調與視覺細節。

### 2. PDNob 交付級 PDF 後製四步驟
由於 NotebookLM 下載的簡報檔本質上是圖片拼裝的 PDF，我們可以使用專業 PDF 編輯器 **PDNob** 進行高效率後製：
1.  **無損覆蓋浮水印**：利用矩形形狀工具框選 NotebookLM 預設浮水印，並以滴管取色器吸取背景色，完成覆蓋。
2.  **添加公司浮水印**：置入公司「限內部使用」等浮水印，調整字體透明度。
3.  **置入頁碼**：加入「封面除外」的右下角頁碼以符合商務交付標準。
4.  **封裝互動超連結**：拉選區設定「開啟網頁」並填入參考來源的網址，提升文件的互動性和專業度。

詳細操作步驟與 ChatGPT vs Gemini 實測心得對比，請參閱卡片 [[AI簡報高階工作流-NotebookLM-PDNob]]。

## 相關連結
- [Andrej Karpathy Github Gist - LLM Wiki 指令](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [遠見雜誌原文報導](https://www.gvm.com.tw/article/129280)
- [Obsidian 官方網站](https://obsidian.md/)
