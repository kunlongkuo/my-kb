"""en.shared（中英雙語字幕共用一個底框）：英文佔中文框幾行空白、框寬與中英位置。"""
import os
from pathlib import Path

import pytest

import plan2concat_mcp as m

# 字型是使用者自己的，不進倉庫：S2F_TEST_FONT 指定一支 ttf；沒設（或指到不存在的檔）就略過，不猜位置


@pytest.fixture
def font():
    env = os.environ.get("S2F_TEST_FONT")
    if not env:
        pytest.skip("no test font: S2F_TEST_FONT is not set (set it to the path of a .ttf)")
    f = Path(env)
    if not f.is_file():
        pytest.skip(f"no test font: {f} (point S2F_TEST_FONT at a .ttf)")
    return str(f)


EN = {"size": 0.023, "zh_offsetY": 0.32, "shared": True,
      "cues": [{"start": 0.0, "end": 4.0, "text": "one line"}, {"start": 4.0, "end": 8.0, "text": "a\nb\nc"}]}


def test_rows_two_english_lines_per_blank_chinese_line():
    assert [m.en_rows(EN, t) for t in ["a", "a\nb", "a\nb\nc"]] == [1, 1, 2]


def test_chinese_line_stays_put_and_plate_grows_down(font):
    style, y1 = m.shared_zh({"start": 0.5, "text": "中文一行"}, {}, EN, font)
    style3, y3 = m.shared_zh({"start": 4.5, "text": "中文一行"}, {}, EN, font)
    assert style["content"] == "中文一行\n　" and style3["content"] == "中文一行\n\u3000\n\u3000"
    # the Chinese line's centre (block centre minus k half-pitches) is the same either way
    assert y1 - m.PITCH / 2 == pytest.approx(EN["zh_offsetY"], abs=1e-4) == y3 - 2 * m.PITCH / 2


def test_plate_is_as_wide_as_the_wider_language(font):
    long_en = {**EN, "cues": [{"start": 0, "end": 4, "text": "a much longer English sentence than the Chinese"}]}
    narrow = m.shared_zh({"start": 0.5, "text": "短"}, {}, EN, font)[0]["maxWidth"]
    wide = m.shared_zh({"start": 0.5, "text": "短"}, {}, long_en, font)[0]["maxWidth"]
    assert wide > narrow > 0
