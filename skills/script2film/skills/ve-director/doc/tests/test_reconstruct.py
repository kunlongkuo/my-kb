"""「還原」 scenes for reconstructing an event: countdown runs to its value and turns red, grid_hot marks one cell and dims the rest,
compare items grow one line per mention."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_code  # noqa: E402

DOC = {"lang": "zh"}
BEAT = {"id": "B1", "duration": 8.0, "tokens": [["甲", 0.2], ["乙", 0.6], ["丙", 2.0], ["丁", 3.5], ["戊", 5.0]]}


def page(tmp_path, scene, params, expr):
    out, _ = doc_code.build(tmp_path, DOC, BEAT, {"scene": scene, "params": params}, "lecture-light")
    return doc_code.page_value(out, expr)


def test_countdown_ends_on_value_in_red(tmp_path):
    p = {"value": 204, "label": "授權生效（分:秒）", "at": 0.3, "dur": 3, "caption": "錢包被掃空"}
    start, end, red, bar = page(tmp_path, "countdown", p,
        "(() => { const n = document.querySelector('.num'); tl.seek(0.3, false); const a = n.textContent;"
        " tl.seek(D, false); return [a, n.textContent, n.classList.contains('hot'),"
        " gsap.getProperty('.cd-fill', 'scaleX')]; })()")
    assert (start, end, red) == ("0:00", "3:24", True) and bar == pytest.approx(0, abs=1e-3)


def test_countdown_hours_and_not_hot(tmp_path):
    end, red = page(tmp_path, "countdown", {"value": 3725, "hot": False, "bar": False},
                    "(tl.seek(D, false), [document.querySelector('.num').textContent, document.querySelector('.num').classList.contains('hot')])")
    assert (end, red) == ("1:02:05", False)


def test_grid_hot_marks_one_cell(tmp_path):
    p = {"count": 50, "title": "一筆交易，50 張授權", "at": "乙", "hot": 17, "hot_at": "丁", "caption": "生效的是第 17 張"}
    cells = page(tmp_path, "grid_hot", p,
        "(tl.seek(D, false), [...document.querySelectorAll('.cell')].map(c => [c.textContent, +getComputedStyle(c).opacity]))")
    assert len(cells) == 50 and cells[0][0] == "#01" and cells[16] == ["#17", 1]
    assert all(op == pytest.approx(.18, abs=.01) for k, (_, op) in enumerate(cells) if k != 16)


def test_grid_hot_caption_without_a_hot_cell(tmp_path):
    p = {"count": 10, "at": "乙", "caption": "十條鏈"}
    shown = page(tmp_path, "grid_hot", p,
        "(tl.seek(D, false), [...document.querySelectorAll('.blk.card')].filter(b => b.textContent.includes('十條鏈')).map(b => +getComputedStyle(b).opacity))")
    assert shown == [1]


def test_compare_items_grow_in_order(tmp_path):
    p = {"left": {"title": "發行公司｜凍結", "items": [{"text": "Tether 開始凍結", "at": "乙"}, {"text": "Circle 約 8.2 億", "at": "丁", "hot": True}]},
         "right": {"title": "攻擊者｜換成以太幣", "items": [{"text": "穩定幣 → ETH", "at": "丙"}]}}
    ops = page(tmp_path, "compare", p,
        "(() => { const rows = [...document.querySelectorAll('.blk.card')].filter(b => /凍結|Circle|ETH/.test(b.textContent) && !/｜/.test(b.textContent));"
        " const at = t => (tl.seek(t, false), rows.map(r => Math.round(+getComputedStyle(r).opacity))); return [at(0.5), at(2.5), at(D)]; })()")
    assert ops == [[0, 0, 0], [1, 0, 1], [1, 1, 1]]


def test_hot_at_is_a_checked_trigger():
    assert doc_code.missing_triggers({"hot_at": "不在稿裡"}, BEAT, "zh") == ["hot_at='不在稿裡'"]


def _clip(tmp_path):
    import subprocess
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=s=640x360:d=2:r=30", "-pix_fmt", "yuv420p",
                    str(tmp_path / "ve.mp4")], check=True)


@pytest.mark.parametrize("tone, wash", [("light", "var(--bg)"), ("dark", "rgba(10,15,25")])
def test_bg_video_goes_under_the_scene(tmp_path, tone, wash):
    _clip(tmp_path)
    spec = {"scene": "stat_count", "params": {"value": 19}, "bg_video": {"src": "ve.mp4", "tone": tone}}
    out, d = doc_code.build(tmp_path, DOC, BEAT, spec, "lecture-light")
    html = (out / "index.html").read_text(encoding="utf-8")
    assert 'src="bgv.mp4"' in html and wash in html and (out / "bgv.mp4").exists()
    # the clip (2 s) is shorter than the beat: played forward then back, the file still runs the beat's length
    import subprocess
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out / "bgv.mp4")],
                               capture_output=True, text=True).stdout)
    assert dur == pytest.approx(d, abs=0.05)
    # dark switches the drawing to lecture-dark (light text on the dimmed footage)
    from doc_themes import code_theme
    assert (code_theme("lecture-dark")["vars"] in html) == (tone == "dark")


def test_bg_video_rejects_bad_tone_and_video_scenes(tmp_path):
    _clip(tmp_path)
    with pytest.raises(SystemExit):
        doc_code.build(tmp_path, DOC, BEAT, {"scene": "stat_count", "params": {"value": 1}, "bg_video": {"src": "ve.mp4", "tone": "grey"}},
                       "lecture-light")
    with pytest.raises(SystemExit):
        doc_code.build(tmp_path, DOC, BEAT, {"scene": "ve_annotate", "params": {}, "bg_video": {"src": "ve.mp4"}}, "lecture-light")


def test_short_real_footage_stops_and_short_generated_clip_is_reported(tmp_path, capsys):
    """FORMAT §4e: a clip shorter than its beat plays forward then backward; real footage must not."""
    _clip(tmp_path)
    (tmp_path / "footage").mkdir()
    (tmp_path / "ve.mp4").rename(tmp_path / "footage" / "un_1.mp4")
    spec = {"scene": "stat_count", "params": {"value": 19}, "bg_video": {"src": "footage/un_1.mp4", "tone": "full"}}
    for key, val in (("real_footage", ["footage/"]), ("footage_credits", {"footage/un_": "Video: UN"})):
        with pytest.raises(SystemExit, match="real footage"):
            doc_code.build(tmp_path, {**DOC, key: val}, BEAT, spec, "lecture-light")
    doc_code.build(tmp_path, {**DOC, "real_footage": ["other/"]}, BEAT, spec, "lecture-light")   # not listed: generated
    assert "forward, then backward" in capsys.readouterr().out
    long_beat = {**BEAT, "duration": 1.0}                                                        # the 2 s clip covers it
    doc_code.build(tmp_path, {**DOC, "real_footage": ["footage/"]}, long_beat, spec, "lecture-light")
    assert "forward, then backward" not in capsys.readouterr().out
