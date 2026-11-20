# tools/checklist — 開工清單

一張清單管「開工前」和「出片前」該成立的事。送 VE、送 TP、上傳三支程式開頭會自己跑它，不過就停，所以規則不用靠人記得去讀。

## 用法

```
python3 tools/checklist/checklist.py run <集資料夾> --stage start      # 開工前
python3 tools/checklist/checklist.py run <集資料夾> --stage release    # 出片前（先跑開工前的全部項目）
python3 tools/checklist/checklist.py questions <集資料夾> --stage start|release   # 這一段要回答的題目、出處、目前的答案
python3 tools/checklist/checklist.py answer <集資料夾> <題目代號> "<這一集的答案>"
```

- 集資料夾裡有 `doc.json` 是解說長片，有 `day.json` 是書頁短片；兩個都沒有就停（退出碼 2）。
- 每一項印 `✓`（過）、`✗`（不過）、`－`（不適用，後面是原因）。退出碼 0＝全過、1＝有項目不過、2＝用法或設定寫錯。
- 結果寫到 `<集>/nightly/checklist_<stage>.json`；早上的報告（`tools/nightly/report.py`）讀開工段那一份。
- 舊指令 `python3 tools/nightly/preflight.py <集>/doc.json` 還能用，等於跑開工段。

## 三層、兩段

| 層 | 誰決定 | 系列能不能關 |
|---|---|---|
| 通則 | 工具內建，每支片都跑 | 不能 |
| 格式 | 工具內建，依 `doc.json`／`day.json` 自動選（書頁短片目前只跑通則層） | 不能 |
| 系列 | 上一層有 `series.json` 才跑；沒有就當單集，印一行說明 | 標了「可宣告」的項目可以 |

| 代號 | 內容 | 層 | 段 | 可宣告不適用 |
|---|---|---|---|---|
| `disk` `node` `power` `concat` | 磁碟剩餘、node 版本、接電源、Concat 執行檔 | 通則 | start | 否 |
| `env-dirs` | `S2F_QWEN_TTS_DIR`（資料夾）、`S2F_WHISPER_CPP_MODEL`（轉錄模型檔）要設而且在；`S2F_ASSETS_LOCAL`（使用者素材層）選用，沒設照樣通過、只用內附素材，有設就要資料夾在。值可以寫在 `~/.config/script2film/config.json`（不必每次 export）；`python3 tools/config/s2f_config.py --show` 看現在的值與來源 | 通則 | start | 否 |
| `lexicon` | 讀音表（`tools/tts/lexicon.json`）載得進來、規則沒有重複或空的 | 通則 | start | 否 |
| `voice-ref` `triggers` `facts` `no-dash` | 參考音、稿面觸發字、事實清單、旁白沒有破折號 | 格式（解說長片） | start | 否 |
| `inventory` | 素材盤點（`tools/qa/inventory.py`）：連續純字卡秒數、同一支背景秒數、照片／VE／字卡比例。**只印不擋** | 格式（解說長片） | start | 否 |
| `answers` | 逐條作答：這一段的題目（出片段含開工段的）每題都答了，而且答案是對著現在的旁白寫的 | 通則＋系列 | start、release | 否 |
| `asr-keys` | 雲端轉錄的金鑰（只提示，不擋） | 格式（解說長片） | start | 否 |
| `series` `font` | 系列設定讀得到、字型檔在 | 系列 | start | 否 |
| `yt-token` | YouTube 權杖與範圍 | 通則 | release | 否 |
| `credits` | `assets/` 底下的圖檔與影片檔每個都登記在 `assets/CREDITS.md`（工具去背產生的 `<名>_fg.png` 跟著原圖算；`assets/src/` 不算） | 通則 | release | 否 |
| `bgm-file` `bgm-credit` `thumb` | 配樂檔、配樂署名、縮圖設定 | 格式（解說長片） | release | 否 |
| `release-check` | 出片檢查（`tools/nightly/check.py`）通過，而且不比成片舊 | 格式（解說長片） | release | 否 |
| `lead-est` | 引言卡、數字卡開頭不空白（稿面估算）：還沒配音就照字數估卡片幾秒才出現（每字 0.21 秒），晚於 1.0 秒、畫面上又沒有別的東西就擋；只估中文稿，已經對時過就用實測 | 格式（解說長片） | start | 否 |
| `blank-lead` | 引言卡、數字卡開頭不空白（對時後實測）：觸發字落在第二句以後（`doc_code.empty_first_line`），或落在第一句裡但晚於 1.0 秒、畫面上又沒有別的東西（`doc_code.late_first_element`），都擋；渲染前 `doc_code.py` 也擋 | 格式（解說長片） | release | 否 |
| `subs-files` | 字幕檔：集或系列有設 `subs.burn` 才查；`cut_<色版>/subtitles_<語言>.srt` 每個該有的都在，而且不比 `beats.json` 舊。字幕檔是上傳後手動傳的，上傳程式成功後會印出要傳哪幾個 | 格式（解說長片） | release | 否 |
| `upload-fields` | `series.json` 有 `backup`、`desc_head`、`desc_body`、`hook_lines`（`yt_meta.py` 要的） | 系列 | release | 是 |

