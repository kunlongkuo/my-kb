# tools/h3：MiniMax H3（需要有 Google Colab 帳號）

選用。用 MiniMax H3 做 Optional A 的生成鏡頭和 Optional B 的主持人，生成在你自己 Google 帳號的 Colab GPU 上跑，成品照 VideoExpress、TalkingPhotos 的檔名放回資料夾，剪輯以後的步驟都不用改。

- **主持人**：拿旁白的錄音驅動畫面（鎖音），嘴型跟著錄音走，成品的聲音就是原本的旁白。人物用一張造型圖當參考，動作照提示詞演：可以原地比手勢、邊走邊講，也可以拍成手持自拍的 vlog。
- **生成鏡頭**：純文字生成，或拿一張圖當首格往下演。

## 先讀授權

MiniMax H3 開放權重的授權（MiniMax H3 Community License，2026-08-02）**不涵蓋美國、歐盟、英國、南韓**：在這幾個地方使用、執行、散布權重或它的成品，都不在授權範圍內。公開發布的成品要標示是 AI 生成（YouTube 上傳加 `--synthetic`）。全文：https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/LICENSE

所以這個工具有兩道關：

1. 開工清單多一題 `h3-territory`（這一集有 `h3/manifest.json` 才會問）：你在哪裡、片子在哪裡用。
2. 每次開機先查那台 Colab 機器的所在國家，落在授權地區外就馬上關機、不生成。
   - 先用 IP 查，查不到就隔 20 秒再查，最多三次。
   - 三次都查不到，就看機器網址裡的 Google Cloud 區域。例如 `asia-southeast1` 是新加坡，`asia-northeast3` 是首爾（不在授權地區）。
   - 兩種都判斷不了就關機。連網址都沒有，表示機器根本沒開成功，會直接講明。

## 要什麼

| | |
|---|---|
| 訂閱 | **Google AI Pro**（附 Colab 運算單元，每月約 400 點）。AI Plus 不夠 |
| 上游工具 | [dseditor/h3-colab-skill](https://github.com/dseditor/h3-colab-skill)（MIT）：照它的 `INSTALL_FOR_AGENTS.md` 裝好 `google-colab-cli` 並登入一次。登入由你自己在瀏覽器完成，貼回授權碼 |
| 設定 | `S2F_H3_SKILL_DIR`＝上游的 `h3-multimodal-colab` 資料夾（寫在 `~/.config/script2film/config.json`） |
| 這台電腦 | 不需要顯示卡。模型（約 50 GB）每次開機下載到 Colab 上，不佔這台電腦的空間 |

## 用法

```
python3 skills/ve-director/doc/scripts/doc_host.py split <集>/doc.json --max 15 --min 4      # 主持人：H3 一段最多 15 秒
python3 tools/h3/h3_film.py plan <集>/doc.json --shots --host --look <造型圖> --who "<人物、衣著>" [--where "<地點>"]
python3 tools/h3/h3_film.py run <集>/doc.json --confirmed [--keep 30]
python3 tools/h3/h3_film.py collect <集>/doc.json
python3 skills/ve-director/doc/scripts/doc_host.py join <集>/doc.json
```

- `plan` 寫 `h3/manifest.json`，要用的檔複製到 `h3/inputs/`。
  - **主持人**：每段 `host/parts/partK.mp3` 一個工作，台詞按時間點放進提示詞，可以直接送。要動作就改提示詞：手勢、走動、自拍。
  - **生成鏡頭**：每個 VE 拍一個工作，只有從 `doc.json` 的 `shots` 起的**草稿**。H3 的影片提示詞太短會在畫面上燒字幕，所以要照上游 `references/prompt-guide.md` 改寫成 350–500 個英文字，再刪掉 `"draft"`。放一張 `h3/inputs/shotK.png` 就會拿它當首格。
- `run` 不送的情況：
  - 有草稿沒改寫、影片提示詞不到 300 字、秒數不在 2–15 秒之間。
  - 沒加 `--confirmed`。`--confirmed` 代表使用者看過規格，也同意花點數。
  - 開工清單沒過。要硬送得加 `--skip-checklist "<原因>"`，而且要使用者同意，會記錄下來。
- 做完預設馬上釋放 GPU。`--keep 30` 讓 GPU 再留 30 分鐘，接著送下一批就不用重新下載模型；沒有新工作時，上游的計時器會自己關機。
- `collect`：`h3/out/shotK.mp4` 放到 `ve_<look>/shotK.mp4`，`h3/out/hostK.mp4` 放到 `host/parts/partK.mp4`。舊檔會先改名成 `.bak.mp4` 留著。

## 花費與時間（2026-11-18，L4、480P）

| | 時間 |
|---|---|
| 開機加下載模型 | 4–7 分鐘 |
| 5 秒鏡頭 | 約 3 分鐘 |
| 12 秒鎖音主持人 | 約 3–4 分鐘（720P 約 3.3 分；720P 加 12 步要十幾分鐘） |
| 一整晚試了十幾支 | 約 2 點 |

## 已知

- 鎖音只能用參考模式（`mode: ref`）。首格模式加鎖音會被 ComfyUI 拒絕（`I2VA cannot include reference media`）。
- 上游 `selftest_graph.py --manifest` 不會帶 `drive_audio`，所以鎖音的工作會誤報 BUILD FAILED，真的送出時沒有問題。
- 上游預設的主模型和兩顆常駐 LoRA 是社群做的（合併模型、turbo、MysticXXX），不是 MiniMax 或 Comfy-Org 官方的權重。`plan --model-set official` 會改用 Comfy-Org 的官方權重，但這要上游支援 `model_set` 才有作用（2026-11-18 還沒有）。
- 背景裡的招牌、看板常出現像字又不是字的東西，`collect` 後要看過。
