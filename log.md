# Knowledge Base Log

这是一份 append-only 的操作日誌。這份日誌可以提供知識庫演進的時間序列，並幫助 LLM 暸解近期執行過哪些操作。

## [2026-04-24] ingest | 勝NotebookLM！前Tesla人Wiki筆記術
- **資料修復**：修復原始損毀之 `raw/` 檔案，補全《遠見雜誌》關於 Karpathy 「LLM Wiki」之全文報導。
- **新增類別**：建立 `wiki/AI工具/` 子目錄，收錄 AI 工具教學與方法論。
- **建立節點**：新增 [[LLM-Wiki-筆記術]]，摘要卡帕西的「File Over App」哲學、自動化編譯特點，以及使用 Antigravity 安裝之步驟。
- **索引更新**：於 [[index.md]] 加入「AI 工具」實體類別與連結。

## [2026-04-24] maintenance | 補完 ETF 經理人資訊
- **數據補完**：針對「主動型」、「市值型」及「高股息」三份 ETF 清單，全面新增「經理人」欄位並填寫共 49 檔標的之對應操盤手姓名。
- **資料校閱**：校對 2026-04 最新公開資訊，確保主動式與被動式 ETF 之經理人資料正確。

- **新增類別**：建立 `wiki/金融投資/` 子目錄，收錄台灣目前上市之主動型 ETF 資訊。
- **數據彙整**：整理共 21 檔主動型 ETF 之代號、保管銀行、配息月份及相關費率比較表（新增 00400A, 00983A, 00986A, 00989A, 00993A, 00995A, 00997A, 00983D）。
- **修正資訊**：根據使用者提供之圖表修正 00982A 的配息月份為 2、5、8、11 月。
- **修正資訊**：根據使用者提供之圖表修正 00990A 的保管銀行為「臺灣銀行」，並更新名稱為「元大AI新經濟」。
- **修正資訊**：根據使用者提供之圖表修正 00994A 的保管銀行為「永豐商業銀行」，並更新名稱為「第一金台股優」。
- **索引更新**：於 [[index.md]] 加入「金融投資」實體類別與連結。
- **新增清單**：建立 [[市值型ETF清單]]，收錄 12 檔市值相關標的之資訊，並補充「保管銀行」欄位以利匯費參考。
- **新增清單**：建立 [[高股息ETF清單]]，收錄 16 檔熱門高股息標的（新增 00907、00961、00964）。
- **修正資訊**：根據使用者提供之圖表修正 00929、00936、00940 的保管銀行，並將多數標的的保管費率調整為 0.04%；另修正 00907 的配息月份為 2、4、6、8、10、12 月。

## [2026-04-22] synthesis | 補充貨物裝載規定 (具體條號)
- **精確化更新**：於 [[道路交通安全規則]] 明確標註高度限制依據為第 79 條（貨車）及第 88 條（機車）。
- **同步更新**：修正裝載規定區塊，加入第 80 條（臨時通行證）之參考。

## [2026-04-22] ingest | 道路交通標誌標線號誌設置規則
- **新增規章**：根據 2026 最新法規收錄「道路交通標誌標線號誌設置規則」。
- **重點摘要**：針對白線寬度（10cm vs 15cm）及其停車效力差異進行定義，包含路面邊線與分隔線之區別。
- **維護同步**：更新 [[index.md]] 並於 `wiki/交通法規/` 建立詳細節點頁面。

## [2026-04-21] maintenance | Wiki 結構重整與索引同步
- **結構重整**：建立 `wiki/System/` 並遷移 `llm-wiki.md`、`llm-wiki-zh.md`；清理根目錄冗餘檔案（CSV、空白 MD）。
- **索引補完**：於 `index.md` 補齊 `職業訓練與補助方案` 及 7 份烘培食譜（基礎戚風、巴斯克、經典生乳捲等）。
- **規範對齊**：確保所有 Wiki 節點符合 `schema.md` 定義之目錄結構。

## [2026-04-18] system | 批次更新原始資料與 Wiki 內容

- **交通法規更新**：同步《道路交通管理處罰條例》於 2026-03-31 施行之最新修正（分心駕駛、學校路段加重刑責、舉發時效修正）。
- **新增烘焙食譜**：收錄 `raw/` 下的新產品 [[鳳梨酥]] 與 [[牛軋糖]]，並建立詳細 Wiki 頁面。
- **數據同步**：根據 `raw/烘培食譜/整理.xlsx` 修正並補完現有食譜的發酵與烘烤參數。
- **結構優化**：更新 [[index.md]] 與 [[烘培食品丙級術科]] 加入新實體連結。

- 整理 `raw/烘培食譜/` 下的丙級烘焙相關資料，包含西點蛋糕與麵包之證照配方 PDF、助教筆記圖片與學科測驗 SOP。
- 於 `wiki/烘培食譜/` 建立了 14 份詳細食譜專頁，整合了成分百分比、重量、製作步驟與助教筆記重點摘要。
- 建立總覽頁面：[[烘培食品丙級術科]] 與 [[烘培食品丙級學科測驗]]。
- 更新 [[index.md]] 加入烘培 Wiki 區塊。

## [2026-04-15] synthesis | 勞工請假規則 (婚假等)
- 根據《勞工請假規則》彙整勞工婚、喪、病假之天數與規範。
- 確立婚假為 8 日，且需於結婚前後特定期限內請畢。
- 建立頁面: [[勞工請假規則]]
- 更新頁面: [[勞工相關法規概覽]]、[[index.md]]

## [2026-04-15] synthesis | 未禮讓行人罰則 (第 44 條)
- 根據台灣最新法規，更新了維基中關於未禮讓行人的罰鍰（提升至 6,000 元）及記點制度。
- 更新頁面: [[道路交通管理處罰條例]]
- 更新頁面: [[常見交通違規罰則]]

