# tools/score — 程式作曲的配樂

把畫面的段落（幾秒到幾秒、是開場還是轉折）寫成 events，照它自動編曲，用 SoundFont 離線渲染成 wav。每段開頭落在拍點上，同一份 events 每次產出的檔完全相同（亂數種子取自名稱）。不連網、不用任何金鑰。

## 安裝

```
cd tools/score && uv sync
```

音色庫不隨倉庫附（32 MB）。到 <https://github.com/mrbumpy409/GeneralUser-GS> 下載 `GeneralUser-GS.sf2`，放到 `$S2F_ASSETS_LOCAL/soundfonts/`，或把環境變數 `S2F_SOUNDFONT` 設成那個檔的路徑。找不到時程式會停下並印這兩個位置。授權見倉庫根目錄 `NOTICE.md`。

## 用法（都在 `tools/score` 底下跑）

| 要做什麼 | 指令 |
|---|---|
| doc 模式的一集：照 `doc.json` 的 `bgm.arc` 分段作曲、接成一條 | `uv run python adapters/doc_arc.py <集>/doc.json --render --out <集>/score_bgm.wav` |
| 只看分段與角色，不作曲 | `uv run python adapters/doc_arc.py <集>/doc.json` |
| 自己寫 events：編曲＋渲染 | `uv run python score.py make <events.json> [--lufs -20]` |
| 只編曲，產出可以手改的計畫 | `uv run python score.py plan <events.json> [--out <plan.json>]` |
| 照改過的計畫渲染 | `uv run python score.py render <plan.json>` |
| 把配樂疊進影片（保留原音軌） | `uv run python score.py mux <影片> <配樂.wav> [--out <輸出.mp4>]` |
| 檢查段首有沒有落在拍點 | `uv run python check_align.py <wav> <plan.json>`（命中率 ≥ 0.8 且比隨機基線高 0.3 才 exit 0） |
| 量一首參考曲的 BPM、調性、頻段 | `uv run python analyze.py <音檔…>` |

風格（`style`）：`devotion`、`story`、`scifi`、`lounge`、`bazaar`，設定在 `styles.py`。

## 產物寫在哪

`events/`、`plans/`、`outputs/` 都建在「工作資料夾」底下，不會寫進這個倉庫：

1. `--work <資料夾>`（`score.py` 放在子命令前面：`score.py --work <資料夾> make …`）
2. 環境變數 `S2F_SCORE_WORK`
3. 預設：`adapters/doc_arc.py` 用該集資料夾的 `score/`（`doc.json` 旁邊）；`score.py`、`compose.py` 用執行時所在資料夾的 `score_out/`

## 測試

```
cd tools/score && uv run python -m pytest -q
```
