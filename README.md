# Mark's Personal Knowledge Base (my-kb) 🧠✨

> 一座基於 Obsidian 的個人第二大腦，結合 LLM Wiki 架構與 AI Agent 自動化工作流，持續累積台灣法規、金融投資、烘焙食譜與 AI 工具等領域知識。

---

## 📌 專案用途

本倉庫是一個**個人知識管理系統 (PKM)**，採用 [LLM Wiki](wiki/System/llm-wiki.md) 架構搭配 Obsidian 作為前端，主要目標：

1. **知識收錄與結構化**：將散落的法規、投資數據、食譜、AI 工具教學等原始資料，經「原始歸檔 → 暫存卡片 → 永久 Wiki」三階段流程系統性整理。
2. **ETF 持股自動化追蹤**：每日自動爬取台灣主動型 / 被動型 ETF 持股明細（來源：MoneyDJ），累積歷史分頁並進行增量比對（新增、刪除、加碼、減碼）。
3. **AI Agent 協作**：透過 Anti-Gravity / OpenCode 等 AI Copilot 框架，實現「開工→收工」自動化工作流、YouTube 影片摘要自動收錄等功能。
4. **版本控管與知識交接**：所有知識節點皆以 Git 追蹤，確保可追溯性與 AI 交接能力。

---

## 🚀 目前功能

### 知識庫核心
| 功能 | 說明 |
|------|------|
| Wiki 知識節點 | 8 大分類、50+ 篇結構化知識頁面（交通法規、勞工法規、金融投資、烘焙食譜、AI 工具等） |
| 卡片盒筆記法 | `raw/` → `cards/` → `wiki/` 三階段知識萃取流程，符合 Zettelkasten 架構 |
| 全域索引 | `index.md` 供 LLM 快速定位相關知識節點 |
| 操作日誌 | `log.md` 記錄所有知識庫操作的 append-only 時間序列 |

### ETF 持股追蹤系統
| 功能 | 說明 |
|------|------|
| 主動型 ETF 日更 | 31 檔主動型 ETF 持股明細，每日自動爬取、追加分頁並增量比對 |
| 被動型 ETF 更新 | 市值型 (20 檔) 與高股息 (21 檔) ETF 持股追蹤 |
| 歷史差異比對 | 自動生成新增個股、刪除個股、加碼張數、減碼張數四大分頁 |
| 每日個股合計 | 彙整所有 ETF 對各個股的總張數，逐日比較增減 |
| 每週加減碼摘要 | Weekly Additions / Weekly Reductions 分頁 |
| ETF 比較清單同步 | Markdown ↔ Excel 雙向同步（`sync_excel_to_md.py`） |
| 個股加減碼分析儀表板 | 包含個股歷史趨勢（`主動型ETF持股分析.html`）與每日加減碼排行（`主動型ETF個股加減碼排行.html`），支援搜尋、Chart.js 圖表與投信明細鑽取 |



### 自動化工具
| 功能 | 說明 |
|------|------|
| YouTube 影片摘要 | `youtube_to_notes.py` 自動擷取影片逐字稿並生成結構化筆記 |
| Chrome 擴充套件 | 瀏覽器一鍵剪輯工具，將網頁內容匯入知識庫 |
| Gemini KB App | 前後端分離的知識庫查詢應用 |
| 多檔案 RAG 查詢 | `.opencode/skills/skill-rag` 將文字文件切成 chunks，建立本機 JSON 索引並可匯出 MySQL SQL |
| Anti-Gravity 工作流 | 「開工 / 收工 / 初始化專案」AI 自動化 SOP（整合 `handoff.md` 跨電腦交接） |
| 規則檔自動同步 | `sync_rules.py` 支援 OS 硬連結 (Hard Link) 偵測之規則同步工具 |
| 影片製作工作流 | `skills/video-production-workflow` 規範活動紀錄、教學與科普影片前期策略與分鏡 SOP |
| 影片自動執行 | `skills/video-autopilot` 整合 Editkin v4 唯一剪輯合約、機械閘門與 CapCut/ffmpeg 落地 |
| AI 語音精剪 | `skills/video-use` 對話驅動之 AI 自動逐字稿與口播贅詞/死空間精剪 |
| 原理解說動畫 | `skills/motion-explainer` 系列（HyperFrames 動畫、授權照片證據卡、H3 AI 影片、品味規範與審查） |
| AI 短劇編劇 | `skills/shanshiba-drama` 預設 9:16 直式 Shorts / 指定 16:9 橫式 MiniMax H3 短劇創作、試映讀本、drama-hooks 與單鏡 ≤12 秒拆鏡契約 |
| 3D 空間預演 | `skills/blender-previs` Blender 白模鎖定機位、空間防漂移、布置圖檢查與運鏡交付包 |
| 社群平台貼文 | `skills/social-post` 社群內容規劃、依授權樣本校準語氣、平台化撰稿與審慎成效檢視 |
| 技能製造機 | `skills/07-skill-creator` 輔助引導自訂技能設計與生成 |
| 技能搜尋員 | `skills/08-find-skills` 列出與說明已安裝的技能 |
| 智慧搜尋 | `skills/09-smart-search` 提供多維度全文檢索與內容定位指南 |
| 資訊圖表生成 | `skills/10-infographic-builder` 輔助 Mermaid、SVG 與生圖設計 |
| SlideMaster 簡報影片化 | `skills/12-slidemaster` 透過寫講稿、配語音、合成影片三步驟，將簡報轉為影片 |

