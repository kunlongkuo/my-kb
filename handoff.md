# Handoff

## 目前做到哪

完成第 78 次（20260914，週一）+ 第 79 次（20260915，週二）主動型 ETF 持股日更：

- **20260914**：抓取 30 檔 ETF 共 **1,735 筆**持股，寫入 `主動型ETF持股明細.xlsx` 的 20260914 分頁，比對 20260911 → 20260914 變動並產生今日排行圖表。
- **20260915**：抓取 30 檔 ETF 共 **1,735 筆**持股，寫入 20260915 分頁。⚠️ MoneyDJ 今晚抓取時多數 ETF 資料日期仍停在 2026/09/14，導致 20260915 與 20260914 持股完全一致，Dashboard 20260915 無排行資料。**明天重跑 `--sheet-date 20260915` 覆蓋即可。**
- 每日個股合計累計 **59,358 列**（共 80 個交易日，20260520～20260915）。
- 更新 `dashboard_data.js`，HTML 日期下拉選單同步至 20260915（562 檔個股與 yfinance 收盤價數據）。

## 目前狀態
- 是否可運行：是
- 做一半的功能：無
- 卡關項目：20260915 分頁待明天覆蓋（MoneyDJ 尚未更新）

## 下一步（優先順序）
1. **明天（20260916 或確認開盤後）**：重跑 `python skills/active-etf-holdings/scripts/collect_active_etf_holdings.py --input-list "wiki/金融投資/主動型ETF清單.md" --output-dir "wiki/金融投資" --sheet-date 20260915` 覆蓋 20260915 分頁，再跑 `add_daily_stock_total.py` 與 `generate_dashboard_data.py`。
2. 繼續每日主動型 ETF 持股日更（下次：20260916，週三）
3. 如有新增或修改設定 / AGENTS.md，執行 `chezmoi re-add` 更新備份

## 最後更新
- 日期時間：2026-09-15 21:50
- 更新者：Antigravity @ DESKTOP-JT9ET4L
- Git push 狀態：本地已更新，待推送
