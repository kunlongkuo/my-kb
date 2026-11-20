# Handoff — 主動型 ETF 知識庫

## 目前做到哪

**已安裝並配置完成 Script2Film 影片製作技能 🎬**

- 倉庫位置：`skills/script2film/`
- Agent 技能入口：
  - `.agents/skills/script2film/SKILL.md`（解說短片、27 種程式圖表、對時、自動剪輯合成）
  - `.agents/skills/ve-director/SKILL.md`（VideoExpress 分鏡導演、提示詞生成）
  - `.agents/skills/google-flow/SKILL.md`（Google Flow / Veo / Lyria 生成）
- 依賴安裝：Node / npm（HyperFrames, GSAP）、Chrome Headless Shell、Python（pytest, opencc, soundfile）、思源黑體與宋體可變字型。
- 檢驗通過：`doctor.py --skip voice`（✓ ready to go）與 `doc_lint.py` 驗證成功。
- 文件更新：`AGENTS.md`、`ANTIGRAVITY.md`、`README.md`、`docs/PROGRESS.md`、`每日筆記/2026-11-21.md`。

## 目前狀態

✅ 所有技能與指令配置完畢，環境正常可運行。

- 工作區乾淨，無衝突。
- 安全掃描：通過，無敏感金鑰洩漏。

## 下一步

1. **影片製作嘗試**：使用者若想嘗試第一個解說短片，可隨時發送稿子或想法觸發 `script2film`。
2. **2026-11-23（週一）**：執行第 123 次主動型 ETF 日更
   ```powershell
   python skills/active-etf-holdings/scripts/collect_active_etf_holdings.py --output-dir wiki/金融投資
   python skills/active-etf-holdings/scripts/add_weekly_summary.py --excel wiki/金融投資/主動型ETF持股明細.xlsx
   python skills/active-etf-holdings/scripts/add_daily_stock_total.py --xlsx wiki/金融投資/主動型ETF持股明細.xlsx
   python skills/active-etf-holdings/scripts/generate_dashboard_data.py
   ```

## 最後更新

- **日期時間**：2026-11-21（週六）06:49
- **更新者**：Antigravity @ DESKTOP-GIM4VFP
- **Git push 狀態**：準備推送
