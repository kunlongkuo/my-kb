# my-kb/skills 功用表（完整 21 項）

## 00-install-all
---
name: antigravity-install-all
description: 一次安裝所有 AntiGravity 懶人包技能。說「全部安裝」「裝完所有 AntiGravity 懶人包」時載入。
---

# 一次安裝全部技能

依序載入並執行：

1. **01-notebooklm** — 連接 NotebookLM
2. **02-github** — 連接 GitHub
3. **03-firebase** — 連接 Firebase
4. **04-draw** — 生圖指引
5. **05-workflow** — 開工/收工/初始化
6. **06-obsidian** — 連接 Obsidian (MCPVault)
7. **07-skill-creator** — 技能製造機
8. **08-find-skills** — 技能搜尋員
9. **09-smart-search** — 智慧搜尋
10. **10-infographic-builder** — 資訊圖表生成
11. **11-question-bank-reverse** — 題庫逆向衍生（讀取 .docx 題庫，分析命題概念，生出全新試題，輸出 Word 試卷）

## 01-notebooklm
---
name: antigravity-notebooklm
description: 在 AntiGravity 連接 NotebookLM MCP。說「連接 NotebookLM」「設定 NotebookLM」時載入。
---

# 連接 NotebookLM（AntiGravity 版）

## 步驟

### 1. 安裝
```bash
uv tool install notebooklm-mcp-cli
nlm --version
```

### 2. 登入
```bash
nlm login
```
（瀏覽器 OAuth，選正確的 Google 帳號）

## 02-github
﻿---
name: antigravity-github
description: 在 AntiGravity 連接 GitHub CLI。說「連接 GitHub」「設定 GitHub」時載入。
---

# 連接 GitHub（AntiGravity 版）

## 步驟

### 1. 檢查
```bash
gh auth status
```

### 2. 登入
```bash
gh auth login --web --git-protocol https
```

### 3. 設定 Git 使用者

## 03-firebase
﻿---
name: antigravity-firebase
description: 在 AntiGravity 連接 Firebase MCP。說「連接 Firebase」「設定 Firebase」時載入。
---

# 連接 Firebase（AntiGravity 版）

## 步驟

### 1. 安裝與登入
```bash
npx.cmd -y firebase-tools@latest --version
npx.cmd -y firebase-tools@latest login
npx.cmd -y firebase-tools@latest projects:list
```

### 2. 註冊 MCP
```json
"firebase": {
  "type": "local",

## 04-draw
﻿---
name: antigravity-draw
description: AntiGravity 生圖指引。說「生圖」「畫圖」「產生圖片」時載入。
---

# 生圖（AntiGravity 版）

## 兩條路

| 路線 | 說明 |
|------|------|
| A：內建生圖 | 直接用自然語言產圖，不需 API Key |
| B：API 路線 | 需 `OPENAI_API_KEY`，參考 OpenCode 懶人包 #08 |

## 建議提示格式

```
生成一張圖片：
用途：
尺寸比例：

## 05-workflow
---
name: antigravity-workflow
description: AntiGravity 開工/收工/新專案初始化流程。說「開工」「收工」「初始化專案」時載入。
---

# 開工 / 收工 / 新專案初始化

## 開工
1. 讀取 `ANTIGRAVITY.md`
2. 讀取專案筆記重點
3. `git status` + 最近 commit
4. 回報狀態與建議下一步
5. 不自動 pull/commit/push

## 收工
1. 檢查敏感資料（API key、token、學生真名等）
2. 更新 `README.md`，寫清楚：專案用途、目前功能、啟動方式、部署方式、環境變數、已知問題、下一步
3. 更新 `docs/PROGRESS.md`，以日期記錄：今天完成什麼、改了哪些重要檔案、做了哪些決策、目前卡在哪裡、下次接手要先看什麼
4. 更新專案筆記（完成事項、下一步、踩坑）
5. 只在規則改變時更新 ANTIGRAVITY.md

## 06-obsidian
---
name: antigravity-obsidian
description: 在 AntiGravity 連接 Obsidian MCP (MCPVault)。說「連接 Obsidian」「設定 Obsidian」時載入。
---

# 連接 Obsidian（AntiGravity 版）

## 步驟

### 1. 找到 vault
請先確認 Obsidian vault 的實體路徑。
- `I:\Mark\my-kbaw\obsidian`

