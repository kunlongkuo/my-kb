# tools/music3：MiniMax Music 3（需要有 Google Colab 帳號）

選用。用 MiniMax Music 3 生成一首有歌詞的歌或一段純配樂，生成在你自己 Google 帳號的 Colab GPU 上跑。做好的 WAV 照 Optional C 的方式當成片的背景音樂（`doc.json` 的 `bgm.src`）。

兩種用法：agent 用 `music3_film.py` 從這台電腦遙控 Colab（和 `tools/h3` 用同一個 colab-cli 登入），或你自己在 Colab 開 notebook 貼程式。

## 先讀授權

MiniMax-Music3 Community License（MIT 式）**沒有地區限制**。要遵守的：

- 保留版權聲明，遵守使用政策。公開發布的成品要標示是 AI 生成（YouTube 上傳加 `--synthetic`）。
- 歌詞的著作權要是你的。別人的詩歌、歌詞不能拿來生成。
- 年營收超過 2,000 萬美元要另外取得授權；把它包成服務給別人用，要有防濫用機制。

全文：https://huggingface.co/MiniMaxAI/MiniMax-Music3

## 要什麼

| | |
|---|---|
| 訂閱 | **Google AI Pro**（附 Colab 運算單元） |
| 執行階段 | L4（24 GB，程式會自動開 CPU offload）或 A100 |
| 這台電腦 | 不需要顯示卡。模型每次開機下載到 Colab 上 |

## 用法（agent，從這台電腦）

```
python3 tools/music3/music3_film.py plan <集> --caption-file caption.txt [--lyrics-file lyrics.txt] [--seconds 240] [--seed 7]
python3 tools/music3/music3_film.py run <集> --confirmed [--gpu L4]
python3 tools/music3/music3_film.py collect <集>
```

- `plan` 寫 `music3/job.json`。不給 `--lyrics-file` 就是純配樂，長度預設等於旁白長度（`tts/lines.json` 最後一句結束再加 3 秒）；有歌詞要自己給 `--seconds`。`--seconds` 是**上限**：歌詞唱完，模型就會自己收尾（實測給 240 秒，整首唱完、淡出，只用了 168 秒）。曲風描述（caption）少於 25 個英文字不收。
- `run` 開一台 Colab GPU、在機器上背景生成、下載 `music3/out/song.wav`（純配樂是 `bgm.wav`），不論成功失敗都會關機。沒加 `--confirmed` 不開機；同名的機器還開著也不開第二台。
- `collect` 把 WAV 複製成 `<集>/music3_bgm.wav`（舊檔留成 `.bak.wav`），`doc.json` 的 `bgm.src`、`bgm.credit` 填好，其他 `bgm` 設定不動。

## 用法（自己在 Colab notebook）

在 Colab 新增 notebook，執行階段選 L4 或 A100，依序執行：

```python
!pip install -q git+https://github.com/huggingface/diffusers transformers accelerate soundfile
```

```python
import torch, numpy as np, soundfile as sf
from diffusers import ModularPipeline, ComponentsManager

if torch.cuda.get_device_properties(0).total_memory < 40e9:      # L4：模型分批放進顯示卡
    manager = ComponentsManager(); manager.enable_auto_cpu_offload(device="cuda")
    pipe = ModularPipeline.from_pretrained("MiniMaxAI/MiniMax-Music3", components_manager=manager)
    pipe.load_components(dtype=torch.bfloat16)
else:
    pipe = ModularPipeline.from_pretrained("MiniMaxAI/MiniMax-Music3")
    pipe.load_components(dtype=torch.bfloat16); pipe.to("cuda")
```

```python
LYRICS = "[Intro]\n[Instrumental]\n\n[Verse]\n（你的歌詞）\n\n[Chorus]\n（你的歌詞）\n"
CAPTION = ("Global Metadata: ...（曲風、速度、情緒）\n\n"
           "Vocal Details: ...（人聲；純配樂就寫 No vocals at all）\n\n"
           "Arrangement: ...（每一段用什麼樂器、怎麼起伏）")
audio = pipe(prompt=CAPTION, lyrics=LYRICS, audio_duration=60.0,
             generator=torch.Generator("cuda").manual_seed(7), output="audios")[0]
wav = audio.T.detach().cpu().float().numpy() if torch.is_tensor(audio) else np.asarray(audio).T
sf.write("/content/song.wav", wav, pipe.sampling_rate)
```

- 歌詞用 `[Verse]`、`[Chorus]`、`[Bridge]`、`[Instrumental]` 這類段落標記。純配樂只放 `[Instrumental]`。
- `CAPTION` 分三段寫：整體（曲風、BPM、情緒）、人聲、編曲。寫得越具體越好控制。
- 做完從左邊的檔案欄把 `song.wav` 下載回來，然後**到「執行階段」選「中斷連線並刪除執行階段」**，不然會一直扣運算單元。

## 接回片子

把 WAV 放進片的資料夾，`doc.json` 的 `bgm.src` 指向它，`bgm.credit` 寫「MiniMax Music 3（AI 生成）」。其他步驟見 `docs/FLOW.md` 的 Optional C。

## 花費與時間（2026-11-18，L4）

| | |
|---|---|
| 裝套件、下載並載入模型 | 約 4 分鐘（載入 103 秒） |
| 60 秒的歌 | 約 5 分鐘（每秒音樂約 5 秒），顯示卡記憶體峰值 19.4 GB |
| 一首完整的歌（給 240 秒，實際 168 秒） | 生成約 12 分鐘；開機到關機約 17 分鐘，約 0.4 點 |
| 一次開機、生成一首 60 秒 | 約 0.3–0.5 點 |

輸出是 44.1 kHz 立體聲 WAV。

## 已知

- 台語歌詞唱得出來，但要能用還得多試幾個 seed、改寫 `CAPTION`。第一次就能用的機率不高。
- Mac 本機（MPS）還沒有成熟的跑法，2026-11-18 不建議。
- **曲風描述寫了 choir（合唱）就會唱出人聲**，即使同時寫了 No vocals、歌詞全是 `[Instrumental]`（2026-11-19：62 秒的史詩配樂，第 23–51 秒變成人聲段）。純配樂不要寫 choir。
- 那首實際只出 52.3 秒（給 62 秒）：純配樂也可能提早收尾，`--seconds` 要比片子需要的多留 10 秒以上。
- 事後用 demucs 去人聲不划算：人聲段去掉後幾乎無聲（每秒響度 -40 到 -65），只能拿器樂段重排。

### 曲風描述範例：史詩預告片配樂（2026-11-19，使用者評「比較好」；已拿掉會引出人聲的 choir）

```
Global Metadata: Epic orchestral trailer score, cinematic Hollywood action, 128 BPM, D minor, heroic, majestic and grandiose, building tension with triumphant brass climaxes, wide and powerful, driving momentum throughout.

Vocal Details: No vocals at all, instrumental only, no lyrics, no singing, no spoken words.

Arrangement: Opens with a bold low brass and string hit and a short heroic French horn call. Then fast driving staccato string ostinato with taiko and big orchestral percussion accents (not a constant kick drum), the horns playing a soaring heroic melody. Around twenty seconds a triumphant full brass fanfare with trumpets. A slightly lighter, confident, playful middle passage with pizzicato strings and woodwinds. Then the strings rebuild with rising tension, brass stabs and timpani rolls, growing into a massive final climax with trumpets carrying the main melody, crashing cymbals and huge drums, ending on a powerful sustained chord.
```
