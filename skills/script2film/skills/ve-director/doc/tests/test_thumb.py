import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from doc_thumb import H, W, credits_for, make  # noqa: E402

CREDITS = """# 素材授權

| 檔案 | 原檔 | 授權 | 作者 | 署名 | 用在 |
|---|---|---|---|---|---|
| player.jpg | https://x | CC BY 4.0 | A | 照片：A／Wikimedia Commons，CC BY 4.0 | B3 |
| park.jpg | https://y | CC BY-SA 4.0 | B | 照片：B／Wikimedia Commons，CC BY-SA 4.0 | B1 |
| other.jpg | https://z | CC0 | C | 照片：C | 沒用到 |
"""


def _episode(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets/CREDITS.md").write_text(CREDITS, encoding="utf-8")
    return tmp_path


def test_credit_line_lists_the_pictures_used_and_maps_a_cutout_to_its_photo(tmp_path):
    base = _episode(tmp_path)
    got = credits_for({"bg": "assets/park.jpg", "cut": "assets/player_fg.png"}, base)
    assert got == "照片：A／Wikimedia Commons，CC BY 4.0；照片：B／Wikimedia Commons，CC BY-SA 4.0"


def test_written_credit_wins_and_no_table_means_no_line(tmp_path):
    assert credits_for({"bg": "x.jpg", "credit": "插圖：AI 生成"}, tmp_path) == "插圖：AI 生成"
    assert credits_for({"bg": "x.jpg"}, tmp_path) == ""


# the font comes from the asset layers (doc_common.assets("fonts")); without it asset() stops with the copy command
def test_thumbnail_is_youtube_size_and_the_words_stay_left_of_the_picture(tmp_path):
    Image.new("RGB", (1920, 1080), (40, 200, 40)).save(tmp_path / "still.jpg")
    im = make({"pic": "still.jpg", "title": "超過 20 億美元", "title2": "一筆交易", "accent": "#FF0000"}, tmp_path)
    assert im.size == (W, H)
    # the framed picture starts right of x≈620; no red title pixel may fall inside it
    red = [x for x in range(620, W) for y in range(0, H, 4) if im.getpixel((x, y))[0] > 200 and im.getpixel((x, y))[1] < 60]
    assert not red