### 2. 安裝 MCPVault
在命令提示字元或 PowerShell 中執行安裝：
```powershell
npm.cmd install -g @bitbonsai/mcpvault
where.exe mcpvault
```
常見安裝路徑：

## 07-skill-creator
---
name: antigravity-skill-creator
description: 協助使用者在專案中建立、修改與最佳化自訂技能（Skills）。當使用者說「建立技能」「新增技能」「製作技能」「設計技能」「skill-creator」時載入。
---

# 技能製造機（Skill-Creator）

本技能旨在引導使用者與 AI 代理（Antigravity）協同合作，快速設計、建立、修改與最佳化專案自訂技能（Custom Skills），將繁瑣的多步驟 SOP 自動打包成隨插即用的技能模組。

## 技能開發流程 (SOP)

當載入此技能時，請依照以下步驟引導使用者：

### STEP 1：需求收集與釐清
透過簡短的問答，向使用者確認以下基本資訊：
1. **技能名稱 (Skill Name)**：英文短標籤（例如 `auto-report`）與中文名稱。
2. **主要功能與用途**：該技能要解決什麼重覆性工作？期望的「完成定義 (Definition of Done)」為何？
3. **觸發詞與情境**：在什麼情境下，使用者會下達什麼指令來觸發此技能？
4. **所需依賴與工具**：是否需要連接外部 API、本機指令、MCP 伺服器或特定 Python/Bash 腳本？

## 08-find-skills
---
name: antigravity-find-skills
description: 協助使用者在專案中搜尋已安裝的自訂技能（Skills）。當使用者說「搜尋技能」「有哪些技能」「尋找技能」「find-skills」時載入。
---

# 技能搜尋員（Find-Skills）

本技能旨在協助使用者快速檢索與盤點目前專案知識庫中已安裝的所有自訂技能（Custom Skills），並展示其名稱、觸發條件與功能描述，以利重複使用。

## 執行流程 (SOP)

當使用者觸發此技能時，請執行以下步驟：

### STEP 1：掃描技能目錄
1. 列出專案根目錄下 `skills/` 資料夾內的所有子資料夾。
2. 逐一檢查每個子資料夾中是否存在 `SKILL.md` 檔案。

### STEP 3：讀取與解析技能資訊
1. 對於每個找到的 `SKILL.md` 檔案，讀取其前 10 行以解析 YAML Frontmatter。
2. 提取以下核心屬性：

## 09-smart-search
---
name: antigravity-smart-search
description: 協助使用者在整個知識庫（含 wiki、cards、raw、Obsidian）進行多維度智慧搜尋與內容定位。當使用者說「智慧搜尋」「全文檢索」「搜尋內容」「smart-search」時載入。
---

# 智慧搜尋（Smart-Search）

本技能旨在為個人知識庫提供高效且精準的多維度全文檢索與內容定位能力，幫助使用者快速找到跨越不同卡片、Wiki 及原始文件的關聯知識。

## 執行流程 (SOP)

當使用者發起智慧搜尋請求時，請執行以下步驟：

### STEP 1：確認搜尋關鍵字與範圍
1. 向使用者確認要搜尋的關鍵字（可支援多個字詞或簡單正則表達式）。
2. 確認搜尋範圍限制（預設為全知識庫，亦可限制在 `wiki/`、`cards/` 或 `raw/` 內）。

### STEP 2：執行搜尋與資料過濾
1. **全文檢索**：使用 `grep_search` 在指定路徑下執行不區分大小寫的搜尋。
2. **優先權排序**：

## 10-infographic-builder
---
name: antigravity-infographic-builder
description: 協助使用者在專案中設計與生成各類資訊圖表（Infographics）、流程圖、架構圖與數據圖。當使用者說「產生圖表」「製作資訊圖表」「生成流程圖」「畫架構圖」「infographic-builder」時載入。
---

# 資訊圖表生成（Infographic-Builder）

本技能旨在協助使用者根據不同的展示需求，設計並生成高品質的資訊圖表（如流程圖、關係圖、統計圖或海報插圖），並自動建議最適用的渲染技術。

## 執行流程 (SOP)

當載入此技能時，請依照以下步驟引導使用者：

