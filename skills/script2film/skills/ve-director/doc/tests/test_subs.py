"""Which subtitle is burned in and which caption files are written (FORMAT §4d point 4)."""
import json, sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from doc_common import series_of, subs_problems, subtitle_plan  # noqa: E402
from doc_cut import line_cues, write_caption_files  # noqa: E402

A = {"lang": "zh", "lines": [{"text": "一"}]}                                  # Chinese narration only
B = {"lang": "en", "lines": [{"text": "One."}], "zh": ["一"]}                 # English narration, Chinese translation
C = {"lang": "zh", "lines": [{"text": "一"}], "en": ["One."]}                 # Chinese narration, English translation
D = {"lang": "en", "lines": [{"text": "One."}]}                               # English narration only
ZH, EN = {"subs": {"burn": "zh"}}, {"subs": {"burn": "en"}}


def plan(doc, series=None):
    p = subtitle_plan(doc, series)
    return p["main"], p["second"]


def test_not_set_keeps_the_old_rules():
    assert plan(A) == ("narration", False)
    assert plan(B) == ("zh", True)                           # both lines, the old default
    assert plan({**B, "en_layer": False}) == ("zh", False)
    assert plan(C) == ("narration", True)
    assert plan({**C, "en_layer": False}) == ("narration", False)
    assert plan(D) == ("narration", False)
    assert subtitle_plan(A, None)["burn"] is None and subtitle_plan(A, {"name": "s"})["burn"] is None


def test_burn_names_the_one_language():
    assert plan(A, ZH) == ("narration", False)
    assert plan(B, ZH) == ("zh", False)
    assert plan(C, ZH) == ("narration", False)               # the English goes out as a caption file only
    assert plan(D, EN) == ("narration", False)
    assert plan(B, EN) == ("narration", False)               # English viewers: the Chinese translation is not burned
    assert plan(C, EN) == ("en", False)                      # Chinese narration for English viewers: only the "en" lines
    assert plan({**A, "lang": "zh-Hant"}, ZH) == ("narration", False)


def test_the_episode_overrides_the_series():
    assert subtitle_plan({**B, **EN}, ZH)["burn"] == "en"
    assert subtitle_plan(B, ZH)["burn"] == "zh"


@pytest.mark.parametrize("doc,series,word", [
    ({**A, "subs": {"burn": "ja"}}, None, "must be zh or en"),
    ({**B, "en_layer": False}, ZH, "keep only one of"),
    (D, ZH, "has no Chinese translation"),
    (A, EN, "has no English translation"),
    ({**D, "en": ["One."]}, None, "needs no en field"),
])
def test_bad_settings_are_listed_and_stop_the_plan(doc, series, word):
    assert any(word in m for m in subs_problems(doc, series))
    with pytest.raises(ValueError):
        subtitle_plan(doc, series)


def test_good_settings_have_no_problems():
    for doc, series in [(A, None), (B, None), (C, None), (D, None), (A, ZH), (B, ZH), (C, ZH), (D, EN), (B, EN), (C, EN)]:
        assert subs_problems(doc, series) == []


def test_series_of(tmp_path):
    ep = tmp_path / "系列" / "EP1"
    ep.mkdir(parents=True)
    assert series_of(ep) is None
    (ep.parent / "series.json").write_text(json.dumps({"name": "s", **ZH}), encoding="utf-8")
    assert series_of(ep)["subs"] == {"burn": "zh"}


def episode(tmp_path, doc):
    (tmp_path / "voice.cleaned").mkdir()
    (tmp_path / "cut").mkdir()
    (tmp_path / "voice.cleaned/final.srt").write_text("1\n00:00:00,500 --> 00:00:02,000\n" + doc["lines"][0]["text"] + "\n", encoding="utf-8")
    (tmp_path / "voice.cleaned/screens.json").write_text(json.dumps(
        [{"line": 1, "text": doc["lines"][0]["text"], "at": 0.5, "end": 2.0}], ensure_ascii=False), encoding="utf-8")
    return doc


@pytest.mark.parametrize("doc,names", [(A, ["subtitles_zh.srt"]), (B, ["subtitles_en.srt", "subtitles_zh.srt"]),
                                       (C, ["subtitles_zh.srt", "subtitles_en.srt"]), (D, ["subtitles_en.srt"])])
def test_every_episode_gets_caption_files(tmp_path, doc, names):
    files = write_caption_files(tmp_path, episode(tmp_path, doc), "cut")
    assert [p.name for _, p in files] == names
    assert sorted(p.name for p in (tmp_path / "cut").iterdir()) == sorted(names)
    for lang, p in files:
        text = p.read_text(encoding="utf-8")                 # plain UTF-8, no style markup (YouTube's basic .srt)
        assert "-->" in text and "<" not in text and "{" not in text
    own = tmp_path / "cut" / names[0]                        # the narration's file is the episode's own final.srt
    assert own.read_text(encoding="utf-8") == (tmp_path / "voice.cleaned/final.srt").read_text(encoding="utf-8")


def test_subs_must_be_an_object():
    assert "must be an object" in subs_problems({**A, "subs": "zh"}, None)[0]
    assert "must be an object" in subs_problems(A, {"name": "s", "subs": "zh"})[0]
    assert subs_problems(A, {"name": "s", "subs": {}}) == []


def test_english_main_subtitle_leaves_out_burst_lines(tmp_path):
    """subs.burn "en" over Chinese narration: doc_cut writes the burned subtitle from line_cues, without the burst_title
    lines (they show as a title) and without lines whose "en" is empty."""
    doc = {"lang": "zh", "lines": [{"text": "一"}, {"text": "二"}, {"text": "三"}], "en": ["One.", "Two.", ""]}
    (tmp_path / "voice.cleaned").mkdir()
    (tmp_path / "voice.cleaned/screens.json").write_text(json.dumps(
        [{"line": k, "text": t, "at": k, "end": k + 0.8} for k, t in ((1, "一"), (2, "二"), (3, "三"))], ensure_ascii=False))
    assert [c["text"] for c in line_cues(tmp_path, doc)] == ["One.", "Two."]
    assert [c["text"] for c in line_cues(tmp_path, doc, skip={1})] == ["Two."]


def test_sub_highlight_wraps_whole_words_only():
    from doc_cut import sub_highlight, sub_markup
    hl = sub_highlight({"sub_highlight": {"words": ["VideoExpress", "TalkingPhotos"], "color": "#D65440"}})
    assert sub_markup("then VideoExpress turns it", hl) == 'then <span class="hl">VideoExpress</span> turns it'
    assert sub_markup("TalkingPhotosX & <b>", hl) == "TalkingPhotosX &amp; &lt;b&gt;"      # not part of a longer word; text escaped
    assert sub_markup("plain", None) == "plain"


def test_sub_highlight_rejects_a_bad_colour():
    from doc_cut import sub_highlight
    with pytest.raises(SystemExit):
        sub_highlight({"sub_highlight": {"words": ["X"], "color": "red"}})
