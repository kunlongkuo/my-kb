"""範例 scenes.py（嘉義市 115 年教育 AI 及數位學習績優成果宣傳動畫，2026-11）。
新專案複製到 <專案>/Codex/anim/scenes.py 後改寫：每鏡回傳 (片長, 元件清單)。

定位原則（以實際 Veo 影片的擷取畫面決定，不要只看構圖圖）：
- 鏡頭推進／平移的鏡：標題卡放在整段都不會擋到人臉的區域（多半是天空、樹梢），必要時 6 秒後收掉。
- 固定鏡頭（locked-off）的鏡：可以把標籤對準畫面中的物件（徽章、四宮格、卡片）。
- 標籤出場時間用 VOICE["nXX"]["segs"][i][0] + delay，對準旁白念到的那一刻。
- 每鏡開頭 GoldSweep(-0.5, 1.0)（接前一鏡光帶）、結尾 GoldSweep(dur-1.0, 1.0)；第一鏡只有結尾、最後一鏡只有開頭。
"""


def build(scene, fx):
    W, H = fx.W, fx.H
    Title, Ribbon, Panel, Tag, AwardBadge = fx.Title, fx.Ribbon, fx.Panel, fx.Tag, fx.AwardBadge
    Particles, GoldSweep, voice_caption, VOICE = fx.Particles, fx.GoldSweep, fx.voice_caption, fx.VOICE
    GOLD_TXT, CREAM_TXT = fx.GOLD_TXT, fx.CREAM_TXT
    if scene == "s01":
        dur = 9.0
        items = [
            Particles(60, 1),
            Title("嘉義市", 190, (W / 2, 250), 1.0, 7.6, sweep_at=2.4),
            Ribbon("教育 AI × 數位學習", (W / 2, 405), 1.7, 7.7),
            voice_caption("n01", 0.6, "這一年，嘉義市的教室裡，AI 與數位學習，悄悄改變了教與學的樣子"),
            GoldSweep(8.0, 1.0),
        ]
        return dur, items
    if scene == "s02":
        dur = 10.6
        items = [
            GoldSweep(-0.5, 1.0),
            Particles(45, 2),
            Panel((W / 2 - 790, 70, W / 2 + 790, 330), 0.8, 6.2),
            Ribbon("115年 教育部", (W / 2, 140), 1.1, 6.1, size=44),
            Title("推動教育AI及數位學習績優徵選", 92, (W / 2, 252), 1.4, 6.0, stagger=0.05, sweep_at=3.4),
            voice_caption("n02", 0.4, "在 115 年教育部推動教育 AI 及數位學習績優徵選中，嘉義市教育團隊，交出了亮眼的成績單"),
            GoldSweep(9.6, 1.0),
        ]
        return dur, items
    if scene == "s03":
        dur = 9.8
        d = 0.4
        meds = [(425, 195), (675, 95), (950, 75), (1230, 75), (1495, 170)]
        names = [("領航獎", 1, "校", 1.45), ("卓越獎", 2, "位", 3.00), ("特優", 4, "件", 4.67), ("優選", 3, "件", 5.98), ("佳作", 4, "件", 7.35)]
        items = [GoldSweep(-0.5, 1.0), Particles(50, 3)]
        for i, ((n, v, u, t), m) in enumerate(zip(names, meds)):
            items.append(AwardBadge(n, v, u, m, t + d, label_pos=(W / 2 + (i - 2) * 350, 820)))
        items.append(GoldSweep(8.8, 1.0))
        return dur, items
    if scene == "s04":
        dur = 8.7
        return dur, [
            GoldSweep(-0.5, 1.0), Particles(45, 4),
            Panel((60, 50, 800, 330), 0.6, 7.6),
            Title("領航獎", 128, (430, 155), 0.9, 7.5, sweep_at=2.6),
            Ribbon("嘉義市西區北園國民小學", (430, 272), 1.4, 7.5, size=42),
            voice_caption("n04", 0.4, "領航獎，由嘉義市西區北園國小獲得，領航全市，邁向智慧教育"),
            GoldSweep(7.7, 1.0),
        ]
    if scene == "s09":
        dur = 11.0
        d = 0.4
        seg = VOICE["n09"]["segs"]
        tags = [
            ("民族國小｜林崇光、楊佳惠", "《換個「基準」，自己出題！AI賦能，同課異教》", (60, 214), seg[1][0]),
            ("崇文國小｜張鉉苹", "《Think Safe, Act Fast：防火安全我會做》", (990, 214), seg[2][0]),
            ("垂楊國小｜黃雅瑜", "《破解火燒連環船的秘密》", (60, 612), seg[3][0]),
            ("林森國小｜呂嘉豪", "《花的構造與功能》", (990, 612), seg[4][0]),
        ]
        items = [GoldSweep(-0.5, 1.0), Particles(35, 9)]
        for a, b, pos, t in tags:
            items.append(Tag([(a, 30, 700, GOLD_TXT, "sans"), (b, 32, 800, CREAM_TXT, "serif")], pos, t + d, maxw=820))
        items += [
            Title("佳作 4 件", 104, (W / 2, 850), 0.5, 10.4, stagger=0.07, sweep_at=2.0),
            voice_caption("n09", d, "佳作四件，涵蓋 AI 出題、防火安全、歷史探究與自然科學，處處都是創新的第一線教學"),
            GoldSweep(10.0, 1.0),
        ]
        return dur, items
    if scene == "s05":
        dur, d = 8.6, 0.4
        seg = VOICE["n05"]["segs"]
        return dur, [
            GoldSweep(-0.5, 1.0), Particles(45, 5),
            Panel((W / 2 - 300, 34, W / 2 + 300, 214), 0.5, 7.6),
            Title("卓越獎", 120, (W / 2, 124), 0.7, 7.5, sweep_at=2.2),
            Tag([("嘉義市立民生國民中學", 30, 700, GOLD_TXT, "sans"), ("蔡邦居 老師", 46, 900, CREAM_TXT, "serif")], (60, 770), seg[1][0] + d),
            Tag([("嘉義市西區港坪國民小學", 30, 700, GOLD_TXT, "sans"), ("梁益榮 老師", 46, 900, CREAM_TXT, "serif")], (W - 60, 770), seg[2][0] + d, anchor="rt"),
            voice_caption("n05", d, "卓越獎，由民生國中蔡邦居老師，以及港坪國小梁益榮老師，一起摘下"),
            GoldSweep(7.6, 1.0),
        ]
    if scene == "s06":
        dur, d = 11.2, 0.4
        seg = VOICE["n06"]["segs"]
        return dur, [
            GoldSweep(-0.5, 1.0), Particles(45, 6),
            Panel((W / 2 - 190, 30, W / 2 + 190, 190), 0.4, 10.2),
            Title("特優", 112, (W / 2, 110), 0.6, 10.1, sweep_at=2.0),
            Tag([("民生國中｜蔡邦居", 30, 700, GOLD_TXT, "sans"), ("《Code出數學力──AI數學遊戲DIY × NotebookLM跨域全攻略》", 32, 800, CREAM_TXT, "serif")], (50, 790), seg[1][0] + d, maxw=840),
            Tag([("嘉義國中｜黃菁華、曾永祥", 30, 700, GOLD_TXT, "sans"), ("《AI大導演：我的創意廣告工作室》", 34, 800, CREAM_TXT, "serif")], (W - 50, 790), seg[2][0] + d, anchor="rt", maxw=840),
            voice_caption("n06", d, "特優教案，有民生國中的 AI 數學遊戲，也有嘉義國中的 AI 大導演，讓孩子用創意改寫課堂"),
            GoldSweep(10.2, 1.0),
        ]
    if scene == "s07":
        dur, d = 9.7, 0.4
        seg = VOICE["n07"]["segs"]
        return dur, [
            GoldSweep(-0.5, 1.0), Particles(45, 7),
            Panel((W / 2 - 190, 30, W / 2 + 190, 190), 0.3, 8.8),
            Title("特優", 112, (W / 2, 110), 0.4, 8.7, sweep_at=1.6),
            Tag([("博愛國小｜鄭云婷、潘思存、鄭嘉雯", 30, 700, GOLD_TXT, "sans"), ("《數位學習教案－從繪本月亮到阿提米絲任務的英語數位探究課》", 32, 800, CREAM_TXT, "serif")], (50, 790), seg[0][0] + d + 0.2, maxw=860),
            Tag([("嘉北國小｜張君聖、紀博仁", 30, 700, GOLD_TXT, "sans"), ("《嘉北城市學的數位雙翼》", 34, 800, CREAM_TXT, "serif")], (W - 50, 790), seg[4][0] + d, anchor="rt", maxw=760),
            voice_caption("n07", d, "博愛國小把繪本帶進英語探究任務，嘉北國小用數位雙翼，讀懂自己的城市"),
            GoldSweep(8.7, 1.0),
        ]
    if scene == "s08":
        dur, d = 12.0, 0.4
        seg = VOICE["n08"]["segs"]
        cards = [
            ([("崇文國小｜曾郁芳", 26, 700, GOLD_TXT, "sans"), ("《數位學習教案－人熊高峰會》", 30, 800, CREAM_TXT, "serif")], 372, seg[1][0]),
            ([("宣信國小｜王宇萱", 26, 700, GOLD_TXT, "sans"), ("《AI傳頌道將圳，永續數位新篇章》", 30, 800, CREAM_TXT, "serif")], 950, seg[2][0]),
            ([("崇文國小 葉姝瑜｜嘉大附小 林妤芳", 26, 700, GOLD_TXT, "sans"), ("《我的原創神話故事藍圖》", 30, 800, CREAM_TXT, "serif"),
              ("運用因材網Ｅ度寫作精靈實踐四學模式的AI輔助神話寫作", 22, 600, CREAM_TXT, "sans")], 1530, seg[3][0]),
        ]
        items = [GoldSweep(-0.5, 1.0), Particles(40, 8)]
        for lines, x, t in cards:
            items.append(Tag(lines, (x, 760), t + d, maxw=500, anchor="ct"))
        items += [
            Panel((W / 2 - 300, 24, W / 2 + 300, 174), 0.4, 11.0),
            Title("優選 3 件", 100, (W / 2, 100), 0.6, 10.9, stagger=0.07, sweep_at=2.0),
            voice_caption("n08", d, "優選三件，從人熊高峰會，到道將圳的永續新篇章，再到孩子的原創神話，故事與科技並肩同行"),
            GoldSweep(11.0, 1.0),
        ]
        return dur, items
    if scene == "s10":
        dur, d = 10.2, 0.4
        seg = VOICE["n10"]["segs"]
        t2 = seg[1][0] + d
        return dur, [
            GoldSweep(-0.5, 1.0), Particles(80, 10),
            Panel((W / 2 - 720, 60, W / 2 + 720, 340), t2 - 0.3, 99),
            Title("恭喜所有獲獎學校與教育夥伴", 88, (W / 2, 155), t2, 99, stagger=0.05, sweep_at=t2 + 1.5),
            Ribbon("嘉義市政府教育處智慧教育中心　賀", (W / 2, 268), t2 + 0.8, 99, size=40),
            voice_caption("n10", d, "感謝每一位教育夥伴的深耕與付出，嘉義市，用 AI 與數位學習，讓學習發光", y=H - 60, size=40),
        ]
    raise SystemExit(f"unknown scene {scene}")
