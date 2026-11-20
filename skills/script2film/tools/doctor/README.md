# 安裝檢查

```bash
python3 tools/doctor/doctor.py                              # 能不能做出第一支片
python3 tools/doctor/doctor.py --need concat,ve,tp,youtube   # 這幾組也當必要
python3 tools/doctor/doctor.py --json                       # 給其他腳本讀
python3 tools/doctor/doctor.py --skip voice                 # 配音、轉錄兩項缺了不算失敗（CI 用）
```

只檢查、印修法：不安裝、不下載、不連線，也不確認帳號登入還有沒有效（VE 只看登入過留下的檔在不在）。每一項一行：`✓` 通過、`✗` 要處理、`－` 選用功能沒裝；
`✗` 與 `－` 的下一行（`→`）是修法。退出碼：0（最後一行 `✓ ready to go`）、1 必要的項目有 `✗`（最後一行 `✗ <n> to fix`）、2 設定檔讀不進來、64 用法錯誤。

檢查的是程式實際會讀到的值：先載入設定檔（`~/.config/script2film/config.json`，見下），再看環境。

| 組 | 項目 | 查什麼 |
|---|---|---|
| 必要 | system | Apple Silicon 的 macOS |
| 必要 | python packages | `pytest`、`opencc`、`PIL`、`numpy`、`fontTools`、`playwright`、`soundfile` 匯入得到（和 `requirements.txt` 同一份；裝在倉庫的 `.venv`，用系統的 `python3` 跑時程式會自己改用它） |
| 必要 | ffmpeg | `ffmpeg`、`ffprobe` 在 PATH，而且有 `libx264` |
| 必要 | node | 22 以上 |
| 必要 | HyperFrames | `S2F_HF_BIN` 或倉庫的 `node_modules/hyperframes`（`npm ci`） |
| 必要 | GSAP | 倉庫的 `node_modules/gsap/dist/gsap.min.js`（`npm ci`；渲染時複製到頁面旁邊，不連 CDN） |
| 必要 | render browser | `HYPERFRAMES_BROWSER_PATH`，或 `~/.cache/hyperframes/chrome` 底下的 `chrome-headless-shell` |
| 必要 | playwright browser | Playwright 自己的無頭瀏覽器與錄影用的 ffmpeg 裝好了（問 `playwright install --dry-run --only-shell chromium` 它們該在哪，看每個位置有沒有裝完的標記 `INSTALLATION_COMPLETE`；跟著 `PLAYWRIGHT_BROWSERS_PATH` 走，不下載、不開瀏覽器）。測試、`doc_code.py` 的音效標記與螢幕錄製拍用它；送 VE、TP 用系統的 Chrome，不在這一項。修法：`.venv/bin/python -m playwright install --only-shell chromium`（`docs/INSTALL.md` 第 3 步） |
| 必要 | voice (TTS) | `S2F_QWEN_TTS_DIR`、它的 `.venv/bin/python`、模型資料夾裡的 `Qwen3-TTS-12Hz-1.7B-Base`（還沒裝：`bash tools/doctor/setup_voice.sh`） |
| 必要 | transcription | `S2F_WHISPER_CPP_MODEL` 指的模型檔（`ggml-large-v3-turbo.bin`）在、`whisper-cli` 找得到（`S2F_WHISPER_CLI` 或 PATH）。只設了舊的 `S2F_MLX_WHISPER_DIR` 會說它已換成 whisper.cpp |
| 必要 | bundled assets | `assets/fonts/manifest.json` 與 `assets/sfx/manifest.json` 列的檔都在（字型檔不在 git 裡，修法會印兩條下載命令；音效隨倉庫附帶，缺了修法是 `git checkout -- assets/sfx`） |
| 必要 | disk | 家目錄所在磁碟剩 5 GB 以上 |
| 必要 | config file | 沒有設定檔算通過；有的話每個鍵都認得、值的型別對、路徑存在（程式自己會建的資料夾不查） |
| `concat` | Concat | 執行檔在（`S2F_CONCAT_BIN` 或 `/Applications/Concat.app`） |
| `ve` | Google Chrome | `/Applications/Google Chrome.app`（VE 與 TP 都用系統裝的 Chrome） |
| `ve` | VE login | 倉庫的 `tools/ve-runner/.profile/Default/Cookies` 在（登入過一次；新複本沒有，修法是 `S2F_VE_HEADED=1 python3 tools/ve-runner/ve_runner.py --login`，自己在開出的視窗登入） |
| `tp` | TP profile folder | `S2F_TP_PROFILE` 或預設位置（`~/.config/script2film/tp-profile`；舊版的預設資料夾已存在而新位置沒有時看舊的）已經建好 |
| `youtube` | YouTube | 上傳用的 Python 環境、憑證資料夾裡的用戶端憑證檔（只看檔在不在） |
| 提醒 | user assets layer | `S2F_ASSETS_LOCAL` 有設而且資料夾在（音效已隨倉庫附帶，這一層放你自己的，同 id 時優先） |
| 提醒 | secrets file permissions | `~/.config/script2film/secrets.json` 存在時權限是 600（只看權限，不開檔） |

