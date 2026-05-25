---
title: Jason Tools (JTDT)
category: METHOD
tags: [PDF, Office, 資安, 開源, 工具軟體]
sources: [raw/obsidian/Jason Tools 文件工具箱 — PDF  Office 整合式文件處理平台.md, cards/Jason-Tools-功能摘要.md]
status: verified
updated: 2026-05-03
---

# Jason Tools (JTDT)

Jason Tools (JTDT) 是一個整合式的 PDF 與 Office 文件處理平台，旨在提供一個安全、在地化且可控的文件處理環境，避免敏感資料流向第三方雲端服務。

## 核心價值
1. **隱私優先**：檔案不離開伺服器，無 API 調用或遠端遙測。
2. **開源透明**：Apache 2.0 授權，原始碼可稽核。
3. **企業級控管**：具備認證、權限矩陣、稽核與 SIEM 整合能力。

## 主要功能分類

### 1. 填單、用印與浮水印
- **表單自動填寫**：自動辨識 PDF/Office 欄位並填入公司 Profile。
- **用印與簽名**：支援拖曳定位印章、簽名，支援批次處理。
- **浮水印**：可調整透明度、角度、平鋪，直接寫入 Content Stream。

### 2. 檔案編輯與壓縮
- **輕量編輯器**：疊加文字、圖片、形狀或刪除原內容。
- **PDF 壓縮**：多段 DPI 設定與字型子集化。
- **頁面整理**：合併、分拆、轉向、頁碼排版。

### 3. 內容萃取與分析
- **文字擷取**：輸出 Markdown/Word，支援 LLM 段落重排。
- **附件與註解**：萃取 PDF 附件，整理並匯出註解清單 (CSV/Markdown)。
- **字數統計**：提供多維度統計圖表。

### 4. 格式轉換
- **文書轉 PDF/圖片**：Word/Excel/PPT 轉檔（需 OxOffice 引擎）。
- **圖片轉 PDF**：支援多圖排序與頁面設定。

### 5. 資安處理 (Redaction)
- **去識別化**：自動偵測身分證、信用卡等敏感個資，執行編修 (Redaction) 或遮罩 (Masking)。
- **加密保護**：AES-256 加密、權限控制、中繼資料 (Metadata) 清除。
- **風險掃描**：清除 JavaScript、嵌入檔等隱藏內容。
- **差異比對**：文件並排比對 (Diff)。

## 技術架構與安裝
- **環境**：Python 3.12 (uv 管理)，不需預裝系統 Python。
- **引擎**：處理 Office 格式需 OxOffice 或 LibreOffice。
- **平台**：支援 Linux (Ubuntu 22.04+), macOS 12+, Windows 10+。
- **部署**：支援單機模式與伺服器模式 (Bind 0.0.0.0)。

## 參考資料
- [Ref] [[Jason Tools 文件工具箱 — PDF  Office 整合式文件處理平台]]
- [Ref] [GitHub README](https://github.com/jasoncheng7115/jt-doc-tools)
