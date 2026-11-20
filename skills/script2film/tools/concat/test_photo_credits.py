"""photo_credits：照片拍的當頁署名從 CREDITS.md 帶、時間照 beats.json、缺署名就停。"""
import pytest

import photo_credits as m

MD = """# 素材授權

| 檔案 | 原檔 | 授權 | 作者 | 署名 | 用在 |
|---|---|---|---|---|---|
| a.jpg | https://x | CC0 | 甲 | 照片：甲，CC0 | 第 1 句 |
| b.png | https://y | 公有領域 | 乙 | 圖：乙，公有領域 | 第 2 句 |
"""
BEATS = {"beats": [{"id": "B1", "start": 1.0, "end": 4.5}, {"id": "B2", "start": 4.5, "end": 9.0},
                   {"id": "B3", "start": 9.0, "end": 12.0}, {"id": "B4", "start": 12.0, "end": 15.0}]}


def test_rows_read_the_credit_column():
    assert m.credit_rows(MD) == {"a.jpg": "照片：甲，CC0", "b.png": "圖：乙，公有領域"}


def test_code_photo_beats_get_their_credit_and_beat_time():
    doc = {"beats": [
        {"id": "B1", "source": "code", "scene": "photo", "params": {"photos": [{"src": "assets/a.jpg"}]}},
        {"id": "B2", "source": "code", "scene": "quote_card", "params": {"photo": [{"src": "assets/a.jpg"}, {"src": "assets/b.png"}]}},
        {"id": "B3", "source": "code", "scene": "web_evidence", "params": {"src": "web/x.png"}},   # 報導截圖有自己的來源列
        {"id": "B4", "source": "clip", "clip": "assets/a.jpg"}]}                                    # 不是程式畫面
    assert m.photo_credits(doc, BEATS, m.credit_rows(MD)) == [
        {"beat": "B1", "start": 1.0, "dur": 3.5, "text": "照片：甲，CC0"},
        {"beat": "B2", "start": 4.5, "dur": 4.5, "text": "照片：甲，CC0；圖：乙，公有領域"}]


def test_a_photo_without_a_credit_row_stops():
    doc = {"beats": [{"id": "B1", "source": "code", "params": {"photos": [{"src": "assets/c.jpg"}]}}]}
    with pytest.raises(SystemExit, match="c.jpg"):
        m.photo_credits(doc, BEATS, m.credit_rows(MD))


def test_credit_sits_flush_right():
    import plan2concat_mcp as p
    # 寬 400 px、左右各留 0.012 × 1080 px 底色：右緣離畫面右邊 70 px
    x = p.credit_offset_x(400)
    assert (0.5 + x) * 1920 + 400 / 2 + 0.012 * 1080 == pytest.approx(1920 - 70, abs=0.5)


def test_ai_credit_marks_beats_that_use_generated_footage():
    doc = {"ai_credit": "AI-generated image", "beats": [
        {"id": "B1", "source": "clip", "clip": "extra_collage/ve_collage/shot1.mp4"},
        {"id": "B2", "source": "code", "scene": "photo", "params": {"photos": [{"src": "assets/a.jpg"}]},
         "bg_video": {"src": "extra_live/ve_live/shot1.mp4"}},
        {"id": "B3", "source": "clip", "clip": "host/tp_host.mp4"},            # 主持人不是生成的場景
        {"id": "B4", "source": "ve", "shot": "x"}]}
    assert [(r["beat"], r["text"]) for r in m.photo_credits(doc, BEATS, m.credit_rows(MD))] == [
        ("B1", "AI-generated image"), ("B2", "照片：甲，CC0；AI-generated image"), ("B4", "AI-generated image")]
    del doc["ai_credit"]                                                        # 沒設就和以前一樣：只有照片拍
    assert [r["beat"] for r in m.photo_credits(doc, BEATS, m.credit_rows(MD))] == ["B2"]
