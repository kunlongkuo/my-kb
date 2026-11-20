# tools/tp — TalkingPhotos 主持人

用 TalkingPhotos（TP）把分段的主持人音檔做成會說話的主持人影片。所有操作都經過一個開著的 Chrome（`tp_browser.py serve`，CDP 埠 9333），各支腳本連上去做一步就離開。

## 登入

TP 要在 `serve` 開出來的 Chrome 視窗裡**自己登入**（腳本不輸入帳號密碼）。登入狀態存在設定檔資料夾裡，之後的 `serve` 沿用。結束 `serve` 時送 SIGTERM（`kill -TERM <pid>`），讓它把登入狀態寫回設定檔；不要直接砍 Chrome。

## 腳本

| 腳本 | 用途 | 用法 |
|---|---|---|
| `tp_browser.py` | 開著已登入的 Chrome 給其他腳本連；也提供單步操作（截圖、點文字、執行 JS、上傳、填字） | `python3 tools/tp/tp_browser.py serve`（背景跑）；`… shot <out.png>`、`… click "<文字>"`、`… eval "<js>"`、`… upload "<css>" <檔>`、`… fill "<css>" "<文字>"` |
| `tp_host.py` | 一集的主持人分段一鍵做完：上傳音檔 → 送渲染 → 等 → 下載 → 驗長度 | `python3 tools/tp/tp_host.py <集資料夾> --prefix <名稱前綴> [--look "<造型>"] [--parts 1 3] [--timeout 30]` |
| `tp_multi.py` | 好幾集的分段排成一條隊伍送，讓同時渲染一直保持在上限 | `python3 tools/tp/tp_multi.py <集資料夾>:<prefix>[:<look>] ... [--timeout 30]` |
| `tp_upimg.py` | 把造型圖上傳到 TP 媒體庫 Images。上傳前量比例，和 `TP_ASPECT` 不合就停；`--fit` 置中裁成那個比例再傳（裁在暫存副本上，原檔不動），`--as-is` 不裁照傳。TP 顯示的名字不一定等於檔名（底線會變空白、開頭變大寫）：成功時印出 TP 顯示的名字，`--look` 填那個 | `python3 tools/tp/tp_upimg.py [--fit \| --as-is] "<造型名>.jpg" ...` |
| `tp_submit.sh` | 全新流程：選角色（原版或造型）→ 匯入音檔 → 送出；`tp_host.py` 會呼叫它 | `tools/tp/tp_submit.sh "<音檔名>" "<成片名>" ["<造型>"]` |
| `tp_swap.sh` | 流程停在上一次的 Render 步驟時，換音檔與名稱（停在按 Render 之前） | `tools/tp/tp_swap.sh "<音檔名>" "<成片名>"` |
| `tp_pick.sh` | 在目前頁面照名字點一張卡並按 Select | `tools/tp/tp_pick.sh "<卡片名>"` |
| `tp_paths.py` | 設定檔與 `serve` 紀錄檔的位置（給上面幾支用） | — |

`tp_browser.py` 要 `playwright` 與本機的 Chrome。

`tp_host.py` 開頭會先跑開工清單（`tools/checklist/README.md`）：集過不了就不送，在開瀏覽器之前退出。硬要送加 `--skip-checklist "<原因>"`，會記在 `<集>/nightly/checklist_skips.jsonl`。

## 環境變數

| 名稱 | 用途 | 沒設時 |
|---|---|---|
| `S2F_TP_PROFILE` | TP 專用的 Chrome 設定檔資料夾（含登入 cookie，放在倉庫外）；舊名 `TP_PROFILE` 也認（新名有設就只用新名） | `~/.config/script2film/tp-profile`（舊版的預設資料夾已經存在、新位置還沒有時，沿用舊的，不用重登） |
| `TP_ORIGINAL` | 不給造型時用的原版角色在 TP「Choose Previous Character」裡的名稱 | 沒有預設：要用原版角色而沒設，`tp_submit.sh` 會停下 |
| `TP_AUDIO_DIR` | 媒體庫裡放音檔的資料夾名 | `Audio` |
| `TP_ASPECT` | 畫面比例（直式給 `9:16`）；新角色與原版角色都適用 | `16:9` |
| `TP_GENDER` | 新角色的性別選項 | `male` |
| `TP_HEADLESS` | `1`＝不開視窗（不建議：TP 無頭多半落在登入頁） | 開視窗 |

`tp_host.py` 自己起 `serve` 時，紀錄寫在設定檔資料夾的上一層 `tp_serve.log`。

**閒置自動關**：`serve` 連續 10 分鐘沒有任何單步指令連進來就自己正常關閉（和收到 SIGTERM 一樣的收尾，登入狀態會寫回）。等渲染時 `tp_host.py` 每分鐘會來查一次，不會被關。要改時間設 `S2F_TP_IDLE_MIN=<分鐘>`，設 `0` 不自動關（例如要在視窗裡手動操作很久，或用別的工具直接連 9333 埠、不經過 `tp_browser.py` 的時候）。2026-11-15 實測：設 1 分鐘，64 秒後自己關、沒有殘留程序，再開仍是登入狀態。

## 測試

```
python3 -m pytest tools/tp -q
```