### 共用 Agent 技能包
| 功能 | 說明 |
|------|------|
| 共用技能來源 | `skills/` 為單一來源，內容更新以這裡為準 |
| OpenCode 鏡像 | `.opencode/skills/` 提供 OpenCode 直接讀取與授權調用 |
| 其他 Agent 鏡像 | `.agents/skills/` 提供 AntiGravity 與其他 Agent 共用 |
| 技能同步說明 | [`docs/AGENT_SHARED_SKILLS.md`](docs/AGENT_SHARED_SKILLS.md) 說明目前同步狀態與使用順序 |

> 影片與動畫製作技能體系包含：`video-production-workflow`（前期策略）、`video-autopilot`（Editkin v4 剪輯合約與落地）、`video-use-editor`（AI 語音逐字稿精剪）、`motion-explainer` 系列（HyperFrames 原理解說動畫與 AI 影片）、`shanshiba-drama`（AI 短劇編劇）與 `blender-previs`（Blender 空間預演），皆已全數同步至 OpenCode 與 `.agents` 鏡像區。

社群文案由 `skills/social-post` 負責；規劃、撰稿及成效分析不代表已連接社群帳號或可自動發布。

---

## 📂 目錄結構

```
my-kb/
├── wiki/                    # 永久知識節點（按主題分類）
│   ├── 交通法規/            # 台灣交通相關法規
│   ├── 勞工法規/            # 勞動相關法規
│   ├── 金融投資/            # ETF 清單、持股明細、比較表
│   ├── 烘培食譜/            # 丙級烘焙食譜
│   ├── AI工具/              # LLM Wiki、ChatGPT 工具教學
│   ├── 工具軟體/            # Jason Tools 等
│   ├── youtube-notes/       # YouTube 影片自動摘要
│   └── System/              # Wiki 系統指南
├── raw/                     # 不可變更的原始資料（.gitignore 排除）
├── cards/                   # 暫時筆記 / Zettelkasten 卡片
├── scripts/                 # 自動化腳本
│   ├── youtube_to_notes.py  # YouTube 影片 → Obsidian 筆記
│   ├── sync_excel_to_md.py  # Excel ↔ Markdown 同步
│   └── ...
├── skills/                  # AI Agent 技能包
│   ├── active-etf-holdings/ # 主動型 ETF 持股追蹤技能
│   ├── passive-etf-holdings/# 被動型 ETF 持股追蹤技能
│   ├── 00-install-all/      # 環境安裝
│   ├── 01-notebooklm/       # NotebookLM 整合
│   ├── 02-github/           # GitHub 操作
│   ├── 03-firebase/         # Firebase 整合
│   ├── 04-draw/             # 繪圖工具
│   ├── 05-workflow/         # 工作流管理
│   ├── 06-obsidian/         # Obsidian 連接
│   ├── 07-skill-creator/    # 技能製造機
│   ├── 08-find-skills/      # 技能搜尋員
│   ├── 09-smart-search/     # 智慧搜尋
│   ├── 10-infographic-builder/ # 資訊圖表生成
│   └── 12-slidemaster/      # SlideMaster 簡報影片化技能
├── chrome_extension/        # Chrome 瀏覽器擴充套件
├── gemini-kb-app/           # Gemini 知識庫查詢應用
│   ├── backend/             # 後端 API
│   └── frontend/            # 前端 UI
├── rag-data/                # RAG 文件來源（待查文字檔放在 sources/）
│   └── sources/
├── templates/               # Obsidian 頁面模板
├── 每日筆記/                # 每日工作紀錄（開工/收工日誌）
├── Clippings/               # 網頁剪輯暫存（待收錄）
├── bin/                     # 二進位工具（ffmpeg 等，.gitignore 排除）
├── scratch/                 # 暫存檔案（.gitignore 排除）
│
├── index.md                 # 全域知識節點索引
├── schema.md                # 知識庫操作規範與結構定義
├── log.md                   # 操作日誌（append-only）
├── ANTIGRAVITY.md           # AI Agent 行為規則與 SOP
├── opencode.json            # OpenCode MCP 伺服器設定
├── .env                     # 環境變數（已加入 .gitignore）
└── .gitignore               # Git 排除規則
```

