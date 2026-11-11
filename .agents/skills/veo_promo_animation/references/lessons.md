# 踩過的坑（2026-11 嘉義市成果宣傳動畫）

## 構圖圖（Codex 生圖）
- 插圖一律「不含文字」，中文標題、校名、教案名全部由程式疊字——AI 生圖會寫錯中文。
- 台灣城市一定加「low-rise only, NO skyscrapers, NO Taipei 101」：第一輪 10 張有 7 張冒出台北 101。修正用 `--edit` 把原圖當底圖，只換背景。
- 第一張沒寫臉部要求 → 人物沒有五官；風格段要寫「simple cute faces: dot eyes and gentle smiles」。
- 不要叫它「下方 1/3 留白」——會畫出一大塊空白米色區；改成「下方 20% 較素的區域，仍是插畫」。
- 先拼成總覽圖（ffmpeg xstack）一次審 10 張，比逐張讀省很多 token。

## Veo
- 使用者要的是「會動的動畫」，不是圖片輪播＋推拉。人物場景一律圖生影片；數字／名單類鏡頭也用 Veo 讓背景動，資訊用程式疊。
- 要疊標籤對位的鏡頭，提示詞寫「locked-off static camera … stay exactly in place」，Veo 會乖乖不動。
- 推鏡鏡頭：畫面下方在後段會被人物塞滿，標題放上方；先看實際 Veo 影片的頭／中／尾三格再定位置。
- Flow 的 Veo 推鏡太猛時會「長出」高樓、換掉人物 → 改「nearly static camera … do not add any new buildings / people」重生。
- Flow Veo 3.1 Fast 8 秒、Gemini 版約 10 秒。旁白較長的鏡要放慢：K≤1.15 直接複製畫格；1.15～1.5 用 framerate 混合；動作很快（揮手、大聲公）的鏡改 `interp: dup`，否則有殘影。
- **不要用 minterpolate mci**：插畫人物臉會糊成一團色塊。
- Veo 原片本身也會有 1～2 格動態模糊或小變形，回報給使用者，由使用者決定是否重生。

## 旁白與字幕
- 配音先試聽 1～2 句，使用者確認聲線後才批次生成。
- 字幕不要按字數平均分配時間，先跑 `voice_timing.py` 取得語音段落，用 `voice_caption()` 貼齊停頓。
- 字幕文字可以和旁白不同：旁白念「一百一十五年」，字幕顯示「115 年」。
- 標籤出場時間對準旁白念到該校的語音段起點（`VOICE[n]["segs"][i][0] + delay`）。
- 每鏡片長 = delay + 旁白長 + 約 0.6 秒；assemble `--dry-run` 會列出 voice_gaps，負數表示旁白重疊。

## 轉場與音樂
- 每鏡頭尾都放 GoldSweep 金色光帶；串接時在光帶最亮處 xfade 0.3 秒，看起來就是光帶把下一鏡帶進來。
- 背景音樂比片長短時，assemble 會把前段 0–62 秒接上「從 Y 秒到結尾」的後段，交叉淡化 4 秒，讓音樂的自然結尾剛好落在片尾。
- loudnorm -15 LUFS、TP -1.5；旁白時 sidechain 壓低音樂。

## 交付
- 完整版 CRF 19（約 130MB/110 秒）、社群版 CRF 23 maxrate 6M（約 70MB）。
- 遠端／手機檢視上限 30MB：另壓 720p 1.8Mbps 預覽版（約 26MB）再用 SendUserFile 傳。
- 舊版本影片改名保留，不要自動刪除，請使用者自行決定。
