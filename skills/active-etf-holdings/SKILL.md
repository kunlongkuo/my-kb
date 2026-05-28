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

```powershell
python skills/active-etf-holdings/scripts/collect_active_etf_holdings.py --input-list "wiki/金融投資/主動型ETF清單.md" --output-dir "wiki/金融投資"
```

如果使用者直接提供 ETF 代號，使用：

```powershell
python skills/active-etf-holdings/scripts/collect_active_etf_holdings.py --tickers 00400A,00980A,00981A --output-dir "wiki/金融投資"
```

要計算並產生每週加減碼明細（會修改 XLSX 加入 Weekly Additions 與 Weekly Reductions 分頁）：

```powershell
python skills/active-etf-holdings/scripts/add_weekly_summary.py
```

要彙總每日所有 ETF 對各支個股的總張數，並與前一日比較增減（會修改 XLSX 加入「每日個股合計」分頁）：

```powershell
python skills/active-etf-holdings/scripts/add_daily_stock_total.py
```

## 輸出檔案

腳本會建立或更新下列檔案：

- `主動型ETF持股明細.xlsx`：同一個活頁簿每日新增一個分頁，分頁名稱使用 `YYYYMMDD`。同一天重跑時會覆蓋同名分頁。執行 `add_weekly_summary.py` 後，會自動產生 `Weekly Additions` 與 `Weekly Reductions` 分頁，記錄該週各 ETF 加減碼的詳細持股與張數變化。執行 `add_daily_stock_total.py` 後，會自動產生「每日個股合計」分頁，記錄每日所有 ETF 對各支個股的總張數及與前日的增減比較。
- `主動型ETF持股彙總.md`：包含各 ETF 抓取狀態，以及依「加總投資比例」排序的前 50 名持股。
- `主動型ETF持股變動.md`：比較 XLSX 中最近兩個 `YYYYMMDD` 分頁，逐檔 ETF 列出新增持股、刪除持股與投資比例變動。

XLSX 欄位如下：

`ETF代號`, `ETF名稱`, `資料日期`, `持股代號`, `持股名稱`, `投資比例(%)`, `持有股數`, `持有張數`, `來源`

## 工作流程

1. 讀取使用者指定的 ETF 清單檔或輸出資料夾。若未指定，使用 `wiki/金融投資/主動型ETF清單.md` 與 `wiki/金融投資`。
2. 執行腳本。MoneyDJ 資料每日可能變動，因此通常需要網路連線。
3. 檢查輸出的筆數、XLSX 最新分頁名稱，以及彙總表前幾列，確認沒有明顯解析錯誤。
4. 若 XLSX 至少有兩個日期分頁，查看 `主動型ETF持股變動.md`，回報今日新增股票、刪除股票，以及持股仍在但投資比例變動的股票。
5. 執行 `add_weekly_summary.py` 產生 `Weekly Additions` 與 `Weekly Reductions`。這兩個分頁除了算出加減碼張數外，還會列出「週原比例」、「加/減碼後比例」及「差異」。若持股已全數賣光出清，減碼後比例會自動補 0，以便算出正確的負向差異。
6. 執行 `add_daily_stock_total.py` 產生「每日個股合計」分頁。此分頁以個股為單位，彙整所有 ETF 在每個日期的合計持有張數，並逐日計算增減張數（`張數增減`）與增減比例（`增減比例(%)`）。首日或新出現的個股以淺藍底色標示；張數增加以淺綠、減少以淺橘底色標示。
7. 若 XLSX 少於兩個日期分頁，說明缺少基準日，尚無法判斷新增、刪除與比例變動。
8. 回報沒有資料的 ETF，特別是抓取狀態為 `無日期` 或筆數為 `0` 的標的。
9. 說明「加總比例」是同一持股在不同 ETF 中投資比例的直接加總，適合觀察重疊熱度，不代表全市場加權曝險。

## 資料來源注意事項

- MoneyDJ 全部持股頁面格式為 `Basic0007B.xdjhtm?etfid={ticker}.TW`。
- 台灣主動型 ETF 名單可能變動。若使用者要求最新 ETF 範圍，先查證最新來源，再使用本地清單。
- 債券、期貨等標的的持有股數可能顯示為 `N/A`。保留投資比例，持有股數與持有張數留空。
- 持有張數的換算方式為 `持有股數 / 1000`。