### STEP 1：釐清圖表需求與類型
向使用者確認以下重點，以決定最適合的製作技術：
1. **圖表主題與目的**：想要傳達什麼核心觀點或數據？
2. **圖表類型選擇**：
   - **流程/關係圖**（如架構圖、心智圖、時間軸、決策流程）
   - **數據統計圖**（如折線圖、長條圖、圓餅圖）
   - **視覺概念圖**（如文宣插圖、海報、卡片式排版）

## 11-question-bank-reverse
---
name: antigravity-question-bank-reverse
description: 讀取專案目錄中的題庫 Word 檔（如 題庫.docx），分析命題概念與誘答邏輯，逆向工程生出全新相似試題，並產出格式化的 Word 試卷。當使用者說「讀取題庫」「逆向出題」「幫我出新題」「題庫逆向衍生」「question-bank-reverse」「出相似題」「命題神技」時載入。
---

# 題庫逆向衍生工作流（Question Bank Reverse Engineering）

本技能旨在讀取使用者提供的 Word 題庫檔案，深度分析命題規則與邏輯，再依「概念遷移」原則，憑空生出品質相當的全新試題，最終產出排版整齊的 Word 試卷。

## 先決條件確認

載入此技能後，先確認以下項目：
1. 請使用者確認題庫 `.docx` 檔案是否已放入專案目錄（預設路徑：知識庫根目錄或 `raw/` 資料夾）。
2. 詢問**年段**（國中 / 高中）與**科目**（國文、數學、英文…等）。
3. 詢問**輸出目錄**（預設 `outputDir/`，若不存在則自動建立）。
4. 若使用者沒有提供以上資訊，以合理預設值繼續，並在回報時說明所用假設。

---

## STEP 1：讀取與深度分析題庫

## 12-slidemaster
---
name: antigravity-slidemaster
description: 協助使用者透過 SlideMaster 三步驟（寫講稿、配語音、合成影片）將簡報投影片（PDF/PPTX/圖片）轉為完整影片。當使用者說「SlideMaster」「投影片轉影片」「投影片變影片」「簡報合成影片」「簡報影片化」等時載入。
---

# 🎬 SlideMaster 投影片轉影片服務

本技能旨在將原本繁瑣的「投影片製作影片」工作流（寫講稿、錄音、對字幕、剪接、輸出）化繁為簡。透過 AI 的三步驟導引，協助使用者快速、一鍵地將靜態投影片（PDF、PPTX 或圖片）轉化為高質感的口語旁白影片。

---

## ⚡ 核心精神：把投影片一路送到「影片」終點線
當用戶完成投影片後，往往面臨四大折磨：
1. **寫講稿**：從零開始，卡很久。
2. **自己錄音**：講錯重錄，超崩潰。
3. **配字幕與剪接**：步驟繁瑣，耗時費力。
4. **輸出影片**：折騰半天，才能拿到結果。

SlideMaster 透過三步驟完美解決：
1. **寫講稿**：AI 依投影片生成流暢口語講稿。

## active-etf-holdings
---
name: active-etf-holdings
description: 從本地 ETF 清單或指定代號清單抓取並彙總台灣主動型 ETF 持股。當使用者要求更新、抓取、計算、比較或重新產生主動型 ETF 持股張數、持股比例、重疊持股、ETF 持股明細、持股彙總檔案時使用。
---

# 主動型 ETF 持股統計

> [!CAUTION]
> **重要安全性原則：絕不可直接覆蓋 `wiki/金融投資/` 下的檔案！**
> 1. 本功能的核心明細 `主動型ETF持股明細.xlsx` **含有珍貴的歷史多日期分頁（如 20260519、20260520 等）與累計的加減碼歷史比對**。
> 2. 絕不能直接執行無參數腳本來生成全新、無歷史的 XLSX 檔並直接覆蓋，否則將導致所有歷史數據永久遺失。
> 3. 更新時，必須在**知識庫根目錄**執行，且指定 `--output-dir wiki/金融投資`（目前腳本已改寫為在此路徑存在時預設使用此目錄）。如此一來，腳本會自動載入現存的明細檔案，在此基礎上追加當日分頁並完成增量比較。

## 概覽

使用這個 skill 重新產生知識庫中的台灣主動型 ETF 持股統計。內建腳本會抓取 MoneyDJ ETF「全部持股」頁面，將持有股數換算為張數，寫入完整明細 XLSX，產生依加總投資比例排序的 Markdown 彙總表，並比較最近兩個日期分頁的持股變動。

## 快速使用