「必要」是零付費路徑要的：手寫稿、本機配音與轉錄、`doc_cut.py --render`。其餘四組是選用功能，沒裝只印 `－`；
`--need` 指名的組缺了也算失敗。「提醒」兩項不影響退出碼。
`--skip voice` 把 voice (TTS) 與 transcription 兩項缺的時候改成 `－ … skipped`、不算失敗（JSON 的 status 是 `skipped`），最後一行寫出跳過了哪兩項；裝好了照舊是 `✓`，其他必要項目缺了照樣退出 1。給不裝 6 GB 模型的機器用，例如 CI（`.github/workflows/ci.yml`）。

# 設定檔

`~/.config/script2film/config.json`：一台機器一份，寫一次路徑與偏好，之後不用每個 shell 都 export。鍵名和環境變數相同
（全部的鍵與說明：`python3 tools/config/s2f_config.py --show`）。金鑰不放這裡，放同一個資料夾的 `secrets.json`。

```json
{
 "S2F_QWEN_TTS_DIR": "~/voice/qwen3-tts",
 "S2F_WHISPER_CPP_MODEL": "~/voice/_models/whisper-cpp/ggml-large-v3-turbo.bin",
 "S2F_ASSETS_LOCAL": "~/films/_assets"
}
```

- 優先順序：環境變數 → 設定檔 → 各程式的預設值。環境裡設的是舊名（例如 `QWEN_TTS_DIR`）也算有設。
- shell 腳本或文件裡的指令要用到這些值（例如 `$S2F_DIR/tools/…`）時：`eval "$(python3 <倉庫>/tools/config/s2f_config.py --export)"`。
- `S2F_CONFIG=<另一個檔>` 換一份設定檔；`S2F_CONFIG=none` 不讀設定檔（測試都這樣跑）。
- 設定檔壞掉（不是合法的 JSON）時所有工具都會停下來並印出檔名。
- 起手模板（`skills/ve-director/doc/formats/vox-host/make_doc_template.py`）是複製到專案裡用的，它自己找這個倉庫：
  先看環境變數 `S2F_DIR`，再從自己的位置往上找。設定檔裡的 `S2F_DIR` 對這一步不起作用，其餘的鍵都有效。

## 安裝腳本

`doctor.py` 只檢查。配音與轉錄的環境用 `bash tools/doctor/setup_voice.sh [<資料夾>] [--design]` 裝：抓 Qwen3-TTS 官方程式（釘在測過的版本）、建兩個 Python 3.11 環境、下載配音模型、把兩個路徑寫進設定檔；做過的部分會跳過，可以重跑。整套安裝的順序與實測時間在 `docs/INSTALL.md`。