---

## 🔎 多檔案文件查詢（RAG）快速入門

### 文字檔放置位置

把要查詢的文件放在知識庫根目錄的 `rag-data/sources/`，例如：

```text
rag-data/
└── sources/
    ├── 操作手冊.md
    ├── 常見問題.txt
    └── 商品資料.docx
```

支援 `.md`、`.markdown`、`.txt`、`.json`、`.yaml`、`.yml`、`.sql`、`.docx` 及 `.pdf`。PDF 必須有可選取的文字；影像掃描 PDF 要先 OCR。來源文字可能含私人資訊，請確認適合存放及納入索引。

### 設定與建立索引

首次使用前，安裝 RAG 工具依賴；若私有設定檔尚不存在，再複製範本（此寫法會保留已存在的設定檔）：

```powershell
python -m pip install -r .opencode\skills\skill-rag\requirements.txt
$setup = ".opencode\skills\skill-rag\setup.json"
if (-not (Test-Path -LiteralPath $setup)) {
    Copy-Item -LiteralPath .opencode\skills\skill-rag\templates\setup.example.json -Destination $setup
}
```

編輯 `.opencode/skills/skill-rag/setup.json`，填入 MySQL 設定及 API key。此私有檔已排除於 Git；雖然目前腳本要求 API key 欄位存在，但索引及查詢流程不會呼叫 OpenAI 或產生 embedding。

在知識庫根目錄執行以下命令建立索引：

```powershell
$skill = ".opencode\skills\skill-rag"
python "$skill\scripts\skill_rag.py" --setup "$skill\setup.json" scan --root ".\rag-data" --output "$skill\build\index.json" --sql-output "$skill\build\index.sql"
```

輸出檔案：

- `.opencode/skills/skill-rag/build/index.json`：供本機查詢使用的索引。
- `.opencode/skills/skill-rag/build/index.sql`：可匯入 MySQL 的資料 SQL；產生此檔不代表已寫入資料庫。

### 查詢文件

建立索引後，使用命令列查詢：

```powershell
$skill = ".opencode\skills\skill-rag"
python "$skill\scripts\skill_rag.py" query --index "$skill\build\index.json" --question "如何重設設備？" --top-k 5
```

也可以在 OpenCode 對話中要求「用 `skill-rag` 查詢 `rag-data/sources/` 裡的文件，回答時附上來源檔名」。查詢會回報匹配文件與 chunk。排序依關鍵詞重疊及標題加權，不是語意向量搜尋。

### 建立 MySQL 資料表並匯入索引

MySQL 資料表是可選的。`skill-rag` 的一般查詢讀取 `index.json`，不會連線 MySQL。若要另外保存索引資料，第一次需用 MySQL Workbench 執行 `.opencode/skills/skill-rag/templates/sql-schema.sql`，建立 `mydb`、`rag_sources`、`rag_chunks` 及全文索引；再用 `mysql` 命令列工具匯入 `index.sql`：

```cmd
mysql -h 127.0.0.1 -P 3306 -u user1 -p < .opencode\skills\skill-rag\templates\sql-schema.sql
mysql -h 127.0.0.1 -P 3306 -u user1 -p mydb < .opencode\skills\skill-rag\build\index.sql
```

將 `user1` 換成有權限的 MySQL 帳號；`-p` 會提示輸入密碼。以上命令請在 **cmd.exe** 執行，或改用 MySQL Workbench。schema 範本只建立不存在的資料表，不會清除資料；匯入前仍須確認連線目標。後續掃描會重建 JSON 並產生可更新既有資料列的 SQL，但不會自動清除已刪除來源留下的舊資料列。

如需直接檢查 MySQL 中的資料，可使用 `skill-db`：

```powershell
python .opencode\skills\skill-db\scripts\mysql_skill.py schema
python .opencode\skills\skill-db\scripts\mysql_skill.py run --sql "SELECT COUNT(*) AS chunk_count FROM rag_chunks"
```

