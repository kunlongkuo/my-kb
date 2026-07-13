# Literature Note: AI 繪圖與生圖提示詞庫解析

- **來源原始檔**：
  - [高處老建築・雕刻圖騰高訂.md](file:///I:/Mark/my-kb/raw/圖片提示詞/高處老建築・雕刻圖騰高訂.md)
  - [生圖提示詞範例.xlsx](file:///I:/Mark/my-kb/raw/圖片提示詞/生圖提示詞範例.xlsx)
- **Ingest 日期**：2026-07-11

---

## 核心摘要與觀點

此筆記收錄了 AI 生圖（特別是基於 Midjourney、ChatGPT DALL-E 3 / Image 2.0 等多模態模型）的核心提示詞架構、高級感控制視覺參數，以及一系列兼具實用性、藝術性與社群分享價值的範例 Prompt。

1. **結構化詠唱 (Structured Prompting)**：一個高質量的圖像 Prompt 通常由 6 大核心元素（主體、風格、構圖、光影、氛圍、限制）組成。透過結構化的分區撰寫（使用括號或 JSON 鍵值），能大幅提升模型對細節的遵循能力。
2. **高級感的關鍵 (Quiet Luxury in Design)**：高級的畫面不需要繁雜的指令堆砌，而在於**色調統一**（限制主色）、**光影具層次**（明確光的方向與質地）與**背景留白**（為文字或主體預留「呼吸感」）。
3. **一致性與臉部鎖定 (Identity & Style Matching)**：在 Image-to-Image (圖生圖) 情境下，以特定人物照片為唯一身份參考，要求模型「保留骨相、特徵與年齡感」，並將其置於不同的時尚、角色或年紀變化的視覺版面中（如眼鏡適配、人生分岔海報、3D Pop-out 社群圖卡）。

---

## 原始文獻精華收錄

### 1. 高處老建築・雕刻圖騰高訂時尚攝影

這是一個極致追求電影質感與高級時裝細節的 4:5 直式 Prompts，適用於高端人像生圖。

*   **主體與臉部鎖定**：以參考照片中的女性為唯一來源，保留臉型骨相、五官比例、真實年齡感與自然氣質。
*   **構圖與場景**：人物坐於畫面中右側老城市高處老建築外牆的狹窄石窗沿上。右側為斑駁厚重老石牆、細長窗框與鑄鐵欄杆，左側為遙遠朦朧的灰金色城市天際線。人物佔比約 70%，全身與鞋子完整入鏡。
*   **光影與色調**：柔和自然光、細微顆粒、低飽和礦物色調、真實空氣透視。陰天與暮色間的灰金色。
*   **禮服設計**：修長貼合身形，適合坐姿。使用舊象牙色、石灰米色、風化砂岩色之啞光面料（絲質嘎巴甸、立體提花等）。表面具有抽象拱形節奏、植物雕紋、幾何邊飾等仿古建築刻痕紋理。
*   **髮型與鞋子**：側分雕塑感短鮑伯髮型，柔霧亞麻金棕色。搭配同色系尖頭高跟短靴（霧面皮革，簡潔線條）。
*   **最終 Prompt (中/英文參考)**：
    > **中文描述**：`生圖提示詞：一位女性安靜坐在老城市高處建築外牆的狹窄石窗沿上，右側是近距離、斑駁厚重的老式石牆、細長窗框與黑色鑄鐵欄杆；左側向外展開遙遠、朦朧的灰金色城市天際線，安靜、冷感、怪美、成熟、精緻。女性身穿修長高訂禮服，顏色以舊象牙色、石灰米色、礦物灰米色、風化砂岩色為主，材質為啞光面料，表面具有細膩的浮雕、壓印與古老建築雕刻圖騰紋樣。側分雕塑感短鮑伯髮型，搭配尖頭高跟短靴。35mm film still，柔和自然光，細微顆粒，低飽和礦物色調，超寫實電影級高訂時尚攝影，architectural couture，quiet surrealism，high fashion realism。`

---

### 2. 生圖提示詞範例.xlsx 精華提煉

#### 💡 提示詞的 6 大核心解剖
1.  **主體 (Subject)**：畫面的絕對核心。
2.  **風格與媒介 (Style & Medium)**：如 `35mm film still`, `oil painting`, `clay illustration`。
3.  **構圖 (Composition)**：視角與鏡頭，如 `low angle shot`, `macro shot`。
4.  **光影 (Lighting)**：光線質地，如 `soft natural light`, `cinematic backlight`。
5.  **氛圍 (Mood)**：情緒基調，如 `quiet`, `dreamy`, `burnout`。
6.  **細節與限制 (Details & Negative)**：限制元素與比例，如 `--ar 16:9`。

#### 🎨 讓畫面瞬間高級的 3 大進階要素
*   **色調統一**：
    *   【日系療癒】→ 暖棕＋灰藍＋米白
    *   【港式復古】→ 暖黃＋紅綠＋深棕
    *   【清新文青】→ 莫蘭迪粉＋霧灰＋奶油白
*   **光影層次**：避免死板的證件照平光。使用【柔和逆光】（邊緣光暈）、【45度側光】（立體感）或【斑駁樹影】。
*   **背景會呼吸**：使用【排版優先】（為標題留白）、【大光圈虛化】（突出主體）或【純淨極簡背景】。

#### 🛠️ ChatGPT Image 2.0 實戰 15 大 Prompt
1.  **極致商業產品攝影**：`ultra realistic commercial photography, product placed at the center of high-end studio space, professional 45-degree key light and rim light, highly detailed texture, international brand advertising style, 16:9`
2.  **商品 Mockup**：`cinematic product mockup, packaging floating in a futuristic showroom, mirror floor reflection, circular light ring, Apple keynote style, 16:9`
3.  **生活化產品情境**：`cinematic lifestyle photography, product naturally integrated into real-life scene, soft window light, table with subtle life marks, 16:9`
4.  **超寫實時間凍結**：`ultra realistic frozen moment, liquid splash, water droplets, and fragments floating in mid-air, light refraction, high-speed shutter, 16:9`
5.  **品牌世界觀**：`cinematic worldbuilding, futuristic luxury space, brand visual identity, UI, characters, and products integrated with high consistency, 16:9`
6.  **空間設計**：`cinematic interior design, modern high-end interior, natural light, precise space scale, Netflix documentary style, 16:9`
7.  **一致性角色**：`cinematic character consistency, same character in different scenes and actions, keeping fixed hairstyle, color palette, proportions, and facial features, 16:9`
8.  **個人形象照**：`cinematic portrait photography, ultra-realistic personal portrait, cinematic studio lighting, natural background, professional and confident look, Netflix documentary style, 16:9`
9.  **髮型變換**：`high-end hairstyle transformation, keeping facial features identical, changing only hairstyle and color to present different styles and outfits, 16:9`
10. **資訊圖表**：`modern infographic UI design, complex data converted into high-end infographics, clean UI structure, tech-style layout, Apple keynote style, 16:9`
11. **UI 設計**：`futuristic UI design, minimalist high-end tech UI interface, glassmorphism, clear information hierarchy, Apple/Tesla system-like interface, 16:9`
12. **新聞紀錄片感**：`cinematic documentary realism, ultra-realistic news report scene, live reporter, CNN/Netflix documentary atmosphere, natural light, 16:9`
13. **崩潰上班族**：`office burnout realism, office late at night with only one person, cold white screen light illuminating tired face, messy desk, empty coffee cups, 16:9`
14. **未來世界觀**：`cinematic future worldbuilding, hyper-giant future city where humans and AI co-exist naturally, Blade Runner style mixed with Apple concept design, 16:9`
15. **創作工作流**：`cinematic creative workflow, modern high-end AI creator studio, multiple generation results floating in space, brand designs, storyboards, and infographics, 16:9`

#### 🌟 創意社群視覺風格 Prompts
*   **3D 樹脂天氣微縮模型 (Resin Weather Card)**：
    > `主題：台南市 3D樹脂微縮 氣象圖。風格：超寫實 3D 樹脂質感，拋光與反光亮面處理 (Glossy)，立體微縮模型感，可愛療癒，色彩溫暖。每個獨立物件（安平古堡、赤崁樓、旅遊小人、在地美食）底部或後方需帶有微凸起與柔和陰影 (soft drop shadows)。中景為大型 3D 樹脂氣象資訊牌，顯示：台南市 Tainan City, 2026年5月16日, 32°C/26°C。直式海報比例，層次豐富，精緻微縮模型感。`
*   **韓風莫蘭迪奶油紙手帳 (Creamy Paper Journal)**：
    > `一張高質感韓系美學旅遊手記頁面，背景為奶油白 (Creamy white) 紙張。低飽和度莫蘭迪色系（乾燥玫瑰粉、鼠尾草綠、迷霧藍、奶油黃）。排版乾淨、留白有呼吸感。頂端有手寫風格標題，中間為手繪風視覺行程時間軸（數字圓形圖示 1, 2, 3...），景點名稱使用彩色半透明螢光筆劃記強調，穿插極簡線條的景點建築與美食插圖。`
*   **雙重曝光/側臉剪影史詩海報 (Double Exposure Profile Poster)**：
    > `根據照片自動產生一張收藏版史詩級海報：用人物的巨大優雅側臉向左看之剪影作為外輪廓。剪影內部自然生長出「行動力」或該角色主題的完整世界觀、標誌性場景、象徵符號與氛圍。不是硬拼貼，而是高級的剪影輪廓填充式敘事合成，帶有雙重曝光聯想，偏向電影海報與夢幻水彩插畫融合風格。柔和空氣透視，輕霧化過度，紙張顆粒，大面積留白，版式克制高級。`
*   **3D Pop-out 社群肖像 (人物衝出手機)**：
    > `請參考照片中的人物，保持面貌五官，生成一張 3D pop-out social media portrait poster。主體是一對快樂的父女，爸爸眼神溫柔、笑容滿面，女兒開心依偎。人物以強烈透視構圖從手機畫面中「突破/衝出螢幕」，一隻手或一隻腳跨出畫面，營造誇張景深與立體衝擊感。手機介面為 ins 風社群 UI，包含帳號名稱、頭像、追蹤數與貼圖。背景為陽光親子公園，帶有漂浮氣球、泡泡與心形亮片。明亮馬卡龍色系，高級商業攝影質感，鏡頭採用低角度廣角。`
