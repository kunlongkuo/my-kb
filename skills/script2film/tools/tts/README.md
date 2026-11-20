# tools/tts — 聲音比對與角色配音

`speaker_sim.py`：語者相似度。拿一段確定是本人的錄音當基準，量每個候選音檔（例如克隆聲音產出的配音）像不像，印出每個候選的相似度分數（ECAPA 聲紋，speechbrain 的 `speechbrain/spkrec-ecapa-voxceleb` 模型）。同一人不同句約 0.8–0.9，不同人多在 0.4 以下。

## 用法

```
<有 speechbrain 的 Python> tools/tts/speaker_sim.py <基準.wav> <候選.wav|資料夾>...
```

給資料夾時量裡面的 `.wav`。每個候選印一行「分數  檔名」。

## 環境

- Python 套件：`speechbrain`、`torch`、`torchaudio`、`soundfile`。
- 第一次跑會下載聲紋模型。快取位置用環境變數 `S2F_SPEECHBRAIN_CACHE` 指定，沒設用 `~/.cache/script2film/speechbrain-ecapa`。

## 讀音表

`lexicon.json` 是所有系列共用的讀音表：產旁白之前（`doc_tts.py`，以及旁白快取的鍵）自動把會唸錯的字換掉，字幕不受影響。

- 加一條：在 `rules` 加 `{"from", "to", "lang", "note"}`。整個詞的規則放在單字規則上面；`note` 寫哪一天聽到、聽成什麼。
- 機器抓不到沒進表的多音字（辨識檢查把多音字當成唸對），只能靠人聽。聽出一個就加一條，這是這張表唯一的來源。
- 每集稿子自己的 `tts` 欄位（`make_doc.py` 的 `TTS_FIX`）只放那一集才有的唸法，例如阿拉伯數字改成國字；讀音表會再套在它上面，所以繞不過。
- `python3 tools/tts/lexicon.py <集>/doc.json` 列出這一集「Swapped by the pronunciation table」與「Changed in this episode」兩段；後者若是通用的字，搬進讀音表。
- 同一段文字套幾次結果都一樣（`to` 裡包含 `from` 的規則也是，例如加引號）。
- 測試：`python3 -m pytest tools/tts/tests -q`。

## 角色配音（Qwen3-TTS）

給有好幾個角色的片用：每個角色先設計一次聲音，之後每句都照那段參考音克隆，同一個角色才不會每句變一個人。

```
export S2F_QWEN_TTS_MODELS=<放 Qwen3-TTS 模型的資料夾>     # 底下要有 Qwen3-TTS-12Hz-1.7B-VoiceDesign、Qwen3-TTS-12Hz-1.7B-Base
. tools/tts/env.sh                                          # 設定模型快取位置；沒設上面那個變數會停下
PY=python3                                                  # 任何 python3 都行：沒有 qwen_tts 時這三支會自己改用 $S2F_QWEN_TTS_DIR/.venv/bin/python
$PY tools/tts/design_voices.py <cast.json> <參考音資料夾>/              # 每個角色設計一次：<角色>.wav ＋ <角色>.txt
$PY tools/tts/clone_lines.py <cast.json> <參考音資料夾> <輸出資料夾> [--n 3]   # 每句照參考音克隆，出 n 個候選
$PY tools/tts/speak_lines.py <cast.json> <輸出資料夾> [--n 3]            # 不克隆、直接唸（只適合試聽單句）
```

`cast.json`：`{"voices": {"<角色>": {"instruct": "聲音描述", "ref_text": "參考句", "seed": 7}}, "lines": [{"speaker": "<角色>", "text": "台詞"}]}`。`design_voices.py` 另外讀每個角色的 `"lang"`：`"zh"`（不寫就是它）或 `"en"`；英文角色的描述與參考句用英文寫。模型不隨倉庫附。旁白（單一聲音）走 `skills/ve-director/doc/scripts/doc_tts.py`，不用這三支。
