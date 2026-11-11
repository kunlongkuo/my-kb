# 用 Claude in Chrome 操作 Flow／Gemini 生成（Veo 影片、背景音樂）

圖生影片預設用 **Google Flow**，其次 **Gemini（Veo）**；進到這一步前先讓使用者選。

先讀 `anthropic-skills:chrome-browser` skill。工具一次載齊：
`tabs_context_mcp, tabs_create_mcp, tabs_close_mcp, navigate, computer, find, read_page, javascript_tool, file_upload, browser_batch`。
輔助 JS 片段在 `scripts/veo_browser.js`（A～E）。

## 背景音樂（Gemini）

1. 新分頁開 `https://gemini.google.com/app`，在輸入框輸入（中文即可）：
   「請生成一首約 90 秒的純音樂（無人聲、無歌詞），作為<主題>宣傳動畫的背景音樂。風格：溫暖、明亮、充滿希望與榮耀感，電影感管弦樂結合輕快鋼琴與鈴音，帶一點科技感的電子脈衝點綴；約 100 BPM，輕柔開場逐漸堆疊，中段情緒高峰，結尾莊嚴和弦收束並自然淡出。適合搭配旁白。」
2. 約 1 分鐘完成。滑鼠移到唱片卡上出現下載鈕 → 選「僅音訊 MP3」。
3. 從 `~/Downloads` 搬到 `<專案>/Codex/audio/`。用 ffprobe 看長度；Claude 聽不到聲音，「無人聲」要請使用者試聽確認。

## Veo 影片：Google Flow（預設建議）

1. `https://labs.google/fx/tools/flow` → 「新增專案」，關掉功能介紹視窗。
2. 設定鈕（顯示「影片 · 720p · 8 秒 x 2」）：模型選 **Veo 3.1 - Fast**、數量 **x 1**（x 2 會花雙倍點數）。Veo 3.1 固定 8 秒 720p。
3. 首幀：點「開始」→ 素材選取器的「上傳媒體檔案」（先執行 JS **A**，用 computer 點擊）→ `file_upload`。輸入框支援多檔，可把所有構圖圖轉 JPG（q=2，約 0.8MB）一次上傳，總量 < 10MB。
4. 之後每鏡：JS 片段 **C**（選 `sXX.jpg` 當首幀並聚焦）→ `computer type` 提示詞 → JS 片段 **D**（檢查後送出）。可連續排入多鏡。
5. 輸入框若變成「Agent」參考圖模式（上方出現兩張小圖、沒有「開始／結束」），點「Agent」膠囊切回首幀模式；不要在 Agent 模式送出。
6. 下載：JS 片段 **E** 標記下載鈕 → `find claude-dl-*` → 用 `computer left_click` 逐一點（JS click 下載不會觸發）。
   - Chrome 第一次只放行 1 個下載，之後需使用者在網址列允許「自動下載多個檔案」。下載仍沒有檔案時，請使用者確認權限或手動下載，不要繞道（攔截 blob、localhost 接收都會被 Chrome 另外擋權限）。
7. 下載檔名是 Flow 自取的英文名，用 `scripts/identify_clips.py` 以首格比對分鏡圖自動歸位。

## Veo 影片：Gemini（使用者選擇時，或 Flow 點數用完）

每鏡一個分頁（可同時開數個分頁並行送出）：
1. `navigate` 到 gemini.google.com/app，執行 JS 片段 **A**（攔截檔案輸入）＋ **B**（開「建立影片」）。
2. `find "上傳檔案 button"` → 用 `computer left_click` 真的點它（JS 的 click 不會觸發）→ `find "claude upload input"` → `file_upload` 構圖圖（PNG < 10MB）。
3. 還原 A 的攔截；`javascript_tool` 讓 `[contenteditable=true]` 取得焦點 → `computer type` 打英文動作提示詞 → `key Return`。
4. 約 1.5～3 分鐘後 `find "下載影片"` → 點擊；檔案在 `~/Downloads/gemini_generated_video_*.mp4`（1280×720、24fps、約 10 秒、有音軌）。

**額度**：Gemini 每日 Veo 次數有限。回覆「我是文字型 AI」「我只是個語言模型」「I'm having a hard time」「I seem to be encountering an error」＝額度用完或被拒（偶爾仍會出片，先 `find 下載影片` 確認）。用完就告知使用者並改用 Flow，不要在 Gemini 重試。

## 常見問題

- 截圖逾時（renderer frozen）：Flow 分頁很重，改用 `javascript_tool` 讀 `document.body.innerText` 判斷狀態，或降低 `scale` 再截。
- 分頁 ID 失效：重新 `tabs_context_mcp`。完成後關掉自己開的分頁；不在本次群組的分頁關不掉，請使用者自行關閉。
