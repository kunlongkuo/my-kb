# Handoff — 主動型 ETF 知識庫

## 目前做到哪

**1. 完成首支 VOX 科普短影音《堆高機的運作原理》成片輸出 🚜🎬**
- **專案路徑**：`skills/script2film/projects/forklift/`
- **成片位置**：`projects/forklift/cut_lecture-tech/output.mp4`（7.34 MB，42.40 秒，1080p，-14.0 LUFS）
- **字幕檔案**：`projects/forklift/cut_lecture-tech/subtitles_zh.srt`
- **完整流水線走通**：
  - F1 結構化劇本文檔（5 拍分鏡表）
  - F2 旁白語音合成（Edge-TTS `zh-TW-YunJheNeural` 台灣男聲）
  - F3 逐字對時對齊（`doc_align.py` worst match 1.00）
  - F4 程式動態場景渲染（5 個場景：雙欄對比、槓桿公式、穩定性三角形、側翻誘因、力量拆解）
  - F5 自動剪輯與外殼字幕渲染（`doc_cut.py`）
  - F6 嚴格機器自檢（`check.py`：0 黑格、影音誤差 0.000s、-14.0 LUFS、-2.4 dBTP）

**2. 解決字卡重疊問題與優化佈局引擎**
- 修訂 `skills/ve-director/doc/scenes/breakdown.js`：加入自適應防重疊推開演算（確保 $\ge 40\text{ px}$ 垂直安全間距）、調適字級與中心座標。
- 修訂 `projects/forklift/doc.json` B5 文案：精煉為「搬運物理系統」、「槓桿力矩平衡」、「帕斯卡液壓倍增」，徹底杜絕折行遮擋。
- 18 項 pytest 單元測試 100% 綠燈通過。

**3. Windows 平台相容性全域加固**
- `doc_common.py`：自動將 `python3` 映射至當前環境之 `sys.executable`。
- `doc_cut.py`：Windows symlink 權限不足時自動 fallback 至 `shutil.copy2`。
- `plan2concat_mcp.py`：`loudnorm` 替換檔案加入 Windows 檔案鎖定重試與複製替換機制（免除 WinError 5）。
- 新增本機 Edge-TTS 輕量合成工具（`tools/tts/edge_pipeline.py`、`tools/tts/make_words_json.py`）。

## 目前狀態

✅ **全系統正常運作，短影音成果已就緒，無卡關。**
- 成片可直接點擊播放：`skills/script2film/projects/forklift/cut_lecture-tech/output.mp4`。
- 乾淨工作區，所有暫存檔已清理，敏感資訊掃描無洩漏。

## 下一步

1. **短影音後續應用（可選）**：
   - 如需將堆高機短影音發布至社群（YouTube / FB / IG / Threads），可手動掛載繁中字幕 `subtitles_zh.srt`。
   - 可根據需要更換旁白音色或嘗試其他主題配色（如 `collage`, `live`）。
2. **2026-11-23（週一）盤後**：執行第 123 次主動型 ETF 日更
   ```powershell
   python skills/active-etf-holdings/scripts/collect_active_etf_holdings.py --output-dir wiki/金融投資
   python skills/active-etf-holdings/scripts/add_weekly_summary.py --excel wiki/金融投資/主動型ETF持股明細.xlsx
   python skills/active-etf-holdings/scripts/add_daily_stock_total.py --xlsx wiki/金融投資/主動型ETF持股明細.xlsx
   python skills/active-etf-holdings/scripts/generate_dashboard_data.py
   ```

## 最後更新

- **日期時間**：2026-11-21（週六）08:42
- **更新者**：Antigravity @ DESKTOP-GIM4VFP
- **Git push 狀態**：即將推送
