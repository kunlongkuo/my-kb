# Handoff

## 目前做到哪

1. **主動型 ETF 日更 (2026-09-21)**：
   - 完成 31 檔主動型 ETF 共 1,801 筆持股爬取，寫入 `主動型ETF持股明細.xlsx` 的 `20260921` 工作表。
   - 更新「每日個股合計」統計、Top 10 加減碼變動圖表與 `主動型ETF持股變動.md`。
   - 重新生成 `dashboard_data.js`，Web 儀表板下拉選單同步至 2026-09-21。
2. **台灣ETF比較清單.xlsx 連結修復**：
   - 修正 `collect_active_etf_holdings.py` 腳本中的 `update_comparison_xlsx` 函式，自動添加 MoneyDJ 證券代號超連結與藍色底線樣式。
   - 重新生成並補齊 `台灣ETF比較清單.xlsx`「主動型」分頁全部 31 檔標的之超連結與樣式。

## 目前狀態
- 是否可運行：是
- 做一半的功能：無
- 卡關項目：無

## 下一步（優先順序）
1. 繼續每日主動型 ETF 持股日更（下次：20260922，週二）
2. 如有新增或修改設定 / AGENTS.md，執行 `chezmoi re-add` 更新備份

## 最後更新
- 日期時間：2026-09-21 20:12
- 更新者：Antigravity @ DESKTOP-JT9ET4L
- Git push 狀態：已推送
