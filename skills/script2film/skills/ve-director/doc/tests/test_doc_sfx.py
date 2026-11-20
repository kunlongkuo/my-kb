"""doc_sfx: word matching, the D4 drop order, sfx_off, licences, the mixed track; scenes mark their sounds."""
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_sfx  # noqa: E402
from doc_code import phrase_at  # noqa: E402

KINDS = {k: {"files": [], "volume": 0.2} for k in ("paper", "reveal", "water", "wind", "tick", "whoosh", "tear")}


def beat(bid, start, text):
    chars = [c for c in text if c.strip()]
    return {"id": bid, "start": start, "text": text, "source": "code", "tokens": [[c, round(.2 * i, 2)] for i, c in enumerate(chars)]}


def test_whole_words_only():
    b = [beat("B1", 0, "他打算過紅海")]
    assert doc_sfx.word_hits(b, {"紅海": "water"}, "zh") == [("B1", "紅海", "water", 0.8, 4)]
    with pytest.raises(SystemExit, match="single characters"):
        doc_sfx.check_words({"打": "water"}, KINDS, "zh")
    with pytest.raises(SystemExit, match="unknown kinds"):
        doc_sfx.check_words({"紅海": "ocean"}, KINDS, "zh")


def test_drop_order():
    """4 visual marks in one beat (cap 3), a word 0.6 s from a visual mark (dropped), a word 5 s after a kept word (dropped)."""
    beats = [beat("B1", 0, "甲乙丙丁"), beat("B2", 10, "紅海"), beat("B3", 20, "大風吹過"), beat("B4", 25, "紅海")]
    a = {"B1": [{"kind": "tick", "t": .5}, {"kind": "tick", "t": 1.0}, {"kind": "tick", "t": 1.5}, {"kind": "tick", "t": 2.0}],
         "B2": [{"kind": "paper", "t": .6}]}
    kept, dropped = doc_sfx.plan({}, beats, a, {"紅海": "water", "大風": "wind"}, KINDS, "zh", phrase_at)
    assert [(x["src"], x["beat"]) for x in kept] == [("A", "B1")] * 3 + [("A", "B2"), ("B", "B3")]
    why = {(x["beat"], x["src"]): x["why"] for x in dropped}
    assert "over 3" in why[("B1", "A")] and "1 s of a visual" in why[("B2", "B")] and "8 s of the previous" in why[("B4", "B")]


def test_same_kind_merges_within_a_quarter_second():
    kept, _ = doc_sfx.plan({}, [beat("B1", 0, "甲")], {"B1": [{"kind": "paper", "t": .1}, {"kind": "paper", "t": .3}]},
                           {}, KINDS, "zh", phrase_at)
    assert len(kept) == 1


def test_add_wipes_and_off():
    beats = [beat("B1", 0, "甲乙"), beat("B2", 5, "甲乙丙丁戊己紅海")]   # 紅海 at 6.2 s: clear of the tear at 5.0
    doc = {"sfx_add": [{"beat": "B1", "at": "乙", "kind": "reveal"}], "wipes": ["B2"],
           "sfx_off": ["B2#kind:tear"]}
    kept, dropped = doc_sfx.plan(doc, beats, {}, {"紅海": "water"}, KINDS, "zh", phrase_at)
    assert [(x["src"], x["kind"], x["t"]) for x in kept] == [("C", "reveal", 0.2), ("B", "water", 6.2)]
    assert dropped[0]["why"] == "sfx_off B2#kind:tear"
    kept, _ = doc_sfx.plan({"sfx_off": ["B2#word:紅海"]}, beats, {}, {"紅海": "water"}, KINDS, "zh", phrase_at)
    assert kept == []
    # sfx_off comes last (D4): a word that collided with the tear stays dropped after the tear is switched off
    kept, _ = doc_sfx.plan({"wipes": ["B2"], "sfx_off": ["B2#kind:tear"]}, [beat("B2", 5, "紅海")], {}, {"紅海": "water"},
                           KINDS, "zh", phrase_at)
    assert kept == []
    kept, _ = doc_sfx.plan({"sfx_off": ["B2"], "wipes": ["B2"]}, beats, {}, {"紅海": "water"}, KINDS, "zh", phrase_at)
    assert kept == []


