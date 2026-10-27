# 蝦皮短影音音訊製作與 FFmpeg 混音 SOP

> 核心原則：「口播清晰自然、音樂襯托不喧賓奪主、嚴格把控響度與平衡」

---

## 1. 語音合成（TTS / Fish Audio）規範

在筆記中，語音製作工具以 **Fish Audio** 為代表（或 Edge-TTS / ElevenLabs / 剪映自帶音色）：

1. **音色選擇原則**：
   - 帶貨短影音應選擇「自然、親切、分享型生活好友」音色，避免死板冰冷的機械腔。
   - 科技與 3C 配件：沉穩乾淨、有說服力的青年男女聲。
   - 居家生活與收納好物：溫暖、熱情、生活感強烈的親切嗓音。
2. **語速與語調（Pacing）**：
   - 短影音語速建議設定在 **1.05x ~ 1.20x**，維持俐落明快的節奏，避免沉悶拖沓。
   - 標點符號控制停頓：句子之間保留 0.2s ~ 0.4s 呼吸空隙，讓觀眾容易跟上。

---

## 2. 混音標準與黃金音量比

短影音常見失敗原因之一是「背景音樂太吵，蓋過口播介紹」或「整體聲音太小，滑過直接被忽略」。

### 響度標準：
- **目標綜合響度**：`-14 LUFS` 至 `-16 LUFS`。
- **真峰值限制（True Peak）**：不超過 `-1.0 dBFS`。
- **音軌比例原則**：
  - **人聲口播（Primary Voiceover）**：主導地位（`0 dB` 或目標響度 `-14 LUFS`）。
  - **背景音樂（BGM）**：襯托作用，音量通常下調 **`-18 dB` 至 `-24 dB`**。
  - **開頭/結尾處理**：BGM 開頭 0.5s 淡入（fade-in），結尾 1.0s 淡出（fade-out）。

---

## 3. FFmpeg 自動混音指令（含 Sidechain Ducking 閃避）

### 方案 A：固定比例混音（最穩定常用）
將口播音檔 `voice.mp3` 與背景音樂 `bgm.mp3` 混合，口播維持原音量，BGM 調低至 12%（約 -18dB）：

```bash
ffmpeg -y -i voice.mp3 -i bgm.mp3 -filter_complex ^
"[1:a]volume=0.12,afade=t=in:ss=0:d=0.5,afade=t=out:st=28:d=1.5[bgm]; ^
 [0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2,loudnorm=I=-14:TP=-1.5:LRA=7[aout]" ^
-map "[aout]" mixed_audio.mp3
```

### 方案 B：動態側鏈閃避混音（Sidechain Ducking）
當有人聲口播時，BGM 自動壓低；說完一句停頓時，BGM 柔和浮起：

```bash
ffmpeg -y -i voice.mp3 -i bgm.mp3 -filter_complex ^
"[1:a]volume=0.4[bgm_base]; ^
 [bgm_base][0:a]sidechaincompress=threshold=0.08:ratio=6:attack=50:release=300[ducked_bgm]; ^
 [0:a][ducked_bgm]amix=inputs=2:duration=first[mixed]; ^
 [mixed]loudnorm=I=-14:TP=-1.5:LRA=7[aout]" ^
-map "[aout]" final_mixed_voice.mp3
```

### 方案 C：將混音直接合成到實拍商品無聲影片
將處理好的音軌合成至實拍影像 `product_video.mp4`，維持畫質且長度與音訊完全同步：

```bash
ffmpeg -y -i product_video.mp4 -i final_mixed_voice.mp3 ^
-c:v copy -c:a aac -b:a 192k -shortest output_with_audio.mp4
```
