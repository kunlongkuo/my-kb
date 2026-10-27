# 蝦皮短影音視覺排版、字幕安全區與 Remotion / FFmpeg 規範

> 核心原則：「保留商品展示空間、字幕清晰不擋主體、浮水印防盜且兼顧美感」

---

## 1. 蝦皮短影音視覺安全區（9:16 豎屏，1080 × 1920）

在蝦皮 App 中，短影音四周會被原生介面元素覆蓋：
- **頂部危險區**：頂部 0 ~ 180px（手機狀態列、返回鍵、搜尋列）。
- **右側互動列**：右側 120px 邊界（按讚、評論、分享、旋轉音樂碟片圖示）。
- **底部遮蔽區**：底部 0 ~ 360px（**蝦皮黃色購物車/商品標籤**、創作者頭像、貼文標題與說明文字）。
- **✨ 黃金展示區（商品展示空間）**：Y 軸 220px 至 1350px，這是相機拍攝商品與實體操作的核心視線區。
- **📝 字幕最佳安全帶**：**Y 軸 1380px 至 1550px（畫面下半部約 72% ~ 80% 位置）**。
  - 此高度剛好浮在蝦皮商品標籤上方，同時低於商品操作焦點，兼顧閱讀與商品展示。

```text
+------------------------------------+ (0, 0)
| [X] 頂部避開區 (0 ~ 180px)         |
+------------------------------------+
|                                  | |
|     ✨ 黃金展示空間 (Center)       | |
|     實拍商品操作、特寫、質感展示    | | 右側
|     (220px ~ 1350px)             | | 互動
|                                  | | 按鈕
|                                  | | 區域
+------------------------------------+
| 📝 字幕最佳安全帶 (1380px ~ 1550px) | |
+------------------------------------+
| [X] 蝦皮購物袋、標題、說明 (Bottom)|
+------------------------------------+ (1080, 1920)
```

---

## 2. 帳號浮水印（Watermark）設置規範

- **目的**：宣告版權、建立個人品牌信任度、防止其他賣家盜剪搬運。
- **配置原則**：
  - **位置**：建議放置於 **左上角（Top-Left: x=60px, y=140px）** 或 **右上角偏內側（避開關閉鈕）**。
  - **樣式**：簡潔文字（如 `@GANGLAISHARE`）或微透明 PNG Logo。
  - **透明度**：設定於 **40% ~ 65%**（既清晰可辨，又不搶奪商品注意力）。
  - **大小**：字號 24px ~ 28px，不超過畫面寬度 20%。
  - **禁忌**：絕對不可遮蓋商品的核心商標、按鈕或演示細節。

---

## 3. 字幕排版美學規範

- **字體推薦**：思源黑體（Noto Sans TC Bold / Heavy）、微軟正黑體粗體，避開細字體。
- **單行長度**：**每行 8 至 14 字**。短句更有節奏感，切忌出現三行以上文字塊。
- **顏色搭配**：
  - 方案一（熱門吸睛）：高飽和亮黃色字體（`#FFE814`）+ 黑色描邊（`stroke: 4px #000000`）。
  - 方案二（乾淨高質感）：純白字體（`#FFFFFF`）+ 半透明深色膠囊底色背景（`rgba(0,0,0,0.6)`）。
  - 關鍵字標亮：對於核心賣點詞（如「現折$100」、「一鍵開機」、「Type-C快充」）以強調色（如鮮橘色或青草綠）凸顯。

---

## 4. Remotion 核心排版組件架構範例

若使用 **Remotion** 進行自動化渲染，核心組件架構如下：

```tsx
import { AbsoluteFill, Video, Audio, staticFile } from 'remotion';

export const ShopeeProductVideo: React.FC<{
  videoSrc: string;
  voiceSrc: string;
  bgmSrc: string;
  currentSubtitle: string;
  watermarkText: string;
}> = ({ videoSrc, voiceSrc, bgmSrc, currentSubtitle, watermarkText }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: '#000' }}>
      {/* 1. 實拍商品影片層 (底層) */}
      <Video
        src={videoSrc}
        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
      />

      {/* 2. 帳號浮水印 (左上角安全區) */}
      <div
        style={{
          position: 'absolute',
          top: 130,
          left: 60,
          fontSize: 26,
          fontWeight: 700,
          color: 'rgba(255, 255, 255, 0.65)',
          textShadow: '0 2px 4px rgba(0,0,0,0.5)',
          letterSpacing: 1.2,
        }}
      >
        {watermarkText}
      </div>

      {/* 3. 動態字幕 (位於安全帶 1400px，不遮商品、不被蝦皮購物車遮蓋) */}
      {currentSubtitle && (
        <div
          style={{
            position: 'absolute',
            top: 1420,
            width: '100%',
            display: 'flex',
            justifyContent: 'center',
            padding: '0 40px',
          }}
        >
          <span
            style={{
              backgroundColor: 'rgba(0, 0, 0, 0.72)',
              color: '#FFE814',
              fontSize: 38,
              fontWeight: 800,
              padding: '10px 24px',
              borderRadius: 16,
              textAlign: 'center',
              lineHeight: 1.3,
              boxShadow: '0 4px 12px rgba(0,0,0,0.35)',
            }}
          >
            {currentSubtitle}
          </span>
        </div>
      )}

      {/* 4. 音訊音軌：口播 + 背景音樂 */}
      <Audio src={voiceSrc} volume={1.0} />
      <Audio src={bgmSrc} volume={0.12} />
    </AbsoluteFill>
  );
};
```

---

## 5. FFmpeg 純指令排版方案（無 Remotion 環境時之備援）

若系統未安裝 Node.js / Remotion，可使用 FFmpeg 濾鏡管線直接燒錄浮水印與字幕：

```bash
ffmpeg -y -i raw_product.mp4 -i mixed_audio.mp3 -filter_complex ^
"[0:v]drawtext=text='@MY_SHOPEE_ID':x=60:y=130:fontsize=28:fontcolor=white@0.65:shadowcolor=black:shadowx=2:shadowy=2, ^
 subtitles=subtitles.srt:force_style='FontName=Arial,FontSize=18,PrimaryColour=&H0014E8FF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Alignment=2,MarginV=140'[vout]" ^
-map "[vout]" -map 1:a -c:v libx264 -preset fast -crf 20 -c:a aac -shortest final_shopee_short.mp4
```
