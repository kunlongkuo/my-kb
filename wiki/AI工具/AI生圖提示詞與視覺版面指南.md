---
title: AI生圖提示詞與視覺版面指南
category: CONCEPT
tags: [AI繪圖, Prompt, 提示詞, ChatGPT]
sources: [raw/圖片提示詞/高處老建築・雕刻圖騰高訂.md, raw/圖片提示詞/生圖提示詞範例.xlsx, cards/AI繪圖與提示詞庫解析.md]
status: verified
updated: 2026-07-11
---

# AI生圖提示詞與視覺版面指南

本指南系統化整理了 AI 生圖（以 Midjourney、ChatGPT DALL-E 3 / Image 2.0 等為主）的底層提示詞（Prompt）架構、畫面高級感控制字典，以及具備高度設計感的社群排版與人像生圖實戰指南。

---

## 一、Prompt 結構化設計 (Prompt Architecture)

撰寫高精度、高遵循度的 AI 生圖指令，應遵循 **6 大核心維度** 的積木式結構。權重通常由前往後遞減：

```
Prompt = [主體] + [風格與媒介] + [構圖與鏡頭] + [光影] + [氛圍] + [細節與限制/參數]
```

1. **主體 (Subject)**：畫面的絕對核心（如�6. **細節與參數 (Details & Parameters)**：畫面長寬比與模型參數（如：`--ar 16:9`, `--style raw`）。