配樂、縮圖、權杖放在出片段：開工時本來就還沒有。

## 系列宣告某一項不適用

寫在系列的 `series.json`，要寫原因；只有上表「可宣告」的項目才收，其他的寫了清單會停下報錯：

```json
"checklist": {"na": {"upload-fields": "說明欄每集手寫，不用 yt_meta 產"}}
```

## 逐條作答（機器驗不了的規則）

有些規則只能靠判斷，例如「生成畫面不能冒充具名的真實地點」。這類規則寫成題目，每一集都要用一句話回答，答案要指得出拍號或檔名。

- 通則的題目在 `tools/checklist/rules.json`（每題有 `id`、`stage`、`ask`、`source`，選用的 `format` 限定只問哪一種格式；選用的 `when_file` 是集資料夾裡的相對路徑，那個檔存在才問，例如 `h3-territory` 只問有 `h3/manifest.json` 的集，見 `tools/h3/README.md`）。
- 系列的題目寫在 `series.json`：

  ```json
  "checklist": {"rules": [{"id": "review-done", "stage": "start", "ask": "稿子過外部審稿了嗎？", "source": "SERIES.md:10"}]}
  ```
- **題目包**：`tools/checklist/packs/` 附四組可選的題目，系列在 `series.json` 寫 `"checklist": {"packs": ["current-affairs", "publishing"]}` 才會問。`current-affairs`（時事：外部審稿、立場用詞、真人照片來源、貼文日期、實拍來源）、`scripture`（聖經題材：經文對譯本、來源以外的事實、生成人物的臉、推估的拍要標）、`host`（有主持人：定稿圖、送主持人前先聽）、`publishing`（上架：縮圖、頻道）。系列獨有的題目另外寫在 `checklist.rules`，代號不能和通則或包裡的重複。
- 答案存 `<集>/checklist_answers.json`，連同作答當下旁白全文的指紋。旁白改過，清單會列出「narration changed, confirm again」：重新 `answer` 一次（內容沒變就原文再送）。
- 機器只驗「每題都答了、答案對得上現在的旁白」，驗不了答案的真假；答案是留給人看的紀錄。

## 素材盤點的目標（只標記）

系列可以在 `series.json` 寫比例目標，清單把實測值和目標並排印出，超出只標「over target」，不擋：

```json
"checklist": {"targets": {"photo": [0.2, 0.3], "ve": [0.3, 0.5], "card_max": 0.3}}
```

`photo`、`ve` 是扣掉主持人之後的比例範圍，`card_max` 是字卡（含主持人框的字卡）的上限。

## 三支程式開頭的清單

| 程式 | 跑哪一段 | 集資料夾怎麼找 |
|---|---|---|
| `tools/ve-runner/ve_runner.py <run sheet>` | start | 從 run sheet 所在資料夾往上找有 `doc.json` 或 `day.json` 的資料夾，取最外層的（集底下的 `extra_live/` 之類也有自己的 `doc.json`，要檢查的是整集）。`--inspect` 不帶 run sheet，不經過清單 |
| `tools/tp/tp_host.py <集>` | start | 第一個參數 |
| `tools/youtube/yt_upload.py upload <影片>` | release | 從影片所在資料夾往上找 |

- 往上找到的 `doc.json`／`day.json` 讀不進來或不是 JSON 物件（例如別的工具輸出的陣列）：那個資料夾不算集，印一行 `note:` 說略過了哪個檔，接著往上找。明確指定的集不這樣略過：直接傳那份 `doc.json`／`day.json`，或傳的資料夾本身就放著它（`tp_host.py <集>`、`checklist.py run <集>`）時，壞了照樣報錯（退出碼 2，不能用 `--skip-checklist` 帶過）。
- 找不到集資料夾：送 VE、送 TP 印「not in an episode folder: the checklist does not apply」，照常執行（例如用 VE 做沒有 `doc.json` 的故事片）。上傳不一樣：影片不在任何集資料夾內就停，要帶 `--skip-checklist "<原因>"` 才上傳，紀錄寫在影片旁邊的 `checklist_skips.jsonl`。
- 「接電源」只提醒不擋：沒接電源時那一列仍是 ✓，說明寫「not on AC power」。
- 不過就印出不過的項目並退出（退出碼 1），在開瀏覽器或連線之前。
- 硬要執行：加 `--skip-checklist "<原因>"`。清單不過時才會用到它：原因不能是空的；清單全過時帶了也不留紀錄。每次跳過在 `<集>/nightly/checklist_skips.jsonl` 記一行（時間、哪一步、原因、當時不過的項目）。`series.json` 的清單設定寫錯時不能跳過，先改對。
- 產旁白、畫字卡、剪接不擋：本機、免費、可以重跑。

## 測試

```
python3 -m pytest tools/checklist -q
```
