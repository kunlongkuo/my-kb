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
| 主動型 ETF 日更 | 29 檔主動型 ETF 持股明細，每日自動爬取、追加分頁並增量比對 |
| 被動型 ETF 更新 | 市值型 (20 檔) 與高股息 (21 檔) ETF 持股追蹤 |
| 歷史差異比對 | 自動生成新增個股、刪除個股、加碼張數、減碼張數四大分頁 |
| 每日個股合計 | 彙整所有 ETF 對各個股的總張數，逐日比較增減 |
| 每週加減碼摘要 | Weekly Additions / Weekly Reductions 分頁 |
| ETF 比較清單同步 | Markdown ↔ Excel 雙向同步（`sync_excel_to_md.py`） |

### 自動化工具
| 功能 | 說明 |
|------|------|
| YouTube 影片摘要 | `youtube_to_notes.py` 自動擷取影片逐字稿並生成結構化筆記 |
| Chrome 擴充套件 | 瀏覽器一鍵剪輯工具，將網頁內容匯入知識庫 |
| Gemini KB App | 前後端分離的知識庫查詢應用 |
| Anti-Gravity 工作流 | 「開工 / 收工 / 初始化專案」AI 自動化 SOP |

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
│   ├── collect_passive_etf_holdings.py  # 被動型 ETF 持股爬取
│   ├── sync_excel_to_md.py  # Excel ↔ Markdown 同步
│   └── ...
├── skills/                  # AI Agent 技能包
│   ├── active-etf-holdings/ # 主動型 ETF 持股追蹤技能
│   ├── 00-install-all/      # 環境安裝
│   ├── 01-notebooklm/       # NotebookLM 整合
│   ├── 02-github/           # GitHub 操作
│   ├── 03-firebase/         # Firebase 整合
│   ├── 04-draw/             # 繪圖工具
│   ├── 05-workflow/         # 工作流管理
│   └── 06-obsidian/         # Obsidian 連接
├── chrome_extension/        # Chrome 瀏覽器擴充套件
├── gemini-kb-app/           # Gemini 知識庫查詢應用
│   ├── backend/             # 後端 API
│   └── frontend/            # 前端 UI
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
```

### 執行 ETF 持股更新（被動型）

```powershell
python scripts/collect_passive_etf_holdings.py
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
2. `git add .` → 自動生成 commit 訊息 → `git commit` → `git push`
3. 更新每日筆記的「已完成工作」與「待辦事項」

### MCP 伺服器（OpenCode 整合）

`opencode.json` 設定了兩組 MCP 伺服器：
- **notebooklm**：透過 `nlm mcp` 進行大文件快速檢索
- **firebase**：預留未來資料庫同步使用

---

## ⚠️ 已知問題

1. **`log.md` 中段編碼損毀**（約 131-236 行）：部分早期（2026-05 初）的日誌內容出現二進位亂碼（null bytes / BOM 殘留），疑似 Excel 寫入時的編碼衝突。已不影響後續 append，但歷史紀錄可讀性受損。
2. **YouTube 摘要重複收錄**：`log.md` 中記錄顯示「第一集｜探索 Obsidian」影片被重複 ingest 了 5 次（2026-04-27），疑似腳本冪等性不足。
3. **`raw/` 與 `bin/` 被 .gitignore 排除**：這些目錄的內容不在版本控管中。若需遷移至新機器，需手動複製或重新取得。
4. **被動型 ETF 腳本路徑**：`collect_passive_etf_holdings.py` 目前放在 `scripts/` 而非 `skills/` 架構下，與主動型 ETF 的 skill 架構不一致。
5. **`skills/active-etf-holdings/scripts/__pycache__/`**：Python 快取目錄未被 .gitignore 排除（技能子目錄下），可能被意外提交。

---

## 🔮 下一步規劃

- [ ] 將被動型 ETF 持股追蹤遷移至 `skills/` 架構，與主動型一致
- [ ] 修復 `log.md` 中段的編碼損毀區段
- [ ] 為 YouTube 摘要腳本加入冪等性檢查（避免重複收錄）
- [ ] 考慮將 `.gitignore` 加入 `__pycache__/` 的全域排除規則（目前僅排除根目錄）
- [ ] 完善 `gemini-kb-app` 的文件與啟動說明
- [ ] 建立 ETF 持股追蹤的自動排程（Windows Task Scheduler / Cron）
- [ ] 評估 Firebase 同步功能的啟用時機

---

## 🤖 AI 交接須知

若你是接手此專案的 AI Agent，請先閱讀以下檔案：

1. **[ANTIGRAVITY.md](ANTIGRAVITY.md)**：AI Agent 行為規則與開工/收工 SOP
2. **[schema.md](schema.md)**：知識庫操作規範（Ingest / Query / Lint 流程）
3. **[index.md](index.md)**：全域知識節點索引
4. **[log.md](log.md)**：操作日誌（了解近期做了什麼）
5. **[每日筆記/](每日筆記/)**：最新一篇可了解「上次做到哪」與「下一步計畫」
6. **[skills/active-etf-holdings/SKILL.md](skills/active-etf-holdings/SKILL.md)**：ETF 持股追蹤的完整操作指南
7. **[docs/PROGRESS.md](docs/PROGRESS.md)**：開發進度紀錄

> ⚠️ **關鍵安全規則**：**絕不可**直接覆蓋 `wiki/金融投資/` 下的 `.xlsx` 檔案。詳見 [ANTIGRAVITY.md](ANTIGRAVITY.md) 中的「主動型 ETF 更新安全規範」。

---

*Formulated and maintained with ❤️ via Anti-Gravity.*