![Prompt 結構與中英文公式範例](file:///I:/Mark/my-kb/raw/assets/圖片提示詞/全功能模板.jpeg)

### 中英文全功能萬能模板
> **中**：`[主體描述，包含動作與表情]，[背景場景細節]，[媒介與藝術風格]，[構圖與鏡頭視角]，[主要光影方向與色調]，[畫面整體情緒氛圍]，[比例與渲染參數]`
> **英**：`[Subject details], [Background scene], [Medium and artistic style], [Composition & Camera lens], [Lighting & Color palette], [Atmosphere & Mood], [Aspect ratio and parameters]`

---

## 二、高級感視覺控制字典 (Quiet Luxury Design Codes)

避免生圖結果流於「平淡」或「證件照感」，需在提示詞中加入以下進階視覺控制碼：

| 控制維度 | 視覺設定值 | 提示詞關鍵字與效果 |
| :--- | :--- | :--- |
| **統一色調** | **日系療癒** | `warm brown, gray blue, creamy white` (暖棕＋灰藍＋米白) |
| | **港式復古** | `warm yellow, red-green, deep brown` (暖黃＋紅綠＋深棕) |
| | **清新文青** | `Morandi pink, mist gray, butter white` (莫蘭迪粉＋霧灰＋奶油白) |
| **立體光影** | **柔和逆光** | `soft backlight, glowing rim light` (邊緣產生暖光暈，增加空氣感) |
| | **45度側光** | `45-degree key light, chiaroscuro` (經典肖像光，突顯材質與五官立體度) |
| | **斑駁樹影** | `dappled shadows, leaf shadows filtering through` (光影錯落，營造生動生活感) |
| **留白呼吸感** | **排版優先** | `minimalist clean background, copy space, layout priority` (為標題與文字留白) |
| | **大光圈虛化** | `shallow depth of field, creamy bokeh` (背景朦朧，焦點完全鎖定於主體) |

---

## 三、15 大商業與創作 Prompt 實戰字典

在 ChatGPT DALL-E 3 或 Image 2.0 中，可直接套用以下英文提示詞模板來獲得專業級圖像：

1. **極致商業產品攝影**
   > `ultra realistic commercial photography, product placed at the center of high-end studio space, professional 45-degree key light and rim light, highly detailed texture, international brand advertising style, 16:9`
2. **商品 Mockup (包裝展示)**
   > `cinematic product mockup, packaging floating in a futuristic showroom, mirror floor reflection, circular light ring, Apple keynote style, 16:9`
3. **生活化產品情境**
   > `cinematic lifestyle photography, product naturally integrated into real-life scene, soft window light, table with subtle life marks, 16:9`
4. **超寫實時間凍結**
   > `ultra realistic frozen moment, liquid splash, water droplets, and fragments floating in mid-air, light refraction, high-speed shutter, 16:9`
5. **品牌世界觀**
   > `cinematic worldbuilding, futuristic luxury space, brand visual identity, UI, characters, and products integrated with high consistency, 16:9`
6. **室內空間設計**
   > `cinematic interior design, modern high-end interior, natural light, precise space scale, Netflix documentary style, 16:9`
7. **一致性角色設計**
   > `cinematic character consistency, same character in different scenes and actions, keeping fixed hairstyle, color palette, proportions, and facial features, 16:9`
8. **個人形象照**
   > `cinematic portrait photography, ultra-realistic personal portrait, cinematic studio lighting, natural background, professional and confident look, Netflix documentary style, 16:9`
9. **髮型/造型變換**
   > `high-end hairstyle transformation, keeping facial features identical, changing only hairstyle and color to present different styles and outfits, 16:9`
10. **資訊圖表 UI**
    > `modern infographic UI design, complex data converted into high-end infographics, clean UI structure, tech-style layout, Apple keynote style, 16:9`
11. **極簡科技 UI**
    > `futuristic UI design, minimalist high-end tech UI interface, glassmorphism, clear information hierarchy, Apple/Tesla system-like interface, 16:9`
12. **新聞紀錄片感**
    > `cinematic documentary realism, ultra-realistic news report scene, live reporter, CNN/Netflix documentary atmosphere, natural light, 16:9`
13. **疲憊/崩潰上班族**
    > `office burnout realism, office late at night with only one person, cold white screen light illuminating tired face, messy desk, empty coffee cups, 16:9`
14. **未來科幻世界觀**
    > `cinematic future worldbuilding, hyper-giant future city where humans and AI co-exist naturally, Blade Runner style mixed with Apple concept design, 16:9`
15. **創作者工作流**
    > `cinematic creative workflow, modern high-end AI creator studio, multiple generation results floating in space, brand designs, storyboards, and infographics, 16:9`

---

## 四、經典社群排版與特定風格指南 (Special Layouts)

### 1. 3D 樹脂微縮天氣卡 (Resin 3D Weather Card)
*   **視覺特色**：呈現滴膠樹脂（Resin）的平滑與拋光反光亮面（Glossy），帶有微凸起與柔和陰影（soft drop shadows）。
*   **架構公式**：
    > `主題：[城市名稱] 3D樹脂微縮 氣象圖。風格：超寫實 3D 樹脂質感，拋光亮面處理，立體微縮模型感，可愛療癒，色彩鮮明。前景：樹脂材質的旅遊小人、交通工具與在地美食。中景：大型立體氣象牌，上面有浮凸亮面字體顯示氣象資訊（城市、日期、溫度、降雨機率）。背景：該城市的地標建築與街道景觀。直式海報比例，強烈立體層次。`

![3D 樹脂微縮天氣卡範例](file:///I:/Mark/my-kb/raw/assets/圖片提示詞/樹脂天氣_1.jpeg)

### 2. 韓風手帳紙質旅遊手記 (Morandi Paper Journal)
*   **視覺特色**：奶油白（Creamy white）紙張底色，極簡、留白且具備「呼吸感」，使用低飽和度莫蘭迪色系。
*   **架構公式**：
    > `一個高質感的韓系美學旅遊手記頁面，背景材質為有質感的奶油白紙張。全面使用低飽和莫蘭迪色（乾燥玫瑰粉、鼠尾草綠、迷霧藍、奶油黃）。頂部為手寫風格字體（繁體中文/英文）的旅遊主題。中央為手繪風視覺行程時間軸（使用數字 1, 2, 3 圓形標號）。景點文字呈現細字水性筆的手寫註記，並用類似螢光筆的半透明色塊強調，旁穿插極簡線條的景點與美食插圖。`

![韓風手帳紙質旅遊手記範例](file:///I:/Mark/my-kb/raw/assets/圖片提示詞/奶油紙旅遊_1.jpeg)

### 3. 雙重曝光側臉剪影史詩海報 (Double Exposure Silhouette)
*   **視覺特色**：以人物巨大的優雅側臉剪影作為外輪廓，內部填充敘事性場景，大面積留白。
*   **架構公式**：
    > `根據上傳照片（或指定主題），產生一張收藏版史詩海報：以人物巨大優雅的側臉剪影作為外輪廓。剪影內部自動生長出與 [主題] 緊密契合的完整世界觀、標誌性場景、象徵符號與氛圍。剪影外部大面積留白，背景具備紙張顆粒質感、邊緣白與刷痕。柔和空氣透視，輕霧化過度，整體呈現電影海報與夢幻水彩插畫融合風格，版式克制高級。`

![雙重曝光側臉剪影範例](file:///I:/Mark/my-kb/raw/assets/圖片提示詞/側臉剪影圖片_1.png)

### 4. 3D Pop-out 社群肖像 (人物衝出手機)
*   **視覺特色**：利用低角度廣角與誇張的近大遠小透視，讓人物的一部分（如手、腳）「突破」並衝出手機螢幕。
*   **架構公式**：
    > `請參考上傳照片中的人物，保持面貌五官與髮型一致，生成一張 3D pop-out social media portrait poster。主角站在巨大智慧型手機畫面中，人物以強烈透視構圖從手機裡「突破而出」，手或腳跨出畫面，營造超強景深與 3D 立體衝擊感。手機介面為原創社群 UI（有帳號名稱、追蹤數、粉色按鈕）。背景為精緻裝飾的房間或公園，帶有漂浮的多彩氣球、飛舞泡泡與玻璃碎裂特效。明亮飽和的馬卡龍色系，高級商業攝影打光，低角度廣角鏡頭。`

![3D Pop-out 人物衝出手機範例](file:///I:/Mark/my-kb/raw/assets/圖片提示詞/人物衝出手機_1.jpeg)

### 5. 時尚高訂與古老建築雕刻的交融 (Architectural Couture)
*   **視覺特色**：將古老建築的雕刻圖騰、斑駁歲月痕跡與高級時裝的立體輪廓融合，展現安靜、冷感、怪美的 SURREALISM（超現實主義）氛圍。
*   **架構公式**：
    > `一位女性安靜坐在老城市高處老建築外牆的狹窄石窗沿上。右側是近距離、斑駁厚重的老式石牆、細長窗框與黑色鑄鐵欄杆，展現歲月磨損、裂紋與褪色質感。左側背景是遙遠、朦朧的灰金色城市天際線，天空位於陰天與暮色之間，帶有真實空氣透視與景深。女性身穿修長貼身的高訂禮服，材質為高級啞光面料，表面具有像古老建築雕刻般細膩的浮雕、幾何邊飾與植物雕紋。髮型為側分的雕塑感短鮑伯髮型，搭配簡潔尖頭高跟短靴。35mm film still，低飽和礦物色調，超寫實電影級高訂時尚攝影，architectural couture，quiet surrealism。`�氣卡 (Resin 3D Weather Card)
*   **視覺特色**：呈現滴膠樹脂（Resin）的平滑與拋光反光亮面（Glossy），帶有微凸起與柔和陰影（soft drop shadows）。
*   **架構公式**：
    > `主題：[城市名稱] 3D樹脂微縮 氣象圖。風格：超寫實 3D 樹脂質感，拋光亮面處理，立體微縮模型感，可愛療癒，色彩鮮明。前景：樹脂材質的旅遊小人、交通工具與在地美食。中景：大型立體氣象牌，上面有浮凸亮面字體顯示氣象資訊（城市、日期、溫度、降雨機率）。背景：該城市的地標建築與街道景觀。直式海報比例，強烈立體層次。`

### 2. 韓風手帳紙質旅遊手記 (Morandi Paper Journal)
*   **視覺特色**：奶油白（Creamy white）紙張底色，極簡、留白且具備「呼吸感」，使用低飽和度莫蘭迪色系。
*   **架構公式**：
    > `一個高質感的韓系美學旅遊手記頁面，背景材質為有質感的奶油白紙張。全面使用低飽和莫蘭迪色（乾燥玫瑰粉、鼠尾草綠、迷霧藍、奶油黃）。頂部為手寫風格字體（繁體中文/英文）的旅遊主題。中央為手繪風視覺行程時間軸（使用數字 1, 2, 3 圓形標號）。景點文字呈現細字水性筆的手寫註記，並用類似螢光筆的半透明色塊強調，旁穿插極簡線條的景點與美食插圖。`

### 3. 雙重曝光側臉剪影史詩海報 (Double Exposure Silhouette)
*   **視覺特色**：以人物巨大的優雅側臉剪影作為外輪廓，內部填充敘事性場景，大面積留白。
*   **架構公式**：
    > `根據上傳照片（或指定主題），產生一張收藏版史詩海報：以人物巨大優雅的側臉剪影作為外輪廓。剪影內部自動生長出與 [主題] 緊密契合的完整世界觀、標誌性場景、象徵符號與氛圍。剪影外部大面積留白，背景具備紙張顆粒質感、邊緣白與刷痕。柔和空氣透視，輕霧化過度，整體呈現電影海報與夢幻水彩插畫融合風格，版式克制高級。`

### 4. 3D Pop-out 社群肖像 (人物衝出手機)
*   **視覺特色**：利用低角度廣角與誇張的近大遠小透視，讓人物的一部分（如手、腳）「突破」並衝出手機螢幕。
*   **架構公式**：
    > `請參考上傳照片中的人物，保持面貌五官與髮型一致，生成一張 3D pop-out social media portrait poster。主角站在巨大智慧型手機畫面中，人物以強烈透視構圖從手機裡「突破而出」，手或腳跨出畫面，營造超強景深與 3D 立體衝擊感。手機介面為原創社群 UI（有帳號名稱、追蹤數、粉色按鈕）。背景為精緻裝飾的房間或公園，帶有漂浮的多彩氣球、飛舞泡泡與玻璃碎裂特效。明亮飽和的馬卡龍色系，高級商業攝影打光，低角度廣角鏡頭。`

### 5. 時尚高訂與古老建築雕刻的交融 (Architectural Couture)
*   **視覺特色**：將古老建築的雕刻圖騰、斑駁歲月痕跡與高級時裝的立體輪廓融合，展現安靜、冷感、怪美的 SURREALISM（超現實主義）氛圍。
*   **架構公式**：
    > `一位女性安靜坐在老城市高處老建築外牆的狹窄石窗沿上。右側是近距離、斑駁厚重的老式石牆、細長窗框與黑色鑄鐵欄杆，展現歲月磨損、裂紋與褪色質感。左側背景是遙遠、朦朧的灰金色城市天際線，天空位於陰天與暮色之間，帶有真實空氣透視與景深。女性身穿修長貼身的高訂禮服，材質為高級啞光面料，表面具有像古老建築雕刻般細膩的浮雕、幾何邊飾與植物雕紋。髮型為側分的雕塑感短鮑伯髮型，搭配簡潔尖頭高跟短靴。35mm film still，低飽和礦物色調，超寫實電影級高訂時尚攝影，architectural couture，quiet surrealism。`

---

## 五、引用文獻 [Ref]

*   **[Ref 1]** [高處老建築・雕刻圖騰高訂.md](file:///I:/Mark/my-kb/raw/圖片提示詞/高處老建築・雕刻圖騰高訂.md) — 探討了將建築雕刻紋理與時尚禮服在電影級人像生圖中相結合的詳細設計細節與參數設定。
*   **[Ref 2]** [生圖提示詞範例.xlsx](file:///I:/Mark/my-kb/raw/圖片提示詞/生圖提示詞範例.xlsx) — 提供全功能模板、讓畫面高級的 3 大要素，以及 15 種 ChatGPT DALL-E 3 實戰生圖指令與多種社群排版風格的 Excel 案例資料庫。
