# 開發進度紀錄 (PROGRESS)

> 本文件記錄專案的重要里程碑與進度，供 AI Agent 交接或團隊成員快速掌握現況。

---

## 2026-06-22 ── 主動型 ETF 資料日更與知識庫目錄結構優化

### ✅ 今日完成

1. **主動型 ETF 持股資料日更 (2026-06-22)**
   - 執行 `collect_active_etf_holdings.py` 抓取並追加今日資料至 `主動型ETF持股明細.xlsx` 中的 `20260622` 分頁（共 29 檔主動型 ETF、1,642 筆持股資料）。
   - 執行 `add_daily_stock_total.py` 累計「每日個股合計」工作表，已累計至 23 個日期分頁，共 17,017 行。
   - 同步更新 `台灣ETF比較清單.xlsx` 的主動型分頁，並透過 `sync_excel_to_md.py` 同步到對應之 Markdown 比較清單檔中。
2. **知識庫目錄結構優化（對齊 Schema）**
   - 將根目錄孤立檔案遷移歸檔：
     - `Webwright_vs_Playwright.md` ➔ `wiki/工具軟體/Webwright_vs_Playwright.md`
     - `＜AI影音工具彙整＞.md` ➔ `wiki/AI工具/＜AI影音工具彙整＞.md`
     - `09-AntiGravity專屬懶人包.md` ➔ `wiki/System/09-AntiGravity專屬懶人包.md`
   - 更新 `index.md` 全域索引，在對應區塊中完成這三個檔案的連結註冊，打通知識結構。
3. **`log.md` 歷史編碼亂碼重建修復**
   - 執行修復腳本對 `log.md` 中 2026-05-03 與 2026-05-05 的亂碼區段進行文字還原與重建，成功回復歷史日誌的可讀性。
4. **自訂技能版控與同步優化**
   - 將原先處於 untracked 的 `skills/video-production-workflow/` 技能目錄正式納入 Git 版控。
   - 建立 `scripts/sync_rules.py` 規則同步腳本，並探測證實根目錄下之四個規則檔（`core_rules.md` 等）已被設定為 NTFS Hard Link，腳本已做例外處理支援自動偵測 Hard Link，提升 Robust 性與 DRY 維護度。
5. **更新 README.md 與 2026-06-22 每日筆記**
   - 於 README 中加入規則檔同步與影片工作流功能，並將已修復之 log 亂碼從已知問題移除；更新每日筆記的待辦事項。

### 📝 改了哪些重要檔案

| 檔案 | 異動類型 | 說明 |
|------|----------|------|
| `wiki/System/09-AntiGravity專屬懶人包.md` | **移動** | 移自根目錄，以保持根目錄清爽 |
| `wiki/AI工具/＜AI影音工具彙整＞.md` | **移動** | 移自根目錄，以符合 Zettelkasten 結構 |
| `wiki/工具軟體/Webwright_vs_Playwright.md` | **移動** | 移自根目錄，以符合 Zettelkasten 結構 |
| `index.md` | **修改** | 新增上述三檔移位檔案之全域索引與內鏈 |
| `log.md` | **修改** | 修復還原了 05-03 及 05-05 的編碼亂碼日誌 |
| `scripts/sync_rules.py` | **新建** | 支援 HardLink 自動偵測與例外處理之規則檔同步工具 |
| `skills/video-production-workflow/` | **新增暫存** | 將整個目錄下的技能檔納入 Git 追蹤 |
| `README.md` | **修改** | 更新目前功能表格，移除 log 亂碼已知問題，更新下一步規劃 |
| `每日筆記/2026-06-22.md` | **新建** | 建立今日開工筆記並標記完成項目 |
| `docs/PROGRESS.md` | **修改** | 記錄今日開發進度（本檔案） |

### 🧭 做了哪些決策

