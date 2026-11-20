---
name: script2film
description: 用想法或文稿做成帶有旁白、字幕、圖表與動態場景的完整解說片或知識短影音（Script2Film 工作流）。從想法或文稿出發，經結構化文稿 doc.json、使用者確認、本機/雲端配音、自動逐字對時（Whisper/Scribe）、27 種程式動態場景渲染（折線、圓餅、算式、時間軸、清單、地圖路線、標記重點等）、自動剪輯渲染（-14 LUFS、字幕燒錄），到成片機器自檢（黑格、長度、音效、音畫同步）。支援 VideoExpress 實景鏡頭、TalkingPhoto 虛擬主持人與 Google Flow 擴充。當使用者提到「script2film」「文字做成影片」「稿子做成影片」「做解說片」「科普影片」「知識短影音」「用程式畫圖表影片」「VOX 風格短片」「doc.json」時請務必觸發此技能。
---

# 🎬 Script2Film 影片製作技能（Agent Skill）

> **只要你有想法，剩下的交給 Agent。**  
> Script2Film 是一套給 AI Agent 專用的解說片／旁白影片製作系統。一段想法、一份講稿，即可輸出具有繁中旁白、同步字幕、27 種程式繪製動態場景、背景音樂與虛擬主持人的高質感成品。  
> 核心流程全部可在本機運行，出片前自動執行完整機器審片（無黑格、音畫同步、響度達標）。

---

## 📂 Repo 與工具位置

- **主程式根目錄**：`i:\Mark\my-kb\skills\script2film\`
- **主要工作流說明**：[docs/FLOW.md](file:///i:/Mark/my-kb/skills/script2film/docs/FLOW.md)
- **場景與 doc.json 規範**：[skills/ve-director/doc/README.md](file:///i:/Mark/my-kb/skills/script2film/skills/ve-director/doc/README.md)
- **色盤與視覺畫廊**：[docs/gallery.html](file:///i:/Mark/my-kb/skills/script2film/docs/gallery.html)
- **核心工具目錄**：`tools/`（包含 doctor、assemble、concat、checklist、tp、ve-runner 等）

---

## 🌟 核心理念與特色

1. **從想法出發（Idea-First）**：不是拿拍好的素材東剪西湊，而是從文稿與大綱出發，哪一句旁白配什麼畫面、何時強調重點，全寫在結構化檔案 `doc.json` 中。
2. **27 種程式繪製場景（Code-Drawn Scenes）**：折線圖、圓餅圖、數學算式、時間軸、清單對照、地圖路線、逐字高亮引言等，由程式精準繪製，數字與事實不會產生幻覺。
3. **10 套專業色版（Themes）**：包含 `lecture-light`（清爽教學）、`lecture-dark`（現代深色）、`lecture-finance`（財經商業）、`lecture-tech`（科技）、`lecture-history`（人文歷史）等，一鍵切換整部片氛圍。
4. **自動配音與音畫毫秒對時**：支援本機 Qwen3-TTS / 參考聲音克隆，並由 Whisper.cpp 或雲端 ASR（Groq / ElevenLabs）自動產出精準到毫秒的逐字時間軸。
5. **機器自動審查（Machine Quality Check）**：產出影片時自動檢驗片長、音畫對齊、黑格偵測、音量響度（-14 LUFS 國際標準），並輸出 Contact Sheet 截圖供 Agent 與使用者審視。
6. **選用模組靈活擴充**：
   - **實景鏡頭**：VideoExpress.ai、Google Flow（Veo / Omni）或 MiniMax H3。
   - **虛擬主持人**：TalkingPhoto 對嘴（全版、角落圓框 pip、右側分割視窗 side）。
   - **背景音樂**：自動淡入淡出、說話時自動壓音（Audio Ducking）。

---

## 🚦 核心安全守則與停等點（Stop and Ask）

AI Agent 在執行過程中，**必須在以下關鍵步驟停下來向使用者確認**：

1. **【停等點 F1・文稿確認】（最重要！）**：
   - 產生 `doc.json` 後，必須**完整列印旁白逐字稿與節奏分鏡表（Beat Table）**給使用者看。
   - **必須等使用者回覆確認同意（OK / 確認）後**，才可進入配音階段（執行 `doc_tts.py` 時需帶 `--script-approved` 參數；未確認前腳本會拒絕執行並 exit 4）。
   - 嚴禁自行代表使用者同意或略過文稿審查。
2. **外部額度扣點前**：送出 VideoExpress、TalkingPhoto、Google Flow 等可能扣除點數的服務前，必須說明費用與設定並徵得同意。
3. **影片發布前**：上傳至 YouTube 或社群平台前，必須由使用者下達明確指令。

---

## 🛠️ 標準工作流程（F0 ～ F6）

所有指令建議於 `i:\Mark\my-kb\skills\script2film\` 目錄下執行。

### 步驟 F0：環境診斷（Install Check）
```powershell
python tools/doctor/doctor.py --skip voice
```
- 確認系統依賴、Python 套件、Node/HyperFrames、FFmpeg、Noto 中文字型等全部通過。

### 步驟 F1：編寫文稿與分鏡定義（`doc.json`）
- 在專案目錄（例如 `examples/my-explainer/`）建立 `doc.json`，包含：
  - `lines`：旁白句子清單
  - `beats`：畫面拍點分配（哪一句配哪種場景 `pie`, `line`, `quote`, `list`, `timeline`, `ve`...）
  - `theme`：選定色版（如 `lecture-light`, `lecture-tech`）
- 驗證語法：
  ```powershell
  python skills/ve-director/doc/scripts/doc_lint.py <專案路徑>/doc.json
  ```
- **🛑 停等使用者確認**：展示逐字稿與拍點分鏡，獲得確認後方可繼續！

### 步驟 F2：旁白配音（Voice Generation）
```powershell
python skills/ve-director/doc/scripts/doc_tts.py <專案路徑>/doc.json --script-approved
python skills/ve-director/doc/scripts/doc_voice.py <專案路徑>/doc.json
```
- 每句生成多條候選，自動比對並串接最穩定的一條，輸出 `voice.wav`。

### 步驟 F3：聲音與文字對齊（Alignment & Timing）
```powershell
python skills/ve-director/doc/scripts/doc_align.py <專案路徑>/doc.json
```
- 產出 `beats.json` 與字幕檔 `final.srt`，作為後續所有視覺時間軸的唯一標準。

### 步驟 F4：程式繪製動態場景（Scene Rendering）
```powershell
python skills/ve-director/doc/scripts/doc_code.py <專案路徑>/doc.json --render
```
- 透過 HyperFrames  headless 引擎渲染所有程式圖表與文字動態。

### 步驟 F5：成片自動剪輯與合成（Cut & Assemble）
```powershell
python skills/ve-director/doc/scripts/doc_cut.py <專案路徑>/doc.json --render
```
- 將動態場景、旁白、背景音樂、燒錄字幕組裝成成片 `cut_<theme>/output.mp4`，自動平衡音量至 -14 LUFS。

### 步驟 F6：品質自檢與交付（Quality Check）
```powershell
python tools/nightly/check.py <專案路徑>/cut_<theme>/output.mp4
```
- 檢查長度一致性、有無黑格、音畫同步，產出每個 Beat 起點的聯絡表（Contact Sheet）供最後審查。
