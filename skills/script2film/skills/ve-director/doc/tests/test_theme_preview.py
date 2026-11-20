"""doc_theme_preview: which themes and beats it offers, the estimated timing, placeholders, the 2x2 film, --pick, and the
theme ledger reminder in doc_lint."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_lint  # noqa: E402
import doc_theme_preview as tp  # noqa: E402
from doc_themes import CODE_THEMES  # noqa: E402

LINES = [{"text": "這家咖啡店去年賣出六十三萬杯咖啡。"}, {"text": "第一步是一張傳單。"}, {"text": "客人怎麼找到這裡的？"}]
BEATS = [{"id": "B1", "lines": [1], "source": "code", "scene": "stat_count", "params": {"value": 63}},
         {"id": "B2", "lines": [2], "source": "ve"},
         {"id": "B3", "lines": [3], "source": "code", "scene": "web_evidence", "params": {"src": "evidence/a.png"}},
         {"id": "B4", "lines": [3], "from": "怎麼", "source": "code", "scene": "quote_card",
          "params": {"text": "x", "photo": [{"src": "stills/a.jpg"}, {"src": "stills/b.jpg", "fg": "stills/b_fg.png"}]}},
         {"id": "B5", "lines": [3], "source": "code", "scene": "stat_count", "params": {"value": 1}},
         {"id": "B6", "lines": [3], "source": "code", "scene": "cover", "params": {"title": "t"}}]
DOC = {"lang": "zh", "theme": "lecture-light", "lines": LINES, "beats": BEATS, "gaps": {"default": 0.5}}


def ep(tmp_path, name="ep", doc=DOC, series=None):
    d = tmp_path / name
    d.mkdir(parents=True)
    (d / "doc.json").write_text(json.dumps(doc, ensure_ascii=False))
    if series is not None:
        (tmp_path / "series.json").write_text(json.dumps(series, ensure_ascii=False))
    return d


def test_three_themes_differ(tmp_path):
    """a = the script's theme (no previous episode, no series default); b the other brightness and another family;
    c a third family."""
    got = tp.pick_themes(DOC, ep(tmp_path))
    (a, wa), (b, _), (c, _) = got
    assert a == "lecture-light" and wa == "稿子目前寫的"
    assert CODE_THEMES[b]["light"] != CODE_THEMES[a]["light"]
    assert len({tp.family(t) for t, _ in got}) == 3


def test_previous_episode_and_series_list(tmp_path):
    """a numbered episode takes the previous one's theme; series.json "themes" sets the order the others come from."""
    ep(tmp_path, "001_a", {**DOC, "theme": "dark-gold"}, series={"themes": ["editorial-serif", "collage", "newsroom"]})
    got = tp.pick_themes(DOC, ep(tmp_path, "002_b"))
    assert got[0] == ("dark-gold", "上一集（001_a）用的")
    assert [t for t, _ in got[1:]] == ["editorial-serif", "collage"]


def test_estimate_spreads_words_and_writes_nothing(tmp_path):
    P = ep(tmp_path)
    est = {b["id"]: b for b in tp.estimate(DOC)}
    b1 = est["B1"]
    assert [w for w, _ in b1["tokens"]][:4] == ["這", "家", "咖", "啡"] and b1["tokens"][1][1] - b1["tokens"][0][1] == pytest.approx(.2)
    assert b1["duration"] == pytest.approx(tp.LEAD + 16 * .2 + .5)
    assert est["B4"]["text"] == "怎麼找到這裡的？" and est["B3"]["text"] == "客人"   # B4 cuts in mid-line at 「怎麼」
    assert not (P / "beats.json").exists()


def test_beats_distinct_scenes_no_recordings():
    """three code beats, one per scene, never web_evidence; script order kept; --beats must name code beats."""
    assert [b["id"] for b in tp.pick_beats(DOC, [])] == ["B1", "B4", "B6"]
    assert [b["id"] for b in tp.pick_beats(DOC, ["B5"])] == ["B5"]
    with pytest.raises(SystemExit, match="not code beats"):
        tp.pick_beats(DOC, ["B2"])


def test_missing_pictures_become_placeholders(tmp_path):
    P = ep(tmp_path)
    (P / "preview").mkdir()
    (P / "stills").mkdir()
    (P / "stills/a.jpg").write_bytes(b"x")
    got = tp.fill_missing(P, BEATS[3]["params"])
    assert got["photo"][0]["src"] == "stills/a.jpg" and got["photo"][1] == {"src": "preview/_photo.jpg"}
    assert (P / "preview/_photo.jpg").exists()


def test_palette_and_rise_only_where_they_apply():
    d = {**DOC, "palette": "被擄", "rise": "green"}
    assert "palette" in tp.theme_doc(d, "collage") and "rise" not in tp.theme_doc(d, "collage")
    assert "palette" not in tp.theme_doc(d, "newsroom") and tp.theme_doc(d, "newsroom")["rise"] == "green"


def test_compose_makes_a_2x2_film_and_a_sheet(tmp_path):
    P = ep(tmp_path)
    themes = [("lecture-light", "a"), ("newsroom", "b"), ("editorial-serif", "c")]
    for t, _ in themes:
        (P / f"preview/code_{t}").mkdir(parents=True)
        for i in ("B1", "B6"):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=s=1920x1080:d=1:r=30", "-pix_fmt", "yuv420p",
                            str(P / f"preview/code_{t}/{i}.mp4")], check=True)
    tp.compose(P, themes, ["B1", "B6"], 2.0)
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height:format=duration", "-of", "json",
                            str(P / "preview/theme_preview.mp4")], capture_output=True, text=True, check=True)
    info = json.loads(probe.stdout)
    assert (info["streams"][0]["width"], info["streams"][0]["height"]) == (1920, 1080)
    assert float(info["format"]["duration"]) == pytest.approx(2.0, abs=.1)
    from PIL import Image
    assert Image.open(P / "preview/theme_preview.jpg").size == (640 * 2, 360 * 3)


def test_pick_writes_theme_and_drops_palette(tmp_path):
    P = ep(tmp_path, doc={**DOC, "palette": "被擄"})
    tp.pick(P / "doc.json", json.loads((P / "doc.json").read_text()), P, "newsroom", "想要新聞感")
    d = json.loads((P / "doc.json").read_text())
    assert d["theme"] == "newsroom" and "palette" not in d and d["lines"] == LINES
    assert json.loads((P / "preview/theme_choice.json").read_text())["why"] == "想要新聞感"
    with pytest.raises(SystemExit, match="not a theme"):
        tp.pick(P / "doc.json", d, P, "nope", "x")


def test_theme_streak(tmp_path):
    """the ledger: three in a row with the same theme is reported, two is not."""
    a = ep(tmp_path, "001_a", {**DOC, "theme": "newsroom"}) / "doc.json"
    b = ep(tmp_path, "002_b", {**DOC, "theme": "newsroom"}) / "doc.json"
    assert "same theme 3 episodes in a row: newsroom" in doc_lint.theme_streak({"theme": "newsroom"}, [b, a])
    assert doc_lint.theme_streak({"theme": "newsroom"}, [b]) is None
    assert doc_lint.theme_streak({"theme": "dark-gold"}, [b, a]) is None
