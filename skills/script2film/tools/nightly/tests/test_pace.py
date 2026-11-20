"""pace.py（FORMAT §4e）：每一項剛好在門檻內要過、超過要不過；沒開或缺檔的行為。"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import pace  # noqa: E402


def film(tmp, parts, name="v.mp4"):
    """parts: [(seconds, "move" | colour)]; noise fills the bottom 1/6 the whole time (the subtitle band: it must not count)."""
    files = []
    for k, (d, what) in enumerate(parts):
        f = tmp / f"{name}_{k}.mp4"
        top = f"testsrc2=s=320x200:d={d}" if what == "move" else f"color=c={what}:s=320x200:d={d}"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", top, "-f", "lavfi", "-i", f"nullsrc=s=320x40:d={d},geq=random(1)*255:128:128",
                        "-filter_complex", "[0]pad=320:240[a];[a][1]overlay=0:200,format=yuv420p", "-r", "30", str(f)], check=True)
        files.append(f)
    lst = tmp / f"{name}.txt"
    lst.write_text("".join(f"file '{f}'\n" for f in files))
    out = tmp / name
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)], check=True)
    return str(out)


def test_first_30_seconds_gap(tmp_path):
    colours = ["red", "blue", "green", "white", "black", "yellow", "red", "blue"]
    gap, cuts = pace.first30_gap(film(tmp_path, [(4, c) for c in colours], "a.mp4"))
    assert 3.8 < gap <= 4.2 and len(cuts) >= 6
    gap, cuts = pace.first30_gap(film(tmp_path, [(7, "red"), (7, "blue"), (7, "green"), (7, "white"), (4, "red")], "b.mp4"))
    assert gap > pace.GAP_S


def test_subtitle_band_does_not_count_as_a_change(tmp_path):
    gap, cuts = pace.first30_gap(film(tmp_path, [(30, "gray")]))
    assert gap == 30.0 and cuts == []


def test_longest_static(tmp_path):
    still, at, share = pace.longest_static(film(tmp_path, [(2, "move"), (5, "gray"), (2, "move")], "a.mp4"))
    assert 4.5 <= still <= 5.5 and 1.5 <= at <= 2.5 and still <= pace.STATIC_S
    still, at, share = pace.longest_static(film(tmp_path, [(2, "move"), (8, "gray"), (2, "move")], "b.mp4"))
    assert 7.5 <= still <= 8.5 and still > pace.STATIC_S


def beat(i, scene, **params):
    return {"id": i, "scene": scene, "params": params}


def test_text_limits():
    doc = {"beats": [beat("B1", "photo", label={"text": "one two three four five"}),          # 5 words: fine
                     beat("B2", "photo", label={"text": "one two three four five six"}),      # 6: over
                     beat("B3", "stat", value="1,234", unit="deaths", source="a b c d"),      # source 4: fine
                     beat("B4", "stat", source="a b c d e"),                                  # source 5: over
                     beat("B5", "quote_card", text="a much longer quotation than five words would ever allow"),   # listed only
                     beat("B6", "photo", caption="這是一行很長的中文標籤不在這條規則裡")],
           "pills": [{"text": "one two three four five six seven"}]}
    over, listed = pace.text_over(doc)
    assert [o.split()[0] for o in over] == ["B2", "B4", "pill"]
    assert len(listed) == 1 and listed[0].startswith("B5 quote_card")


MD = """| # | English | 中文 | 出處 | 畫面字 |
|---|---|---|---|---|
| 1 | a | 甲 | 畫 | x |
| 2 | b | 乙 | 念·引用 | x |
| 3 | c | 丙 | 念（當事人） | x |
| 4 | d | 丁 | 說 | x |
| 5 | e | 戊 | 念·引用 | x |

| 詞 | 念法 | 備註 |
|---|---|---|
| 6 | six | 三欄表不算 |
"""


def test_citations():
    assert pace.citations(MD) == (["2", "5"], ["3"])


def episode(tmp, kept, md=MD):
    (tmp / "sfx_plan.json").write_text(json.dumps({"kept": [{}] * kept}))
    (tmp / "稿.md").write_text(md, encoding="utf-8")
    return film(tmp, [(2, "red"), (2, "move"), (2, "blue"), (2, "move"), (2, "green"), (2, "move")])


def test_pace_items_and_rates(tmp_path, monkeypatch):
    mp4 = episode(tmp_path, kept=3)
    monkeypatch.setattr(pace, "first30_gap", lambda m: (4.0, [4.0]))   # a 12 s film: the 30 s window is tested above
    items = pace.pace(tmp_path, {"beats": []}, mp4, "稿.md", 60.0)     # one minute: 3 sounds, 2 citations
    assert [x["ok"] for x in items] == [True, True, True, True, False]
    items = pace.pace(tmp_path, {"beats": []}, mp4, "稿.md", 120.0)    # two minutes: 1.5 and 1.0 a minute
    assert all(x["ok"] for x in items)
    (tmp_path / "sfx_plan.json").write_text(json.dumps({"kept": [{}] * 7}))
    assert [x["ok"] for x in pace.pace(tmp_path, {"beats": []}, mp4, "稿.md", 120.0)][3] is False


def test_pace_stops_without_script_or_sfx_plan(tmp_path):
    mp4 = episode(tmp_path, kept=1)
    with pytest.raises(SystemExit, match="needs the script"):
        pace.pace(tmp_path, {"beats": []}, mp4, None, 60.0)
    with pytest.raises(SystemExit, match="needs the script"):
        pace.pace(tmp_path, {"beats": []}, mp4, "沒有這個檔.md", 60.0)
    (tmp_path / "sfx_plan.json").unlink()
    with pytest.raises(SystemExit, match="sfx_plan"):
        pace.pace(tmp_path, {"beats": []}, mp4, "稿.md", 60.0)