1. **使用 git mv 遷移孤立檔案**：保留 Git 的歷史修改紀錄，並確保路徑在 index.md 中完全映射。
2. **以 Python 腳本對 log.md 做字串重建**：利用已知的文字內容修補損毀的日誌段落，避免手動 replace 亂碼出錯，成功恢復檢索可能性。
3. **HardLink 例外處理與相容性設計**：在 `sync_rules.py` 中利用 Python 的 `st_ino` 來比對 Hard Link 以避免 "same file error"；當未來代碼移至不支援 Link 的環境（如部分雲端平台）時，可回退為 shutil 複製，維持最大相容性。

### 🚧 目前卡在哪裡

- 無。所有任務皆順利完成。

### 👉 下次接手要先看什麼

1. **`每日筆記/2026-06-22.md`**：查閱今日成果與待辦狀態。
2. **`scripts/sync_rules.py`**：了解四個 Hard-linked 規則檔的維護與同步方式。
3. **`skills/video-production-workflow/`**：了解新加入 Git 追蹤的影片製作技能詳情。

---

## 2026-06-19 (追加) ── 安裝四大自訂技能與更新收工規則

### ✅ 今日完成

1. **安裝四大自訂技能 (Custom Skills)**
   - `07-skill-creator` (技能製造機)：提供設計與生成自訂技能的引導。
   - `08-find-skills` (技能搜尋員)：表格化掃描並列出目前已安裝的技能與說明。
   - `09-smart-search` (智慧搜尋)：提供全文檢索與內容定位指南。
   - `10-infographic-builder` (資訊圖表生成)：指引 Mermaid、SVG、Python 與 AI 生圖設計。
2. **註冊全域安裝與更新文檔**
   - 將新技能註冊至 `skills/00-install-all/SKILL.md`。
   - 更新 `09-AntiGravity專屬懶人包.md` 版本至 v1.6，記錄更新歷史。
   - 於 `log.md` 寫入操作日誌。
3. **收工規則重構**
   - 修改並同步了四個核心規則檔 `core_rules.md`、`agents.md`、`claude.md`、`ANTIGRAVITY.md` 以及 `skills/05-workflow/SKILL.md`，將「更新 README.md」、「更新 docs/PROGRESS.md」與「使用具體且詳細的 commit message」等要求寫入「🔴 收工 / 下班了」與「初始化專案」相關規則中。
4. **更新專案 README.md**
   - 在自動化工具列表與目錄結構中補齊四項新技能的詳細描述與路徑。

### 📝 改了哪些重要檔案

| 檔案 | 異動類型 | 說明 |
|------|----------|------|
| `skills/07-skill-creator/SKILL.md` | **新建** | 技能製造機設定檔 |
| `skills/08-find-skills/SKILL.md` | **新建** | 技能搜尋員設定檔 |
| `skills/09-smart-search/SKILL.md` | **新建** | 智慧搜尋設定檔 |
| `skills/10-infographic-builder/SKILL.md` | **新建** | 資訊圖表生成設定檔 |
| `skills/00-install-all/SKILL.md` | **修改** | 新增新安裝的四個技能至清單 |
| `skills/05-workflow/SKILL.md` | **修改** | 將文件更新與具體 commit 規範寫入收工步驟 |
| `core_rules.md` / `agents.md` / `claude.md` / `ANTIGRAVITY.md` | **修改** | 將文件更新與 Git 提交規範納入「🔴 收工 / 下班了」標準 SOP |
| `09-AntiGravity專屬懶人包.md` | **修改** | 升級版本至 v1.6，更新修訂歷史記錄 |
| `README.md` | **修改** | 補齊新自訂技能介紹與目錄結構樹 |
| `log.md` | **修改** | 記錄自訂技能的安裝與懶人包同步日誌 |
| `docs/PROGRESS.md` | **修改** | 記錄本追加進度（本檔案） |

### 🧭 做了哪些決策