@pytest.mark.parametrize("doc,msg", [
    ({"sfx_off": ["B9"]}, "no such beat"), ({"sfx_off": ["B1#kind:boom"]}, "kind must be"),
    ({"sfx_off": ["B1#word:大水"]}, "not in the series word list"), ({"sfx_add": [{"beat": "B1", "at": "丙", "kind": "tick"}]}, "not in"),
    ({"sfx_add": [{"beat": "B1", "at": 0, "kind": "boom"}]}, "kind must be"),
])
def test_bad_manual_entries_stop(doc, msg):
    with pytest.raises(SystemExit, match=msg):
        doc_sfx.plan(doc, [beat("B1", 0, "甲乙")], {}, {"紅海": "water"}, KINDS, "zh", phrase_at)


def test_only_cleared_licences(tmp_path):
    (tmp_path / "a.wav").write_bytes(b"x")
    man = {"a": {"id": "a", "file": "a.wav", "license": "ElevenLabs 免費 tier：不可商用"}}
    with pytest.raises(SystemExit, match="not CC0"):
        doc_sfx.resolve({"paper": {"files": ["a"]}}, tmp_path, man)
    man["a"]["license"] = "CC0"
    assert doc_sfx.resolve({"paper": {"files": ["missing", "a"]}}, tmp_path, {**man, "missing": {"id": "missing", "file": "m.wav", "license": "CC0"}})["paper"][1]["id"] == "a"


def level(path, a, b):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(a), "-t", str(b - a), "-i", str(path), "-f", "f32le", "-ac", "1", "-"],
                       capture_output=True, check=True).stdout
    import array
    x = array.array("f", r)
    return 10 * math.log10(sum(v * v for v in x) / len(x) + 1e-20)


def test_mix_places_each_sound(tmp_path):
    tone = tmp_path / "t.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=f=800:d=0.2", str(tone)], check=True)
    out = tmp_path / "sfx" / "bed.wav"
    doc_sfx.mix([{"t": 1.0, "kind": "tick"}, {"t": 3.0, "kind": "tick"}], {"tick": (tone, {})}, {"tick": {"volume": .5}}, 5.0, out)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                               capture_output=True, text=True).stdout)
    assert abs(dur - 5.0) < 0.03
    assert level(out, 1.02, 1.18) > -20 and level(out, 3.02, 3.18) > -20
    assert level(out, 1.5, 2.8) < -80 and level(out, 0.0, 0.95) < -80


def test_scenes_mark_their_sounds(tmp_path):
    """stat_count marks one reveal when the count ends; quote_card with two stills marks one paper (0.25 s apart, merged)."""
    import doc_code
    P = tmp_path
    (P / "stills").mkdir()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=gray:s=320x180", "-frames:v", "1",
                    str(P / "stills/a.jpg")], check=True)
    doc = {"lang": "zh", "sfx_on": True}
    b = {"id": "B1", "duration": 4.0, "tokens": [["四", 0.5], ["十", 0.7]]}
    out, _ = doc_code.build(P, doc, b, {"scene": "stat_count", "params": {"value": 40, "at": 0.5, "dur": 1.2}}, "collage")
    doc_code.read_sfx(out, P / "s.json")
    assert json.loads((P / "s.json").read_text()) == [{"kind": "reveal", "t": 1.7}]
    b["id"] = "B2"
    out, _ = doc_code.build(P, doc, b, {"scene": "quote_card", "params": {"text": "x", "at": 0.5, "photo": [
        {"src": "stills/a.jpg"}, {"src": "stills/a.jpg"}]}}, "collage")
    doc_code.read_sfx(out, P / "q.json")
    marks = json.loads((P / "q.json").read_text())
    kept, _ = doc_sfx.plan({}, [{**beat("B2", 0, "x"), "id": "B2"}], {"B2": marks}, {}, KINDS, "zh", phrase_at)
    assert [x["kind"] for x in kept] == ["paper", "whoosh"]