若資料已匯入且已建立範本中的 FULLTEXT 索引，可直接做 MySQL 全文檢索：

```powershell
python .opencode\skills\skill-db\scripts\mysql_skill.py run --sql "SELECT s.source_name, c.chunk_index, c.chunk_content FROM rag_chunks AS c JOIN rag_sources AS s ON s.id = c.source_id WHERE MATCH(c.chunk_title, c.summary, c.keywords, c.tags, c.content, c.chunk_content) AGAINST ('搜尋關鍵字' IN NATURAL LANGUAGE MODE) ORDER BY c.chunk_index LIMIT 5"
```

這個 SQL 查詢使用 MySQL 的 FULLTEXT 索引，與 `skill-rag query` 讀取 JSON 索引是兩條不同的查詢路徑；結果會受 MySQL 版本及文字切詞方式影響。

完整設定、更新步驟與限制請參閱 [skill-rag 使用說明](.opencode/skills/skill-rag/README.md)。

---

## ⚡ 啟動方式

### 前置需求

- **Python 3.11+**（ETF 爬取腳本、YouTube 摘要等）
- **Obsidian**（作為知識庫前端瀏覽器）
- **Git**（版本控管）
- **Node.js / npm**（Gemini KB App、MCP 伺服器等）
- **ffmpeg**（影片處理，已放於 `bin/`）

### 開啟 Obsidian Vault

直接在 Obsidian 中開啟 `I:\Mark\my-kb` 作為 Vault 即可。

### 安裝 Python 依賴

```bash
pip install requests beautifulsoup4 openpyxl google-generativeai
```

### 執行 ETF 持股日更（主動型）

```powershell
# 在知識庫根目錄執行
python skills/active-etf-holdings/scripts/collect_active_etf_holdings.py --input-list "wiki/金融投資/主動型ETF清單.md" --output-dir "wiki/金融投資"

# 每日個股合計
python skills/active-etf-holdings/scripts/add_daily_stock_total.py

# 每週加減碼摘要（通常週五執行）
python skills/active-etf-holdings/scripts/add_weekly_summary.py

# 產生個股持股分析儀表板數據 (產出 wiki/金融投資/dashboard_data.js)
python skills/active-etf-holdings/scripts/generate_dashboard_data.py
# 接著可直接於瀏覽器開啟以下檔案：
# - 個股歷史趨勢：wiki/金融投資/主動型ETF持股分析.html
# - 每日加減碼排行：wiki/金融投資/主動型ETF個股加減碼排行.html
```

### 個股加減碼分析儀表板的手機存取與部署方式

本專案儀表板支援完全的手機 RWD 響應式介面，可透過以下兩種方式在手機上執行與檢視：

#### 方案 A：使用本機區域網路伺服器 (即時本機測試)
1. 確保手機與電腦連接在**同一個 Wi-Fi 網路**下。
2. 在知識庫根目錄執行以下腳本啟動 Web 服務：
   ```powershell
   python scripts/start_mobile_server.py
   ```
3. 程式會自動偵測電腦 IP 並在電腦端**打開一個 QR Code 網頁**，直接用手機相機掃描 QR Code 即可連線開啟。

#### 方案 B：啟用 GitHub Pages 雲端託管 (終極推薦)
1. 進入此 GitHub 倉庫的 `Settings` -> `Pages` 設定。
2. 將 Build and deployment 中的 Branch 設為 `main`，路徑設為 `/ (root)`，點擊 Save。
3. 檔案 Push 至 GitHub 後，即可透過以下公開 URL 直接開啟：
   - **個股歷史趨勢**：`https://kunlongkuo-cloud.github.io/my-kb/wiki/金融投資/主動型ETF持股分析.html`
   - **個股加減碼排行**：`https://kunlongkuo-cloud.github.io/my-kb/wiki/金融投資/主動型ETF個股加減碼排行.html`


### 執行 ETF 持股更新（被動型）

```powershell
python skills/passive-etf-holdings/scripts/collect_passive_etf_holdings.py
```

### 執行 Excel ↔ Markdown 同步

```powershell
python scripts/sync_excel_to_md.py
```

### 執行 YouTube 影片摘要

```powershell
python scripts/youtube_to_notes.py <YouTube-URL>
```

### 啟動 Gemini KB App

```powershell
gemini-kb-app\run_app.bat
```

---

## 🔐 環境變數

所有敏感資訊存放於 `.env`（已被 `.gitignore` 排除，不會進入版本控管）：

