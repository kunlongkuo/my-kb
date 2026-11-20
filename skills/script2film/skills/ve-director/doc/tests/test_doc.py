"""pytest for doc-mode pure logic: tokens, subtitle chunking, trigger checking."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from doc_align import chunks, screen_text, two_lines  # noqa: E402
from doc_code import missing_triggers  # noqa: E402
from doc_common import line_key, tokens  # noqa: E402
from doc_voice import SR, candidates, tail_fade  # noqa: E402


def test_tokens_match_lib_js_rule():
    assert tokens("兩個程式，你打我", "zh") == list("兩個程式你打我")
    assert tokens("You've already — forgiven THEM.", "en") == ["you've", "already", "forgiven", "them"]
    assert tokens("doesn’t", "en") == ["doesn't"]


def test_zh_chunks_cut_at_punctuation_and_stay_short():
    out = chunks("當然，前提是對方還在這段關係裡；被傷害，不等於要一直忍。", "zh")
    assert all(len(tokens(c, "zh")) <= 18 for c in out)
    assert "".join(out) == "當然，前提是對方還在這段關係裡；被傷害，不等於要一直忍。"


def test_screen_text_drops_the_closing_chinese_full_stop_only():
    assert screen_text("拿下隊史第一座冠軍。") == "拿下隊史第一座冠軍"
    assert screen_text("這代表錢不重要嗎？也不是。") == "這代表錢不重要嗎？也不是"
    assert screen_text("結果呢？") == "結果呢？" and screen_text("今天聊，") == "今天聊"
    assert screen_text("It was a long wait.") == "It was a long wait."


def test_en_chunks_use_two_lines_of_42():
    out = chunks("Of course, this assumes the other person is still in the relationship. Being hurt doesn't mean enduring forever.", "en")
    assert all(len(line) <= 42 for c in out for line in c.split("\n"))
    assert " ".join(c.replace("\n", " ") for c in out).split() == \
        "Of course, this assumes the other person is still in the relationship. Being hurt doesn't mean enduring forever.".split()


def test_two_lines_breaks_near_the_middle():
    assert two_lines("short line") == "short line"
    a, b = two_lines("That one extra chance pulls them both out of the spiral.").split("\n")
    assert abs(len(a) - len(b)) < 12


def beat(text, lang):
    return {"tokens": [[t, i * 0.3] for i, t in enumerate(tokens(text, lang))]}


def test_missing_triggers_flags_absent_phrases_only():
    b = beat("Two programs on a screen. You hit me, I hit you back.", "en")
    assert missing_triggers({"appear": "two programs", "hits": ["you hit me", "i hit you back"]}, b, "en") == []
    assert missing_triggers({"hits": ["you hit me", "i strike back"]}, b, "en") == ["hits='i strike back'"]
    assert missing_triggers({"photos": [{"cap": "not a time key", "cap_at": {"w": "on a screen", "d": .2}}]}, b, "en") == []
    assert missing_triggers({"photos": [{"at": {"w": "nowhere"}}]}, b, "en") == ["w='nowhere'"]


def test_missing_triggers_zh():
    b = beat("螢幕上兩個程式，你打我一下，我就回你一下。", "zh")
    assert missing_triggers({"appear": "兩個程式", "hits": ["打我", "回你"]}, b, "zh") == []
    assert missing_triggers({"appear": "三個程式"}, b, "zh") == ["appear='三個程式'"]


def test_host_cut_points_sit_in_pauses_under_the_cap():
    from doc_host import cut_points
    lines = [{"start": i * 10 + 0.1, "end": i * 10 + 9.5} for i in range(18)]   # 18 lines, pauses at 9.8, 19.8, …
    total = 180.0
    cuts = cut_points(lines, total, 58)
    edges = [0.0, *cuts, total]
    assert all(10 <= b - a <= 58 for a, b in zip(edges, edges[1:]))
    assert all(any(abs(c - (l["end"] + n["start"]) / 2) < 1e-9 for l, n in zip(lines, lines[1:])) for c in cuts)


def test_host_cut_points_keep_the_last_part_long_enough():
    from doc_host import cut_points
    lines = [{"start": i * 10 + 0.1, "end": i * 10 + 9.5} for i in range(7)]    # pauses at 9.8 … 59.8; 64 s total
    cuts = cut_points(lines, 64.0, 58)
    assert cuts and 64.0 - cuts[-1] >= 10 and cuts[0] <= 58


def test_host_short_narration_needs_no_cut():
    from doc_host import cut_points
    assert cut_points([{"start": 0.1, "end": 40.0}], 40.2, 58) == []


def test_host_cut_points_for_h3_stay_under_15_s():
    """MiniMax H3 locks at most 15 s of audio: --max 15 --min 4 gives parts of 4-15 s, cut in the pauses."""
    import pytest
    from doc_host import cut_points
    lines = [{"start": i * 4.0 + 0.1, "end": i * 4.0 + 3.6} for i in range(10)]   # 3.5 s lines, pauses at 3.85, 7.85, …
    total = 40.0
    cuts = cut_points(lines, total, 15, 4)
    edges = [0.0, *cuts, total]
    assert all(4 <= b - a <= 15 for a, b in zip(edges, edges[1:])) and len(edges) > 3
    with pytest.raises(SystemExit):
        cut_points(lines, total, 15)            # the TP minimum (10 s) leaves no pause to cut at in this case


def test_era_palette_reinks_code_and_ve_and_leaves_tables_alone():
    import pytest
    from doc_themes import CODE_THEMES, VE_THEMES, code_theme, ve_theme
    base_code, base_ve = dict(CODE_THEMES["collage"]), dict(VE_THEMES["collage"])
    assert code_theme("collage", "族長") == base_code and ve_theme("collage", None) == base_ve
    c, v = code_theme("collage", "出埃及與曠野"), ve_theme("collage", "出埃及與曠野")
    assert "--red:#1d7a80" in c["vars"] and "180,80,42" in c["css"] and "214,162,39" not in c["css"]
    assert "0.40  0 0 0 0 0.26" in c["texture"] and ".30  0 0 0 0 .22" not in c["texture"]
    assert "turquoise faience accent" in v["style"] and "hot red accent" not in v["style"]
    assert CODE_THEMES["collage"] == base_code and VE_THEMES["collage"] == base_ve
    with pytest.raises(ValueError):
        code_theme("collage", "火星")
    with pytest.raises(ValueError):
        ve_theme("live", "被擄")


def test_every_era_palette_replaces_the_collage_law():
    from doc_themes import PALETTES, VE_THEMES, ve_theme
    for era, p in PALETTES.items():
        if p:
            assert ve_theme("collage", era)["style"] != VE_THEMES["collage"]["style"], era


def test_tail_fade_silences_only_the_end():
    import numpy as np
    x = np.ones(SR, np.float32)
    y = tail_fade(x, 0.08)
    k = int(0.08 * SR)
    assert len(y) == len(x) and x[-1] == 1.0            # input untouched, length kept
    assert np.all(y[:-k] == 1.0) and y[-1] < 1e-6         # body unchanged, last sample silent
    assert np.all(np.diff(y[-k:]) <= 0)                   # monotone fade
    assert np.array_equal(tail_fade(x, 0), x)             # 0 = off
    assert len(tail_fade(np.ones(10, np.float32), 1.0)) == 10   # fade longer than the line clamps


def test_line_key_follows_spoken_text_and_voice(tmp_path):
    (tmp_path / "ref.wav").write_bytes(b"RIFFvoice")
    (tmp_path / "ref.txt").write_text("參考\n", encoding="utf-8")
    doc = {"lang": "zh", "voice": {"ref_wav": "ref.wav", "ref_text": "ref.txt"}}
    a = line_key(doc, tmp_path, {"text": "起初"})
    assert a == line_key(doc, tmp_path, {"text": "起初"})                 # same line, same takes, wherever it sits
    assert a != line_key(doc, tmp_path, {"text": "起初神"})               # edited text, new takes
    assert a == line_key(doc, tmp_path, {"text": "字幕", "tts": "起初"})  # the spoken text counts, not the subtitle
    (tmp_path / "ref.wav").write_bytes(b"RIFFother")
    assert a != line_key(doc, tmp_path, {"text": "起初"})                 # another reference voice


def test_candidates_prefer_the_key_and_fall_back_to_line_numbers(tmp_path):
    for f in ("03_11.wav", "abc123def456_11.wav", "abc123def456_12.wav", "fff000fff000_11.wav"):
        (tmp_path / f).write_bytes(b"")
    assert [c.name for c in candidates(tmp_path, "abc123def456", 3)] == ["abc123def456_11.wav", "abc123def456_12.wav"]
    assert [c.name for c in candidates(tmp_path, "000000000000", 3)] == ["03_11.wav"]
    assert candidates(tmp_path, "000000000000", 4) == []
