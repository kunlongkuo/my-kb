# Handoff — 主動型 ETF 知識庫

## 目前做到哪

**第 122 次主動型 ETF 持股日更（20261120，週五）完成**

- `collect_active_etf_holdings.py` — 31 檔 ETF，1,693 筆明細，寫入 `20261120` 分頁，與 `20261119` 比對完成
- `add_weekly_summary.py` — 比對區間 `20261113` → `20261120`，週加碼 318 筆、週減碼 198 筆
- `add_daily_stock_total.py` — 每日個股合計 24,166 列，圖表（`20261120_additions.png`、`20261120_reductions.png`、`active_etf_top_additions.png`、`active_etf_top_reductions.png`）已生成並更新 Markdown
- `generate_dashboard_data.py` — `dashboard_data.js` 更新完成（430 檔股票）
- 每日筆記 `每日筆記/2026-11-20.md` 已建立
- `docs/PROGRESS.md` 已更新

## 目前狀態

✅ 所有指令執行完畢，全部功能正常可運行。

- XLSX 歷史分頁：33 個（`20261001`～`20261120`），保留完整。
- Dashboard 資料正常更新。
- 安全掃描：`skills/video-use/.env` 有 ElevenLabs API Key，已確認在 `.gitignore` 排除，不會 push 到遠端。

## 下一步

1. **2026-11-23（週一）**：執行第 123 次主動型 ETF 日更
   ```powershell
   python skills/active-etf-holdings/scripts/collect_active_etf_holdings.py --output-dir wiki/金融投資
   python skills/active-etf-holdings/scripts/add_weekly_summary.py --excel wiki/金融投資/主動型ETF持股明細.xlsx
   python skills/active-etf-holdings/scripts/add_daily_stock_total.py --xlsx wiki/金融投資/主動型ETF持股明細.xlsx
   python skills/active-etf-holdings/scripts/generate_dashboard_data.py
   ```
2. 追蹤 **00982A 群益台灣強棒**：換股動作劇烈，賣出光寶科、環球晶、聯電、中美晶等 11 檔，觀察下週是否持續調整。
3. 追蹤 **聯電（2303）**：加碼 1,554 張 vs 減碼 8,236 張，整體淨減碼逾 6,600 張。

## 最後更新

- **日期時間**：2026-11-20（週五）
- **更新者**：Antigravity @ DESKTOP-GIM4VFP
- **Git push 狀態**：已推送
