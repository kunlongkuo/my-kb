# Handoff — 主動型 ETF 知識庫

## 目前做到哪

**第 121 次主動型 ETF 持股日更（20261119，週四）完成**

- `collect_active_etf_holdings.py` — 31 檔 ETF，1,700 筆明細，寫入 `20261119` 分頁，與 `20261118` 比對完成
- `add_weekly_summary.py` — 比對區間 `20261113` → `20261119`，週加碼 292 筆、週減碼 180 筆
- `add_daily_stock_total.py` — 每日個股合計 23,465 列，圖表（`20261119_additions.png`、`20261119_reductions.png`、`active_etf_top_additions.png`、`active_etf_top_reductions.png`）已生成並更新 Markdown
- `generate_dashboard_data.py` — `dashboard_data.js` 更新完成（430 檔股票）
- 每日筆記 `每日筆記/2026-11-19.md` 已建立
- `docs/PROGRESS.md` 已更新

## 目前狀態

✅ 所有指令執行完畢，全部功能正常可運行。

- XLSX 歷史分頁：32 個（`20261001`～`20261119`），保留完整。
- Dashboard 資料正常更新。
- 安全掃描：`skills/video-use/.env` 有 ElevenLabs API Key，已確認在 `.gitignore` 排除，不會 push 到遠端。

## 下一步

1. **2026-11-20（週五）**：執行第 122 次主動型 ETF 日更
   ```powershell
   python skills/active-etf-holdings/scripts/collect_active_etf_holdings.py --output-dir wiki/金融投資
   python skills/active-etf-holdings/scripts/add_weekly_summary.py --excel wiki/金融投資/主動型ETF持股明細.xlsx
   python skills/active-etf-holdings/scripts/add_daily_stock_total.py --xlsx wiki/金融投資/主動型ETF持股明細.xlsx
   python skills/active-etf-holdings/scripts/generate_dashboard_data.py
   ```
2. 追蹤 **增你強（3028）**：連續兩日大加碼（11/18 +3,000 張、11/19 +3,072 張），關注是否延續。
3. 追蹤 **00408A 第一金優股息**：大幅換股（刪除緯穎、南亞科、國巨*），注意持倉方向轉變。

## 最後更新

- **日期時間**：2026-11-19（週四）
- **更新者**：Antigravity @ DESKTOP-GIM4VFP
- **Git push 狀態**：已推送