在知識庫根目錄執行時，優先使用：

## passive-etf-holdings
---
name: passive-etf-holdings
description: 從本地 ETF 清單抓取並彙總台灣被動型（市值型、高股息）ETF 持股。當使用者要求更新、抓取、計算、比較或重新產生被動型 ETF 持股比例、重疊持股、ETF 持股明細、持股彙總檔案時使用。
---

# 被動型 ETF 持股統計

> [!CAUTION]
> **重要安全性原則：絕不可直接覆蓋 `wiki/金融投資/` 下的檔案！**
> 1. 本功能的核心明細 `市值型ETF持股明細.xlsx` 與 `高股息ETF持股明細.xlsx` 含有歷次更新的完整日期分頁與歷史比對資料。
> 2. 絕不能直接執行無參數腳本來生成全新、無歷史的 XLSX 檔並直接覆蓋，否則將導致所有歷史數據永久遺失。
> 3. 更新時，必須在**知識庫根目錄**執行，預設將會自動載入現存的明細檔案，在此基礎上追加當日分頁並完成增量比較。

## 概覽

使用這個 skill 重新產生知識庫中的台灣被動型 ETF 持股統計。內建腳本會抓取 MoneyDJ ETF「全部持股」頁面，將持有股數換算為張數，寫入完整明細 XLSX，產生依加總投資比例排序的 Markdown 彙總表，並比較最近兩個日期分頁的持股變動。

## 快速使用

在知識庫根目錄執行時，使用：

## rdq-skill
---
name: rdq
description: RDQ Method（需求探索四象限法）需求訪談技能，全域可用、實驗性方法。在動工「之前」用四象限（Ⅰ已明說的／Ⅱ想問的／Ⅲ知道卻沒說的／Ⅳ沒想到的）做結構化訪談，產出一頁需求規格卡，經使用者確認後才執行或交棒給執行型技能。當使用者說「用 RDQ」「跑 RDQ」「RDQ 訪談」「幫我釐清需求」「幫我探索需求」「需求訪談」「先訪談我再做」「我還沒想清楚要什麼」「幫我想想還缺什麼」「先問我問題再開始」「做需求規格」時，請一定要使用此技能（語音輸入的同音變體依全域善意還原原則還原後同樣觸發）。當使用者提出全新的中大型任務（新專案、新課程、新研習、新系統）但只給一兩句、缺對象或時間或產出格式時，不要自行開跑訪談，先用一句話問「要不要先跑 RDQ 需求訪談？」，同意才進入；同一對話被婉拒過一次就不再主動提議。以下情況一律不要觸發，直接執行即可：使用者請你解釋、介紹、製作 RDQ 方法論的內容（做 RDQ 的簡報、影片、文章、教材——那是講方法不是跑方法）；使用者已給出完整明確的需求；使用者說「直接做」「不用問」「照上次的做」；小型修改、除錯、單一檔案的小任務；純查詢或知識問答；執行中任務的追加調整；「開工」「收工」「初始化專案」等既有流程；以及其他自帶訪談流程的技能正在進行時。
---

# RDQ Method — 需求探索四象限法

> Requirements Discovery Quadrant Method
> 在執行之前，先把真正的問題找出來。

方法論摘要見 `README.md`。

---

## 核心定位

RDQ 是**所有執行型技能的前置需求層**。它自己不做成品，它產出一張「需求規格卡」，確認後才交棒。

一句話原則：**訪談的成本，必須低於它省下的返工成本。** 任何時候違反這條，就該收手直接做。

## video-autopilot
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

## video-production-workflow
---
name: video-production-workflow
description: 分類短影音需求、選擇剪輯格式、擬定可執行的剪輯策略與 QA 檢查。適用於使用者要先釐清影片類型、平台、長度、字幕風格，或想先產出短影音工作流程再進入剪輯。
---

# 短影音剪輯工作流

這個技能用來先分流、再規劃，最後才進入實作。

## 如何使用

1. 先判斷影片是教學型、活動紀錄型、社群科普型，還是個人日誌型。
2. 再確認平台、長度、受眾、風格與限制。
3. 如果資訊不夠，先問一個最必要的問題。
4. 先產出剪輯策略，再進入實作。
5. 需要剪輯執行時，再把任務交給 `video-autopilot`。

## 使用原則

- 先分類，再設計。

## voxcpm2-voice-cloner