| 變數名 | 用途 | 備註 |
|--------|------|------|
| `GEMINI_API_KEY` | Google Gemini API 金鑰 | YouTube 摘要、知識庫查詢 |
| `GEMINI_MODEL` | Gemini 模型版本 | 目前使用 `gemini-3-flash-preview` |
| `OPENAI_API_KEY` | OpenAI / NVIDIA API 金鑰 | 備用模型 |
| `WIKI_PATH` | Wiki 筆記輸出路徑 | 預設 `wiki/youtube-notes` |
| `RAW_PATH` | 原始逐字稿存放路徑 | 預設 `raw/transcripts` |
| `LOG_FILE` | 操作日誌路徑 | 預設 `log.md` |
| `INDEX_FILE` | 全域索引路徑 | 預設 `index.md` |

> ⚠️ **安全提醒**：請勿將 `.env` 提交至版本控管。複製本專案時需自行建立 `.env` 並填入對應金鑰。

---

## 🚢 部署 / 同步方式

本專案為**本地優先**的 Obsidian Vault，主要透過 Git 進行版本控管與備份：

```powershell
# 日常同步（收工流程會自動執行）
git add .
git commit -m "feat: 描述本次改動"
git push origin main
```

### Anti-Gravity 自動化收工流程

在 AI 對話中說「**收工**」會自動觸發：
1. 敏感檔案安全掃描（防止 API Key 外洩）
2. 更新並全新覆寫根目錄的 `handoff.md`（記錄當前進度、狀態、下一步、最後更新時間與電腦名稱，供跨端無縫交接）
3. `git add .` → 自動生成包含 handoff 摘要之 commit 訊息 → `git commit` → `git push`
4. 更新每日筆記的「已完成工作」與「待辦事項」

### MCP 伺服器（OpenCode 整合）

`opencode.json` 設定了兩組 MCP 伺服器：
- **notebooklm**：透過 `nlm mcp` 進行大文件快速檢索
- **firebase**：預留未來資料庫同步使用

---

## ⚠️ 已知問題

1. **YouTube 摘要重複收錄**：`log.md` 中記錄顯示「第一集｜探索 Obsidian」影片被重複 ingest 了 5 次（2026-04-27），疑似腳本冪等性不足。
2. **`raw/` 與 `bin/` 被 .gitignore 排除**：這些目錄的內容不在版本控管中。若需遷移至新機器，需手動複製或重新取得。
3. **`skills/active-etf-holdings/scripts/__pycache__/`**：Python 快取目錄未被 .gitignore 排除（技能子目錄下），可能被意外提交。

---

## 🔮 下一步規劃

- [x] 將被動型 ETF 持股追蹤遷移至 `skills/` 架構，與主動型一致
- [ ] 為 YouTube 摘要腳本加入冪等性檢查（避免重複收錄）
- [ ] 考慮將 `.gitignore` 加入 `__pycache__/` 的全域排除規則（目前僅排除根目錄）
- [ ] 將新增的影片製作工作流技能 `skills/video-production-workflow` 註冊至全域一鍵安裝技能
- [ ] 完善 `gemini-kb-app` 的文件與啟動說明
- [ ] 建立 ETF 持股追蹤的自動排程（Windows Task Scheduler / Cron）
- [ ] 評估 Firebase 同步功能的啟用時機

---

## 🤖 AI 交接須知

若你是接手此專案的 AI Agent，請務必先閱讀以下檔案：

1. **[handoff.md](handoff.md)**：L1 級別之跨電腦/跨 Agent 接續交接記錄（首要必讀）
2. **[ANTIGRAVITY.md](ANTIGRAVITY.md)**：AI Agent 行為規則與開工/收工 SOP
3. **[schema.md](schema.md)**：知識庫操作規範（Ingest / Query / Lint 流程）
4. **[index.md](index.md)**：全域知識節點索引
5. **[log.md](log.md)**：操作日誌（了解近期做了什麼）
6. **[每日筆記/](每日筆記/)**：最新一篇可了解「上次做到哪」與「下一步計畫」
7. **[skills/active-etf-holdings/SKILL.md](skills/active-etf-holdings/SKILL.md)**：ETF 持股追蹤的完整操作指南
8. **[docs/PROGRESS.md](docs/PROGRESS.md)**：開發進度紀錄

> ⚠️ **關鍵安全規則**：**絕不可**直接覆蓋 `wiki/金融投資/` 下的 `.xlsx` 檔案。詳見 [ANTIGRAVITY.md](ANTIGRAVITY.md) 中的「主動型 ETF 更新安全規範」。

---

*Formulated and maintained with ❤️ via Anti-Gravity.*