## [2026-04-15] synthesis | 行人交通違規罰則 (第 78 條)
- 新增行人未走斑馬線、穿越車道、闖紅燈等違規罰則（罰鍰 500 元）。
- 更新頁面: [[道路交通管理處罰條例]]
- 更新頁面: [[常見交通違規罰則]]

## [2026-04-10] system | Initialize Knowledge Base
- 根據 LLM Wiki 模式建立 `schema.md`、`index.md` 與 `log.md` 等全域結構。
- 建立 `raw` 及 `wiki` 目錄。

## [2026-04-10] ingest | 交通相關法規三份文件
- 讀取 `raw/交通相關法規/` 下的三份法規檔案。
- 於 `wiki/` 建立 `道路交通安全規則.md`、`道路交通管理處罰條例.md`、`道路交通安全基本法.md` 三個實體知識節點頁面。
- 更新 `index.md` 加入實體連結。

## [2026-04-10] ingest | 批次收錄交通相關法規 7 份新文件
- 讀取 `raw/交通相關法規/` 下的其他多份法規，並排除了重複項目。
- 於 `wiki/` 建立了《汽車駕駛人及乘客繫安全帶實施及宣導辦法》等 7 個法規新建實體節點頁面。

## [2026-04-14] ingest | 勞工相關法規 78 份文件批次收錄
- 整理 `raw/勞工相關法規/` 下共 78 份 PDF 與檔案。
- 建立 `wiki/勞工相關法規概覽.md` 作為全域索引與分類導覽。
- 針對 6 份核心母法建立詳細 Wiki 頁面：勞動基準法、工會法、勞工保險條例、勞工退休金條例、性別平等工作法、勞資爭議處理法。
- 更新 `index.md` 加入上述頁面之實體與總結連結。

## [2026-04-14] system | 重整 Wiki 目錄結構
- 為提升可擴張性，於 `wiki/` 下建立 `交通法規/` 與 `勞工法規/` 子目錄。
- 將現有 19 份 Markdown 檔案歸類遷移至對應子目錄。
- 更新 `index.md` 與 `schema.md` 以符合新結構。

## [2026-04-14] synthesis | 勞退新舊制比較分析
- 根據 `勞動基準法` 與 `勞工退休金條例` 彙整產出 [[勞退新舊制比較]] 專頁。
- 透過對照表解析年資可攜性、領取門檻與給付標準之關鍵差異。

## [2026-04-14] synthesis | 退休金與老年給付計算指南
- 整理勞保老年年金與勞退新制專戶之試算公式。
- 於 `wiki/勞工法規/` 建立 [[退休金與老年給付計算]] 知識節點，幫助勞工預估退休現金流。
- 2026-04-25 08:19:47: Ingested YouTube summary [CLAUDE CODE 4小時完整教學：學會Skills / AI 自動工作 / 搜集資料 (2026)](wiki\youtube-notes\CLAUDE CODE 4小時完整教學：學會Skills  AI 自動工作  搜集資料 (2026)_fYuohy6rQ9c.md)

## [2026-04-25] system | Workflow Optimization & Ingest
- 更新 `schema.md` 導入卡片盒筆記法 (Zettelkasten) 與 AI Agent 整理守則。
- Ingest 實測心得文章並補齊完整內容至 `raw/obsidian/`。
- 建立 `cards/` 資料夾並新增 `AI與卡片盒筆記法實測心得.md` 暫時筆記。
- 更新 `wiki/AI工具/LLM-Wiki-筆記術.md`，統整 Karpathy 與 Esor Huang 的 AI PKM 方法論。
- 更新 `index.md` 索引。
- 2026-04-27 19:08:09: Ingested YouTube summary [無痛把 Gemini 裝進電腦！Gemini CLI 讓 AI 直接幫你處理所有檔案，無須任何寫程式背景都能用！【欸那個AJ】](wiki\youtube-notes\無痛把 Gemini 裝進電腦！Gemini CLI 讓 AI 直接幫你處理所有檔案，無須任何寫程式_cXEZ50vgDPw.md)
- 2026-04-27 21:50:19: Ingested YouTube summary [第二集｜Markdown 語法入門：簡潔高效的文本格式化工具【AI 工具課】](wiki\youtube-notes\第二集｜Markdown 語法入門：簡潔高效的文本格式化工具【AI 工具課】_TvFcSiT0n1Q.md)
- 2026-04-27 22:25:08: Ingested YouTube summary [第一集｜探索 Obsidian：打造你的個人知識管理系統【AI 工具課】](wiki\youtube-notes\第一集｜探索 Obsidian：打造你的個人知識管理系統【AI 工具課】_tpEo5O3cR_s.md)
- 2026-04-27 22:32:57: Ingested YouTube summary [第一集｜探索 Obsidian：打造你的個人知識管理系統【AI 工具課】](wiki\youtube-notes\第一集｜探索 Obsidian：打造你的個人知識管理系統【AI 工具課】_tpEo5O3cR_s.md)
- 2026-04-27 22:42:48: Ingested YouTube summary [第一集｜探索 Obsidian：打造你的個人知識管理系統【AI 工具課】](wiki\youtube-notes\第一集｜探索 Obsidian：打造你的個人知識管理系統【AI 工具課】_tpEo5O3cR_s.md)
- 2026-04-27 23:01:24: Ingested YouTube summary [第一集｜探索 Obsidian：打造你的個人知識管理系統【AI 工具課】](wiki\youtube-notes\第一集｜探索 Obsidian：打造你的個人知識管理系統【AI 工具課】_tpEo5O3cR_s.md)
- 2026-04-27 23:09:51: Ingested YouTube summary [第一集｜探索 Obsidian：打造你的個人知識管理系統【AI 工具課】](wiki\youtube-notes\第一集｜探索 Obsidian：打造你的個人知識管理系統【AI 工具課】_tpEo5O3cR_s.md)
- 2026-04-27 23:15:06: Ingested YouTube summary [第五集｜Obsidian 外掛應用【AI 工具課】](wiki\youtube-notes\第五集｜Obsidian 外掛應用【AI 工具課】_WqzHXvEQc5g.md)
- 2026-04-28 21:56:43: Ingested YouTube summary [39分鐘上手Obsidian！基礎操作介紹（電腦、平板、手機全面教學）](wiki\youtube-notes\39分鐘上手Obsidian！基礎操作介紹（電腦、平板、手機全面教學）_9oh9hGE9LsY.md)