1. **同步修改全部規則文件**：為了保持一致，將四個核心規則檔以及 `05-workflow` 技能設定檔中的收工規範同步修改，確保無論 AI 讀取哪一個檔案，都能精確依循新的收工 SOP。
2. **模組化技能編號**：新技能按 `07`、`08`、`09`、`10` 順序進行命名與存放，符合現有專案的命名慣例。

### 🚧 目前卡在哪裡

- 無。已順利完成技能安裝、檔案更新與 SOP 設定。

### 👉 下次接手要先看什麼

1. **`README.md`**：查看四個新自動化工具的用途與目錄結構。
2. **`skills/` 目錄**：可利用新安裝的 `skills/08-find-skills` 技能來快速掃描目前可用的所有技能細節。

---

## 2026-06-19 ── 專案文件整理與版本控管強化

### ✅ 今日完成

1. **全面改寫 `README.md`**
   - 補齊專案用途、目前功能（含知識庫核心 + ETF 追蹤系統 + 自動化工具三大區塊）
   - 新增完整目錄結構說明
   - 新增啟動方式（Python 依賴、各腳本執行指令、Gemini KB App）
   - 新增部署 / 同步方式（Git 工作流、Anti-Gravity 收工自動化、MCP 伺服器設定）
   - 新增環境變數清單（`.env` 各項說明與安全提醒）
   - 新增已知問題清單（5 項）
   - 新增下一步規劃（7 項）
   - 新增 AI 交接須知（依序列出 7 份必讀檔案與關鍵安全規則）

2. **新建 `docs/PROGRESS.md`**（本文件）
   - 建立開發進度紀錄格式，供後續 AI 或人類接手參考

3. **執行 Git commit & push**
   - 安全掃描確認 `.env` 未被追蹤
   - 提交本次所有改動並推送至遠端

### 📝 改了哪些重要檔案

| 檔案 | 異動類型 | 說明 |
|------|----------|------|
| `README.md` | **改寫** | 從 51 行擴充至 ~200 行，補齊所有 GitHub 標準文件要素 |
| `docs/PROGRESS.md` | **新建** | 專案進度紀錄，記錄每次重要改動的決策與影響 |

### 🧭 做了哪些決策

1. **README 架構選擇**：採用「用途 → 功能 → 結構 → 啟動 → 部署 → 環境變數 → 已知問題 → 下一步 → AI 交接」的線性結構，兼顧人類開發者與 AI Agent 閱讀需求。
2. **PROGRESS.md 放置位置**：選擇 `docs/` 目錄而非根目錄，避免根目錄過於擁擠，同時與 GitHub 社群慣例一致。
3. **不修改 `log.md`**：`log.md` 是知識庫專屬的 append-only 操作日誌（依 `schema.md` 規範），與 `PROGRESS.md` 的定位不同——後者聚焦於「專案開發進度」而非「知識庫內容操作」。
4. **已知問題如實記錄**：包含 `log.md` 編碼損毀、YouTube 重複收錄、`__pycache__` 未排除等實際觀察到的問題，不遮掩。

### 🚧 目前卡在哪裡

- 無阻塞性問題。本次為文件整理作業，不涉及功能開發或 bug 修復。

### 👉 下次接手要先看什麼

1. **`README.md`**：了解專案全貌與啟動方式
2. **`每日筆記/` 最新一篇**：了解上次做到哪裡、下一步計畫
3. **`ANTIGRAVITY.md`**：了解 AI Agent 行為規則（特別是 ETF 更新安全規範）
4. **`log.md` 最後幾筆**：了解近期操作紀錄
5. 若要執行 ETF 持股更新，務必先閱讀 `skills/active-etf-holdings/SKILL.md`

---

<!-- 
格式參考：每次重要改動請新增一個日期區段，包含：
- ✅ 今日完成
- 📝 改了哪些重要檔案
- 🧭 做了哪些決策
- 🚧 目前卡在哪裡
- 👉 下次接手要先看什麼
-->
