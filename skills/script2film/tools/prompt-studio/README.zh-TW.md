# Prompt Studio

一個 HTML 檔，把一段點子展開成可以貼進 VideoExpress 的分鏡或單鏡頭提示詞。[English](./README.md)

完整介紹、截圖與線上版在專案網站的 Prompt Studio 頁（[`docs/studio.html`](../../docs/studio.html)）。這份說明只寫怎麼打開、怎麼修改它。

## 打開

- 用任何瀏覽器打開 [`prompt-studio.html`](prompt-studio.html)，不用安裝，不用帳號。
- 要用本機的 Ollama 模型展開提示，改用啟動檔打開：macOS 點兩下 `PromptStudio.command`，Windows 點兩下 `PromptStudio.bat`。它會把這個資料夾開在 `http://localhost:8765`，因為 Ollama 不接受直接點開檔案的頁面送來的請求。

## 修改它

在這個資料夾裡跑：

```bash
node snapshot-test.js        # 產出提示的快照測試，不連網、不用金鑰
node eval.js --list          # 列出語言模型評測案例，不送出任何東西
node eval.js --run           # 會呼叫語言模型：要 GEMINI_API_KEY（或 GROQ_API_KEY／NVIDIA_API_KEY／OPENROUTER_API_KEY）
node check-links.mjs README.md README.zh-TW.md   # 檢查這兩份說明裡的本機連結都指得到檔案
```

網站在 `docs/studio/app.html` 放了一份工具的複本。改了 `prompt-studio.html` 之後，在專案根目錄跑：

```bash
python3 tools/site/sync_studio.py
```

複本沒跟上時，`tools/site/tests/test_site_studio_copy.py` 會失敗。

## 授權

[MIT](../../LICENSE)。劇本寫作規則濃縮自 MIT 授權的 [AI-drama-pound](https://github.com/POUND0423/AI-drama-pound)，出處見 [`NOTICE.md`](../../NOTICE.md)。