## [2026-05-03] ingest & maintenance | ChatGPT 圖片下載與無損浮水印去除
- **文獻歸檔**：將 `raw/obsidian/` 下的 ChatGPT 圖片下載與無損浮水印去除文章永久歸檔。
- **建立卡片**：新增 [[ChatGPT-圖片下載腳本]] 暫時筆記，提煉網頁下載與免浮水印去化工具。
- **建立節點**：新增 `wiki/AI工具/ChatGPT-圖片下載腳本.md`，並將說明補充至 Obsidian。
- **清理索引**：整理 `index.md`，移除多個重複的 YouTube 摘要，保持目錄清爽。
- **索引更新**：於 `index.md` 中的「AI 工具」區塊新增下載腳本連結。

## [2026-05-03] ingest | Jason Tools 整合工具
- **建立卡片**：新增 [[Jason-Tools-功能摘要]]，提煉核心功能與架構設計。
- **建立節點**：新增 `wiki/工具軟體/Jason-Tools.md`，彙整主要模組與技術架構。
- **索引更新**：於 `index.md` 中新增「工具軟體」區塊與 Jason Tools 連結。

- 2026-05-03 23:51:06: Ingested YouTube summary [Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)](wiki\youtube-notes\Rick Astley - Never Gonna Give You Up (Official Vi_dQw4w9WgXcQ.md)

## [2026-05-05] ingest | 海外型與市值型 ETF 清單與說明
- **資料彙整**：整理並補齊海外型 ETF（00646, 00662, 00757, 00830, 00924）與市值型 ETF（006204, 00913）之保管費與追蹤指數資訊。
- **索引更新**：更新 [[index.md]] 並新增對應的清單連結。

## [2026-05-05] ingest | 高股息與海外 REITs ETF 費率整理
- **資料彙整**：補齊高股息型 ETF（00701, 00900）與海外 REITs 型 ETF（00712, 00770）之保管費率與配息月份。
- **資料標準化**：更新台灣 ETF 比較清單，確保除息月份與保管費一致。

## [2026-05-05] ingest | 槓桿與反向型 ETF 清單收錄
- **資料彙整**：收錄台股槓桿型（00631L）與反向型（00632R）等交易工具之費率與風險說明。
- **索引更新**：於 [[index.md]] 新增「槓桿反向型」區塊。

## [2026-05-15] maintenance | Directory Reorganization & Refactoring
- **檔案重整**：建立 bin/ 資料夾，並將 ffmpeg.exe 與 ffprobe.exe 移入，減少根目錄雜亂。
- **腳本歸納**：將 youtube_to_notes.py 與 yt_notes_server.py 移至 scripts/ 資料夾。
- **系統清理**：刪除 __pycache__ 快取資料夾。
- **規範對齊**：本次整理符合 schema.md 中對於目錄整潔與知識庫維護的規範。

## [2026-05-17] ingest | 主動型 ETF 新增與配息頻率標準化
- **新增標的**：收錄 00402A (安聯美國科技領航)、00404A (聯博台灣動能收益50)、00998A (復華全球金融入息) 三檔主動型 ETF 之各項資訊。
- **資料標準化**：校閱並修正全體主動型、半年配與季配型 ETF 之「配息頻率 (月份)」為「實際除息/配息月份」標準。
- **糾正錯誤**：更正 00994A 與 00995A 之配息月份對調錯誤，修正 00403A、00999A、00991A 之評價月混用，並補齊 00405A、00996A 之缺失月份。
- **暫時筆記**：於 `cards/` 建立 [[主動型ETF新增與標準化]] 卡片以摘要本次文獻與操作情境。
- **同步更新**：同步更新 `wiki/` 永久筆記 [[主動型ETF清單]]，並使 Excel 檔案 `台灣ETF比較清單.xlsx` 完全同步。

## [2026-05-17] ingest | 80秒卡通短影音自動化製作流程 (Notion 剪輯)
- **文獻收錄**：自 `Clippings/` 收錄 DennisWei 撰寫之「一篇文章 → 80 秒會說話的卡通片：完整製作流程」教學長文。
- **原始歸檔**：將檔案重命名並移動至 `raw/obsidian/一篇文章到80秒說話卡通片完整製作流程.md` 永久歸檔。
- **暫時筆記**：於 `cards/` 建立 [[一篇文章到80秒說話卡通片完整製作流程]]，摘要 4 大 AI 廚師工具流（Flux 生圖、MiniMax 繁轉簡語音克隆、HyperFrames HTML 渲染及 ffmpeg 對齊）、BGM 選擇與 7 大避坑細節。
- **母筆記回填**：將此自動化實踐案例作為典型 `WORKFLOW`，回填更新至永久 Wiki 筆記 [[LLM Wiki 個人知識庫筆記術]]，防止知識庫發散並健全案例架構。

## [2026-05-17] maintenance | 主動型 ETF 持股明細 Excel 調整與增刪加減碼個股比對
- **新增與美化分頁**：
  - 於 Excel 檔案 `主動型ETF持股明細.xlsx` 新增並套用「新增個股」、「刪除個股」、「加碼張數」、「減碼張數」分頁。
  - 套用鋼鐵藍 (Steel Blue) 高質感美化樣式與自動行高/寬度，使資料清晰美觀。
- **個股新增差異比對**：比對 `20260514` 與 `20260515`，找出 3 檔新增個股，並自動寫入「新增個股」分頁：
  - `00982A` 主動群益台灣強棒新增 `2327` 國巨* (1張)
  - `00985A` 主動野村台灣50新增 `2049` 上銀 (739張)
  - `00989A` 主動摩根美國科技新增 `CBRS.US` Cerebras (0.35張)
- **個股刪除差異比對**：比對 `20260514` 與 `20260515`，找出 5 檔刪除個股，並自動寫入「刪除個股」分頁：
  - `00981A` 主動統一台股增長刪除 `2337` 旺宏 (8張)
  - `00983A` 主動中信ARK創新刪除 `KTOS.US` Kratos (3.329張)
  - `00985A` 主動野村台灣50刪除 `6515` 穎崴 (1張)
  - `00990A` 主動元大AI新經濟刪除 `FORM.US` FormFactor (80.4張)
  - `00995A` 主動中信台灣卓越刪除 `3533` 嘉澤 (7張)
- **加碼張數差異比對**：比對 `20260514` 與 `20260515` 同一檔 ETF 二天都持有的個股，並算出持股張數增加者，共計找出 100 筆加碼明細並寫入「加碼張數」分頁。
- **減碼張數差異比對**：比對 `20260514` 與 `20260515` 同一檔 ETF 二天都持有的個股，並算出持股張數減少者，共計找出 30 筆減碼明細並寫入「減碼張數」分頁（如：00981A 創意減碼 511 張、00991A 亞德客-KY 減碼 299 張、00992A 光聖減碼 250 張等）。
- **自動化腳本功能重構**：將四大持股差異（新增、刪除、加碼、減碼）之比對、高質感鋼鐵藍美化樣式與分頁順序自動校正邏輯，直接重構至 `collect_active_etf_holdings.py` 腳本中。未來在執行主動型 ETF 資料更新時，皆會自動化進行分頁與資料的增量對比更新，達成一鍵式無縫自動維護。

## [2026-05-17] ingest | 用 Agent 養 Agent 運維哲學與遠端修復
- **原始歸檔**：將使用者對 Agent 系統自我維護與遠端管理的經驗隨想，儲存至 `raw/obsidian/用Agent養Agent：開關啟動與遠端修復.md` 永久歸檔。
- **暫時筆記**：於 `cards/` 建立 [[用Agent養Agent]] 卡片，提煉「以強LLM（如ChatGPT）維護、安裝、修復地端Agent系統（OpenClaw、Hermes Agent）」的運維理念，並記錄 Anthropic Channel 的 Telegram 遠端修復應用。
- **母筆記回填**：將此哲學探討作為實踐案例（METHOD 層級），回填至永久 Wiki 筆記 [[LLM Wiki 個人知識庫筆記術]]，探討單 LLM 代理解管地端後多代理架構的存廢思辨。
- **索引更新**：更新 [[index.md]] 中的母筆記描述，補全其對實踐案例的收錄聲明。
- **雙向連結勾連**：將新卡片 [[用Agent養Agent]] 與知識庫中既有的 [[CLAUDE CODE 4小時完整教學：學會Skills  AI 自動工作  搜集資料 (2026)_fYuohy6rQ9c|Claude Code 影片指南]]、[[無痛把 Gemini 裝進電腦！Gemini CLI 讓 AI 直接幫你處理所有檔案，無須任何寫程式_cXEZ50vgDPw|Gemini CLI 影片指南]] 進行了深度的雙向連結勾連，打通 CLI 權限、自動化腳本與地端運維的關聯圖譜。

## [2026-05-17] ingest | Hermes Desktop 桌面伴侶與全圖形化安裝操作指南
- **原始歸檔**：收錄電腦王阿達關於 Windows 一鍵安裝與操作 Hermes Agent GUI 桌面伴侶軟體教學，存入 `raw/obsidian/Hermes Desktop 讓 Windows 直接就能安裝使用 Hermes Agent！初學者也能自己搞定.md`。
- **暫時筆記**：於 `cards/` 建立 [[Hermes-Desktop-GUI安裝與功能摘要]]，梳理其引導式首次安裝（Git, uv, Python 3.11+ 依賴一鍵託管）、本地/遠端後端模式、22 個斜線指令、14 組工具集、16 種網關平台（Telegram/Discord）配置，以及 Cron 圖形化排程任務等核心特性與 Windows 關機失效之限制。
- **母筆記回填**：將此 GUI 工具實踐案例作為地端生態新進展，回填至永久 Wiki 筆記 [[LLM Wiki 個人知識庫筆記術]]，豐富「Agent 系統運維」之實踐案例。
- **雙向關聯勾連**：將此新卡片與 [[用Agent養Agent]]、[[CLAUDE CODE 4小時完整教學：學會Skills  AI 自動工作  搜集資料 (2026)_fYuohy6rQ9c|Claude Code 影片指南]]、[[LLM Wiki 個人知識庫筆記術]] 進行了網狀雙向連結。
- **清理暫存**：清理並刪除了 `Clippings/` 下的原始剪輯檔案，維持目錄乾淨整潔。

## [2026-05-17] ingest | 不靠聲音與字幕從默片撈重點的 ffmpeg + AI 流程
- **原始歸檔**：將使用者分享的 5 分鐘默片重點萃取實作紀錄，儲存至 `raw/obsidian/我學會了一招：不靠聲音、不靠字幕，從一支默片裡撈出 10 個重點.md` 永久歸檔。
- **資源整理**：將 21 秒字卡默片 infographic 圖像複製並命名為 `raw/assets/ffmpeg-silent-video-to-10-points.png` 存放於 assets 目錄中，並於 raw 文件中進行 Obsidian 圖片內嵌。
- **暫時筆記**：於 `cards/` 建立 [[默片撈重點-ffmpeg-AI]] 卡片，摘要無聲短影音 OCR 萃取之三步驟、ffmpeg 定時抽影格與進階場景切換偵測指令，以及知彼解己的教育應用。
- **母筆記回填**：將此自動化實踐案例作為典型 `WORKFLOW`，回填更新至永久 Wiki 筆記 [[LLM Wiki 個人知識庫筆記術]]，豐富其「短影音知識萃取」之實踐案例。
- **索引更新**：更新 [[index.md]] 中的母筆記描述，補齊其對 ffmpeg 默片重點萃取案例的收錄聲明。

## [2026-05-19] maintenance | 主動型 ETF 持股資料日更與歷史變動統計
- **持股資料更新**：成功運行 `collect_active_etf_holdings.py`，從 MoneyDJ 爬取今日（2026/05/19）最新 28 檔主動型與被動型 ETF 持股數據，共解析 1504 筆明細。
- **歷史數據累加**：驗證 Excel 檔案 `主動型ETF持股明細.xlsx`，將今日的持股異動（新增、刪除、加碼、減碼）順利累加於歷史工作表中，未破壞 `20260518` 及更早之歷史紀錄。
- **報告同步更新**：同步生成並更新 `wiki/金融投資/主動型ETF持股變動.md` 與 `wiki/金融投資/主動型ETF持股彙總.md`，提供前 50 大熱門持股的加總比例排名（台積電以 188.17% 與 20 檔 ETF 涵蓋率穩居第一，台光電及台達電分列二三）。

## [2026-05-19] ingest | Manus AI Agent 實戰、Edits 智慧短影音剪輯與 Image Extraction 抓圖神器
- **原始歸檔**：將 `Clippings/` 下的三篇新文獻成功寫入至 `raw/obsidian/` 永久存檔：
  - `【Manus 實戰教學】從研究、簡報到個人網站，帶你掌握普通人也能上手的 AI Agent.md`
  - `Edits 下載方法＋新手使用大全.md`
  - `教學／Image Extraction「抓圖神器」免安裝 貼網址1鍵抓整頁圖片.md`
- **暫時筆記**：於 `cards/` 建立三張專屬卡片，提煉其核心機制與實戰應用：
  - [[Manus-AI-Agent實戰教學]]：歸納任務型 AI 特徵、Manus 的 4 步簡報生成工作流、GitHub Actions 自動部署網頁、以及利用 `/skill-creator` 將多輪對話打包為重複使用 Skill 之 SOP。
  - [[Edits-影片編輯軟體教學]]：梳理 Meta 生態演算法流量紅利（演算法加權、4K無損壓縮 -40% 檔案大小）、AI Caption Highlight 與降噪（濾除 87% 環境音）、以及 `30%環境音+70%主音軌+15%瞬效音` 混音比例與 3 段式流量時間軸公式。
  - [[Image-Extraction-抓圖神器教學]]：提煉 Image Extraction 免安裝、一鍵打包 `Download All` / `Download Selected` 、無浮水印、高解析度優先之特色與 4 步抓圖 SOP。
- **母筆記回填**：將三篇文獻精華分別回填至 Wiki 永久母筆記 [[LLM Wiki 個人知識庫筆記術]] 的實踐案例中（包含 Manus 的 WORKFLOW / METHOD、Edits 的 WORKFLOW、Image Extraction 的 WORKFLOW），實現了卡片盒回填，無任何無端發散。
- **索引與清理**：更新全域索引 [[index.md]] 中的 AI 工具母筆記案例描述，並安全刪除 `Clippings/` 下的暫存剪貼檔案，保持系統目錄清爽。

## [2026-05-19] maintenance | 移除 YouTube 影片摘要 Rick Astley
- **檔案刪除**：自 `wiki/youtube-notes/` 刪除 `Rick Astley - Never Gonna Give You Up (Official Vi_dQw4w9WgXcQ.md` 影片摘要筆記。
- **索引更新**：同步自全域索引 [[index.md]] 中移除該筆記之相對應參考連結，確保知識庫系統結構無斷鍊。

## [2026-05-19] ingest | OpenCode 地端 AI Agent 與 NotebookLM + PDNob 簡報高階工作流
- **原始歸檔**：將 `Clippings/` 下的兩篇文獻移入 `raw/obsidian/` 永久存檔：
  - `OpenCode基本功 EP01：免費 AI Agent 啟手式.md`
  - `別再只用一句話叫 AI 生成簡報！學會這個隱藏技巧.md`
- **暫時筆記**：於 `cards/` 建立兩張結構化 Zettelkasten 卡片：
  - [[OpenCode-AI-Agent地端部署]]：記錄以電腦硬體比喻 Agent 各元件的 Harness Metaphor，撰寫 8 步環境安裝與交互介面啟用指令，並包含 ReAct 思考除錯與自訂 `ToolBase` 工具之實體擴充架構。
  - [[AI簡報高階工作流-NotebookLM-PDNob]]：提煉邏輯前置的 3P 框架（Purposes, Persons, Positions），整理 NotebookLM 將排版記事轉為來源以匹配 PPT 公版模板之風格對齊工作流，並歸納 PDNob 六大 PDF 後製技巧（形狀同色無損遮罩、浮水印添加、右下角封面除外頁碼、超連結選區封裝）與三大 AI 簡報工具實測心得對比。
- **母筆記回填**：將其精華分別回填至永久母筆記 [[LLM Wiki 個人知識庫筆記術]] 的實踐案例中（包含 OpenCode 地端部署之 METHOD、NotebookLM+PDNob 簡報高階工作流之 WORKFLOW）。
- **索引與清理**：更新全域索引 [[index.md]] 的 AI 工具母筆記條目描述，並安全清理 `Clippings/` 目錄下的暫存剪貼檔，保持目錄結構乾淨。

## [2026-05-19] active-etf | 每日持股更新與全市場 28 檔覆蓋
- **腳本升級**：將 `collect_active_etf_holdings.py` 的預設追蹤清單 `DEFAULT_TICKERS` 自 25 檔補足至全市場 28 檔主動型 ETF，補足了 `00402A`、`00404A` 與 `00998A`。
- **數據採集與比對**：執行收集腳本，成功自 MoneyDJ 爬取 28 檔 ETF（共 1504 筆持股紀錄），順利寫入 `20260519` 分頁，並比對 `20260518` ➔ `20260519` 異動，寫入 `主動型ETF持股明細.xlsx` 中的「新增個股」、「刪除個股」、「加碼張數」與「減碼張數」歷史分頁中。
- **報告更新**：重新生成並更新 [主動型ETF持股變動.md](file:///i:/Mark/my-kb/wiki/金融投資/主動型ETF持股變動.md) 與 [主動型ETF持股彙總.md](file:///i:/Mark/my-kb/wiki/金融投資/主動型ETF持股彙總.md)。
- **比較清單同步**：於 `collect_active_etf_holdings.py` 腳本中實作並串接 `update_comparison_xlsx` 功能，使每日數據採集時自動解析 `主動型ETF清單.md` 表格，並無縫同步更新 [台灣ETF比較清單.xlsx](file:///i:/Mark/my-kb/wiki/金融投資/台灣ETF比較清單.xlsx) 中的「主動型」分頁（已順利寫入 28 檔最新主動型 ETF 資料）。

## [2026-05-20] active-etf | 每日持股更新與比較清單同步
- **數據採集與比對**：成功運行 `collect_active_etf_holdings.py`，從 MoneyDJ 爬取今日（2026/05/20）最新 28 檔主動型與被動型 ETF 持股數據，共解析 1490 筆明細，並將數據寫入 `20260520` 工作表。
- **歷史數據累加**：自動將今日的持股異動比對昨日（2026/05/19）成果，更新至 Excel 檔案 `主動型ETF持股明細.xlsx` 中的「新增個股」、「刪除個股」、「加碼張數」與「減碼張數」歷史分頁中，並維持分頁排序。
- **報告更新**：同步重新生成並更新 [主動型ETF持股變動.md](file:///i:/Mark/my-kb/wiki/金融投資/主動型ETF持股變動.md) 與 [主動型ETF持股彙總.md](file:///i:/Mark/my-kb/wiki/金融投資/主動型ETF持股彙總.md)，以便快速檢視前 50 大熱門持股與涵蓋度。
- **比較清單同步**：解析 [主動型ETF清單.md](file:///i:/Mark/my-kb/wiki/金融投資/主動型ETF清單.md) 中的最新比較表，自動更新 [台灣ETF比較清單.xlsx](file:///i:/Mark/my-kb/wiki/金融投資/台灣ETF比較清單.xlsx) 中的「主動型」分頁（已更新 28 檔主動型 ETF 資訊）。

## [2026-05-21] active-etf | 每日持股更新與比較清單同步
- **數據採集與比對**：成功運行 `collect_active_etf_holdings.py`，從 MoneyDJ 爬取今日（2026/05/21）最新 28 檔主動型與被動型 ETF 持股數據，共解析 1499 筆明細，並將數據寫入 `20260521` 工作表。
- **歷史數據累加**：自動將今日的持股異動比對昨日（2026/05/20）成果，更新至 Excel 檔案 `主動型ETF持股明細.xlsx` 中的「新增個股」、「刪除個股」、「加碼張數」與「減碼張數」歷史分頁中，並維持分頁排序。
- **報告更新**：同步重新生成並更新 [主動型ETF持股變動.md](file:///i:/Mark/my-kb/wiki/金融投資/主動型ETF持股變動.md) 與 [主動型ETF持股彙總.md](file:///i:/Mark/my-kb/wiki/金融投資/主動型ETF持股彙總.md)，以便快速檢視前 50 大熱門持股與涵蓋度。
- **比較清單同步**：解析 [主動型ETF清單.md](file:///i:/Mark/my-kb/wiki/金融投資/主動型ETF清單.md) 中的最新比較表，自動更新 [台灣ETF比較清單.xlsx](file:///i:/Mark/my-kb/wiki/金融投資/台灣ETF比較清單.xlsx) 中的「主動型」分頁（已更新 28 檔主動型 ETF 資訊）。

## [2026-05-25] active-etf | 每日持股更新與比較清單同步
- **數據採集與比對**：成功運行 `collect_active_etf_holdings.py`，從 MoneyDJ 爬取今日（2026/05/25）最新 28 檔主動型與被動型 ETF 持股數據，共解析 1502 筆明細，並將數據無縫寫入 `wiki/金融投資/主動型ETF持股明細.xlsx` 中的 `20260525` 工作表。
- **歷史數據累加**：自動將今日的持股異動比對前次（2026/05/22）成果，安全更新至 Excel 檔案 `主動型ETF持股明細.xlsx` 中的「新增個股」、「刪除個股」、「加碼張數」與「減碼張數」歷史分頁中，並維持分頁排序與所有歷史資料分頁完整性。
- **報告更新**：同步重新生成並更新 [主動型ETF持股變動.md](file:///i:/Mark/my-kb/wiki/金融投資/主動型ETF持股變動.md) 與 [主動型ETF持股彙總.md](file:///i:/Mark/my-kb/wiki/金融投資/主動型ETF持股彙總.md)，以便快速檢視前 50 大熱門持股與涵蓋度。
- **比較清單同步**：解析 [主動型ETF清單.md](file:///i:/Mark/my-kb/wiki/金融投資/主動型ETF清單.md) 中的最新比較表，自動更新 [台灣ETF比較清單.xlsx](file:///i:/Mark/my-kb/wiki/金融投資/台灣ETF比較清單.xlsx) 中的「主動型」分頁（已更新 28 檔主動型 ETF 資訊）。

## [2026-05-26] active-etf | 每日持股更新與比較清單同步
- **數據採集與比對**：成功運行 `collect_active_etf_holdings.py`，從 MoneyDJ 爬取今日（2026/05/26）最新 28 檔主動型與被動型 ETF 持股數據，共解析 1502 筆明細，並將數據無縫寫入 `wiki/金融投資/主動型ETF持股明細.xlsx` 中的 `20260526` 工作表。
- **歷史數據累加**：自動將今日的持股異動比對昨日（2026/05/25）成果，安全更新至 Excel 檔案 `主動型ETF持股明細.xlsx` 中的「新增個股」、「刪除個股」、「加碼張數」與「減碼張數」歷史分頁中，並維持分頁排序與所有歷史資料分頁完整性。
- **明細分頁公式與功能升級**：修改並優化 `collect_active_etf_holdings.py`，為「加碼張數」與「減碼張數」分頁新增「原張數」、「加碼後張數/減碼後張數」及「加碼比例/減碼比例」欄位，並套用除零保護之 Excel 公式 `=IF(F{row}=0,0,H{row}/F{row})`（即 `(加碼張數-原張數)/原張數`）與百分比格式，大幅提升數據可讀性與深度分析。
- **每週加減碼明細計算**：執行 `add_weekly_summary.py`，順利計算並更新 Excel 檔案 `主動型ETF持股明細.xlsx` 中的「Weekly Additions」與「Weekly Reductions」工作表，完成每週持股變動 analysis。
- **報告與比較清單更新**：同步重新生成並更新 [主動型ETF持股變動.md](file:///i:/Mark/my-kb/wiki/金融投資/主動型ETF持股變動.md) 與 [主動型ETF持股彙總.md](file:///i:/Mark/my-kb/wiki/金融投資/主動型ETF持股彙總.md)，並解析 [主動型ETF清單.md](file:///i:/Mark/my-kb/wiki/金融投資/主動型ETF清單.md) 將數據同步更新至 [台灣ETF比較清單.xlsx](file:///i:/Mark/my-kb/wiki/金融投資/台灣ETF比較清單.xlsx) 中的「主動型」分頁。

## [2026-05-27] active-etf | 每日持股更新與每日個股合計功能新增
- **數據採集與比對**：成功運行 `collect_active_etf_holdings.py`，從 MoneyDJ 爬取昨日（2026/05/27）最新 28 檔主動型與被動型 ETF 持股數據，共解析 1502 筆明細，並將數據無縫寫入 `wiki/金融投資/主動型ETF持股明細.xlsx` 中的 `20260527` 工作表。
- **差異比對明細升級**：在「加碼張數」與「減碼張數」分頁新增「原張數」、「最新張數」及「加減碼比例」欄位，使用 Excel 百分比公式，優化變動趨勢分析。
- **每日個股合計功能**：新增 `add_daily_stock_total.py` 彙整工具並順利執行，在 Excel 檔案中產生「每日個股合計」工作表，彙整每日各標的之持有總張數、每日張數增減與增減比例。
- **報告更新與比較清單同步**：同步更新 [主動型ETF持股彙總.md](file:///i:/Mark/my-kb/wiki/金融投資/主動型ETF持股彙總.md)、[主動型ETF持股變動.md](file:///i:/Mark/my-kb/wiki/金融投資/主動型ETF持股變動.md) 以及 [台灣ETF比較清單.xlsx](file:///i:/Mark/my-kb/wiki/金融投資/台灣ETF比較清單.xlsx)。

## [2026-05-28] active-etf | 每日持股更新與每日個股合計同步
- **數據採集與比對**：成功運行 `collect_active_etf_holdings.py`，從 MoneyDJ 爬取今日（2026/05/28）最新 28 檔主動型與被動型 ETF 持股數據，共解析 1502 筆明細，並寫入 `wiki/金融投資/主動型ETF持股明細.xlsx` 中的 `20260528` 工作表，完成增量歷史比對（新增、刪除、加碼、減碼分頁自動更新）。
- **每週加減碼明細計算**：執行 `add_weekly_summary.py`，順利計算並更新 Excel 檔案中的「Weekly Additions」與「Weekly Reductions」工作表。
- **每日個股合計同步**：執行 `add_daily_stock_total.py`，順利在 Excel 檔案中更新「每日個股合計」工作表，累計共 11 個交易日的資料（新增 05/28 數據，合計 8,079 列）。
- **報告與比較清單更新**：同步重新生成並更新 [主動型ETF持股變動.md](file:///i:/Mark/my-kb/wiki/金融投資/主動型ETF持股變動.md) 與 [主動型ETF持股彙總.md](file:///i:/Mark/my-kb/wiki/金融投資/主動型ETF持股彙總.md)，並解析 [主動型ETF清單.md](file:///i:/Mark/my-kb/wiki/金融投資/主動型ETF清單.md) 將數據同步更新至 [台灣ETF比較清單.xlsx](file:///i:/Mark/my-kb/wiki/金融投資/台灣ETF比較清單.xlsx) 中的「主動型」分頁。

## [2026-05-28] etf-data | 海外型ETF比較清單欄位補齊
- **缺失資料檢查**：讀取 [台灣ETF比較清單.xlsx](file:///i:/Mark/my-kb/wiki/金融投資/台灣ETF比較清單.xlsx) 中「海外型」分頁，發現兩筆新募集 ETF 資料不完整：**009823 群益標普500 ETF** 與 **009824 群益美國科技巨頭ETF基金**。
- **線上資料查詢**：透過群益投信官網（capitalfund.com.tw）與公開資訊補齊各欄位：
  - **009823**：補齊經理人（謝明志）、修正配息頻率（季配 2,5,8,11 月）、修正經理費格式（0.20% 級距）、修正保管費（0.06%~0.10% 級距）。
  - **009824**：補齊經理人（李晉含）、修正保管銀行（中國信託商業銀行）、補齊經理費（0.80%）、補齊保管費（0.06%~0.12% 級距）。
- **雙檔同步**：將補齊結果寫入 Excel 「海外型」分頁，並同步更新 [海外型ETF清單.md](file:///i:/Mark/my-kb/wiki/金融投資/海外型ETF清單.md)，新增兩檔 ETF 的表格列與投資分類說明（第5類：新興美股全市場型）。

## [2026-05-29] active-etf | 每日持股更新與每週加減碼、個股合計同步
- **數據採集與比對**：成功運行 `collect_active_etf_holdings.py`，從 MoneyDJ 爬取今日（2026/05/29）最新 28 檔主動型與被動型 ETF 持股數據，共解析 1501 筆明細，無縫寫入 `wiki/金融投資/主動型ETF持股明細.xlsx` 中的 `20260529` 工作表。
- **歷史數據與差異比對**：自動將今日持股異動比對昨日（2026/05/28）成果，更新「新增個股」、「刪除個股」、「加碼張數」與「減碼張數」歷史分頁中。
- **每週加減碼明細計算**：執行 `add_weekly_summary.py`，順利計算並更新 Excel 中的「Weekly Additions」與「Weekly Reductions」工作表，完成本週（截至05/29）持股變動分析。
- **每日個股合計同步**：執行 `add_daily_stock_total.py`，順利在 Excel 中更新「每日個股合計」工作表，累計共 12 個交易日的資料（新增 05/29 數據，合計 5,921 列）。
- **報告與比較清單更新**：同步重新生成並更新 [主動型ETF持股變動.md](file:///i:/Mark/my-kb/wiki/金融投資/主動型ETF持股變動.md) 與 [主動型ETF持股彙總.md](file:///i:/Mark/my-kb/wiki/金融投資/主動型ETF持股彙總.md)，並解析 [主動型ETF清單.md](file:///i:/Mark/my-kb/wiki/金融投資/主動型ETF清單.md) 將數據同步更新至 [台灣ETF比較清單.xlsx](file:///i:/Mark/my-kb/wiki/金融投資/台灣ETF比較清單.xlsx) 中的「主動型」分頁。

## [2026-05-29] ingest | Codex 桌面版與 Ollama 本地模型串接
- **原始歸檔**：將 `Clippings/` 下的新文獻成功移入 `raw/obsidian/免費無限使用 Codex 桌面版！一個指令，就能透過 Ollama 輕鬆串接本地 AI 模型.md` 進行永久存檔。
- **暫時筆記**：於 `cards/` 建立專屬卡片 [[Codex-Ollama-本地模型串接]]，摘要 Ollama v0.24.0 對 Codex 桌面版的本地串接支援、串接核心指令 `ollama launch`、隱私與成本優勢以及高隱私開發沙盒之應用情境。
- **母筆記回填**：將此本地模型串接實踐案例作為地端適配與無限量推論新進展，回填至 Wiki 永久母筆記 [[LLM Wiki 個人知識庫筆記術]] 的實踐案例中，豐富其「用 Agent 養 Agent 系統運維」之實踐案例。
- **索引與清理**：更新全域索引 [[index.md]] 中的 AI 工具母筆記案例描述，並安全清理 `Clippings/` 目錄下的暫存剪貼檔，保持目錄結構乾淨。


## [2026-05-31] system | AntiGravity 專屬懶人包與技能同步
- **技能包安裝與更新**：從 GitHub 來源同步更新 `skills/` 下的 AntiGravity 技能。
  - 更新並同步了 `02-github`、`03-firebase`、`04-draw` 及 `05-workflow` 的技能描述與規則（補齊安全規則與注意事項）。
  - 對於 `06-obsidian`（連接 Obsidian），為保留本地專屬的 vault 實體路徑（`I:\Mark\my-kb\raw\obsidian`），特別採取了保留本地原設定的防覆蓋策略。
- **主懶人包同步**：同步主文件 `09-AntiGravity專屬懶人包.md` 至最新的 v1.4 版本，完整定義了開收工流程與 Obsidian MCPVault 配置。

## [2026-06-19] system | 安裝自訂技能與同步懶人包
- **自訂技能安裝**：
  - 新增 `skills/07-skill-creator`（技能製造機）以引導自訂技能設計與生成。
  - 新增 `skills/08-find-skills`（技能搜尋員）以列出與說明已安裝的技能。
  - 新增 `skills/09-smart-search`（智慧搜尋）提供多維度全文檢索與內容定位指南。
  - 新增 `skills/10-infographic-builder`（資訊圖表生成）提供結構化圖表設計、Mermaid、SVG 及 AI 生圖渲染之指引。
- **安裝清單更新**：更新 `skills/00-install-all/SKILL.md`，將新增的自訂技能註冊至一鍵安裝列表中。
- **懶人包同步**：更新主文件 `09-AntiGravity專屬懶人包.md` 至 v1.6，記錄新技能的加入與版本修訂。

## [2026-06-26] system | 新增 SlideMaster 簡報影片化技能
- **自訂技能安裝**：
  - 新增 `skills/12-slidemaster` 技能，協助使用者透過三步驟（寫講稿、配語音、合成影片）將簡報投影片完整轉換為影片。
  - 在 `skills/12-slidemaster/scripts/` 下建立自動化影片合成腳本 `merge_video.py`，支援多影像與多音訊依自然排序批次合成。
- **安裝清單更新**：更新 `skills/00-install-all/SKILL.md`，將 SlideMaster 註冊至一鍵安裝列表中。
