# tools/qa — 動態檢查與轉錄幻覺守衛

`motion-qa.mjs`：成片逐格檢查。只看「畫面有沒有在變」，不懂內容，把可疑的時間碼列出來，再回去抽那一格看：

- 單幀閃現（分 12×9 格比對前後格）、孤兒格（只有一格長的鏡頭）
- ≥1 秒的靜止段（只列不判）
- 硬切、每秒運動曲線
- 第 0 格是不是空白（封面，只列不擋）
- 選用：`--loop` 檢查首尾接不接得上

## 用法

```
node tools/qa/motion-qa.mjs <video.mp4 | 專案資料夾> [--loop] [--json]
```

給專案資料夾時，取 `output/` 裡版號最大的 `vN.mp4`，沒有才用 `output.mp4`。

退出碼：0＝沒有單幀閃現與孤兒格；1＝有閃現、孤兒格或（`--loop` 時）首尾接不上（是線索，抽那一格看過再判斷）；2＝用法或解碼錯誤。

## 環境

- Node（內建模組即可，不用 `npm install`）
- PATH 上要有 `ffmpeg`、`ffprobe`

## 來源與授權

移植自 [huashu-motion](https://github.com/alchaincyf/huashu-motion) 的 `cli/lib/qa.js`（MIT），門檻與改動寫在檔頭。

## 測試

```
node --test tools/qa/tests/
```

## `hallucination_guard.py`：靜音上冒出來的字

語音轉文字的模型在靜音段會自己補字，最常見的是片尾冒出「謝謝觀看」。這支用 ffmpeg 量靜音（−35 dB、0.6 秒），找出落在靜音上的字幕。

```
python3 tools/qa/hallucination_guard.py --audio <音檔> --srt <字幕.srt> [--apply] [--out <新字幕.srt>]
```

- 整句落在某段靜音裡：列出來，不刪（可能是很小聲的真話）。
- 句子開始在「一路到檔尾的靜音」之後：列出來，加 `--apply` 才刪（沒給 `--out` 會覆寫原字幕檔）。
- 整支量不到靜音（底噪高）時會說這次沒有作用。

字幕來自稿子的流程（doc 模式）不用跑這支：`doc_align.py` 對時的時候自己檢查逐字時間的尾巴，有才印一行，不刪。

測試：`python3 -m pytest tools/qa/tests/test_hallucination_guard.py -q`。
