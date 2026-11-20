import json, sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from doc_cut import en_subs, en_wrap, srt, write_caption_files, zh_screens  # noqa: E402
from doc_evidence import stitch  # noqa: E402


def test_en_wrap_makes_lines_of_about_equal_length():
    assert en_wrap("short line") == "short line"
    long = "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen"
    a, b = en_wrap(long, width=60).split("\n")
    assert abs(len(a) - len(b)) <= 10 and f"{a} {b}" == long
    rows = en_wrap(long, width=40).split("\n")   # 105 characters, 40 a line: three lines (2026-10-31 shared plate)
    assert len(rows) == 3 and " ".join(rows) == long and max(map(len, rows)) - min(map(len, rows)) <= 10


def test_srt_numbers_and_formats_times():
    assert srt([{"start": 61.5, "end": 3661.25, "text": "Hi"}]) == "1\n00:01:01,500 --> 01:01:01,250\nHi\n"


def _episode(tmp_path, en):
    (tmp_path / "voice.cleaned").mkdir()
    screens = [{"line": 1, "text": "大家好", "at": 0.5, "end": 1.4}, {"line": 1, "text": "我是 Sam", "at": 1.4, "end": 3.0},
               {"line": 2, "text": "今天聊", "at": 3.0, "end": 5.0}]
    (tmp_path / "voice.cleaned/screens.json").write_text(json.dumps(screens, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "voice.cleaned/final.srt").write_text("1\n00:00:00,500 --> 00:00:01,400\n大家好\n", encoding="utf-8")
    (tmp_path / "cut").mkdir()
    return {"lines": [{"text": "大家好，我是 Sam。"}, {"text": "今天聊。"}], "en": en}


def test_en_line_spans_all_screens_of_its_chinese_line(tmp_path):
    doc = _episode(tmp_path, ["Hi, I'm Sam", "Today"])
    L = en_subs(tmp_path, doc)
    assert [(c["start"], c["end"], c["text"]) for c in L["cues"]] == [(0.5, 3.0, "Hi, I'm Sam"), (3.0, 5.0, "Today")]
    write_caption_files(tmp_path, doc, "cut")
    assert (tmp_path / "cut/subtitles_en.srt").read_text(encoding="utf-8").startswith("1\n00:00:00,500 --> 00:00:03,000\nHi, I'm Sam")
    assert (tmp_path / "cut/subtitles_zh.srt").exists()


def test_an_empty_en_line_gives_no_cue(tmp_path):
    """A line the host already says in English ("What?! Amazing~") is not shown twice: "" in "en" leaves it out."""
    doc = _episode(tmp_path, ["Hi, I'm Sam", " "])
    assert [c["text"] for c in en_subs(tmp_path, doc)["cues"]] == ["Hi, I'm Sam"]
    write_caption_files(tmp_path, doc, "cut")
    assert (tmp_path / "cut/subtitles_en.srt").read_text(encoding="utf-8").count("-->") == 1


def test_en_line_count_must_match_the_script(tmp_path):
    with pytest.raises(SystemExit):
        en_subs(tmp_path, _episode(tmp_path, ["only one"]))


def test_stitch_stacks_slices_with_a_gap(tmp_path):
    src = tmp_path / "page.png"
    im = Image.new("RGB", (100, 300), "white")
    im.paste((255, 0, 0), (0, 0, 100, 50))
    im.paste((0, 0, 255), (0, 200, 100, 250))
    im.save(src)
    out = stitch(src, [10, 90], [[0, 50], [200, 250]])
    assert out.size == (80, 136)
    assert out.getpixel((5, 10)) == (255, 0, 0) and out.getpixel((5, 70)) == (255, 255, 255) and out.getpixel((5, 100)) == (0, 0, 255)


EN_SCREENS = [{"line": 1, "text": "Hi, I'm Sam.", "at": 1.0, "end": 3.0}, {"line": 2, "text": "Today we look at one house,", "at": 3.0, "end": 5.0},
              {"line": 2, "text": "and who destroyed it.", "at": 5.0, "end": 9.0}]
EN_DOC = {"lang": "en", "lines": [{"text": "Hi, I'm Sam."}, {"text": "Today we look at one house, and who destroyed it."}],
          "zh": ["我是 Sam。", "今天看一棟房子，還有是誰把它摧毀的。"]}


def test_zh_screens_share_the_english_lines_span_by_character_count():
    cues = zh_screens(EN_DOC, EN_SCREENS)
    assert [c["text"] for c in cues] == ["我是 Sam", "今天看一棟房子，還有是誰把它摧毀的"]
    assert (cues[0]["start"], cues[0]["end"]) == (1.0, 3.0) and (cues[1]["start"], cues[1]["end"]) == (3.0, 9.0)
    long = {**EN_DOC, "zh": ["我是 Sam。", "今天要看的是城市郊外的一棟兩層樓房子，還有到底是誰把它摧毀的。"]}
    a, b = zh_screens(long, EN_SCREENS)[1:]            # over 18 characters: two screens, 18 and 11 characters of a 6 s span
    assert (a["start"], a["end"], b["start"], b["end"]) == (3.0, round(3 + 6 * 18 / 29, 3), round(3 + 6 * 18 / 29, 3), 9.0)


def test_zh_screens_skip_burst_lines_and_check_the_counts():
    assert [c["text"] for c in zh_screens(EN_DOC, EN_SCREENS, skip={1})] == ["今天看一棟房子，還有是誰把它摧毀的"]
    with pytest.raises(SystemExit):
        zh_screens({**EN_DOC, "zh": ["只有一句"]}, EN_SCREENS)
    with pytest.raises(SystemExit):
        zh_screens({**EN_DOC, "lang": "zh"}, EN_SCREENS)


def test_zh_episode_puts_the_english_narration_on_the_second_line(tmp_path):
    (tmp_path / "voice.cleaned").mkdir(); (tmp_path / "cut").mkdir()
    (tmp_path / "voice.cleaned/screens.json").write_text(json.dumps(EN_SCREENS), encoding="utf-8")
    (tmp_path / "voice.cleaned/final.srt").write_text("1\n00:00:01,000 --> 00:00:03,000\nHi, I'm Sam.\n", encoding="utf-8")
    L = en_subs(tmp_path, EN_DOC)
    assert [(c["start"], c["end"]) for c in L["cues"]] == [(1.0, 3.0), (3.0, 9.0)] and L["cues"][0]["text"] == "Hi, I'm Sam."
    write_caption_files(tmp_path, EN_DOC, "cut")
    assert "我是 Sam" in (tmp_path / "cut/subtitles_zh.srt").read_text(encoding="utf-8")
    # the narration's own file is the episode's final.srt (screen by screen), not one cue per line
    assert (tmp_path / "cut/subtitles_en.srt").read_text(encoding="utf-8") == (tmp_path / "voice.cleaned/final.srt").read_text(encoding="utf-8")
