# Handoff — 主動型 ETF 知識庫

## 目前做到哪

**1. 安裝並配置完成 Script2Film 影片製作技能 🎬**
- 倉庫位置：`skills/script2film/`
- Agent 技能入口：
  - `.agents/skills/script2film/SKILL.md`
  - `.agents/skills/ve-director/SKILL.md`
  - `.agents/skills/google-flow/SKILL.md`
- 依賴安裝：Node / npm（HyperFrames, GSAP）、Chrome Headless Shell、Python（pytest, opencc, soundfile）、思源黑體與宋體可變字型。
- 檢驗通過：`doctor.py --skip voice`（✓ ready to go）與 `doc_lint.py` 驗證成功。

**2. 建立首支 VOX 科普短片企劃《堆高機的運作原理》**
- 專案檔案：`skills/script2film/projects/forklift/doc.json`
- 進度：已完成文稿與 5 拍分鏡表（Beat Table），通過 `doc_lint.py` 檢查，停等點 F1 就緒。

## 目前狀態

✅ 所有技能與指令配置完畢，環境正常可運行。

- 工作區乾淨，無衝突。
- 安全掃描：通過，無敏感金鑰洩漏。

## 下一步

1. **堆高機科普短片接續製作**：使用者回覆確認後，即可依序執行：
   - F2 旁白配音：`python skills/ve-director/doc/scripts/doc_tts.py projects/forklift/doc.json --script-approved`
   - F3 逐字對時：`python skills/ve-director/doc/scripts/doc_align.py projects/forklift/doc.json`
   - F4 場景繪圖：`python skills/ve-director/doc/scripts/doc_code.py projects/forklift/doc.json --render`
   - F5 自動剪輯：`python skills/ve-director/doc/scripts/doc_cut.py projects/forklift/doc.json --render`
2. **2026-11-23（週一）**：執行第 123 次主動型 ETF 日更
   ```powershell
   python skills/active-etf-holdings/scripts/collect_active_etf_holdings.py --output-dir wiki/金融投資
   python skills/active-etf-holdings/scripts/add_weekly_summary.py --excel wiki/金融投資/主動型ETF持股明細.xlsx
   python skills/active-etf-holdings/scripts/add_daily_stock_total.py --xlsx wiki/金融投資/主動型ETF持股明細.xlsx
   python skills/active-etf-holdings/scripts/generate_dashboard_data.py
   ```

## 最後更新

- **日期時間**：2026-11-21（週六）07:03
- **更新者**：Antigravity @ DESKTOP-GIM4VFP
- **Git push 狀態**：已推送
