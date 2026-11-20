"""check.py 停住段：字幕區以上完全沒變 ≥4 秒才列；字幕區在動不影響；停到最後一格也要列。"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from check import freezes  # noqa: E402

BEATS = [{"id": "B1", "start": 0.0}, {"id": "B2", "start": 2.0}, {"id": "B3", "start": 8.0}]


def clip(tmp, parts):
    """parts: [(seconds, moving?)]; every part has a counter changing every frame in the bottom 1/6 (the subtitle band)."""
    files = []
    for k, (d, moving) in enumerate(parts):
        f = tmp / f"p{k}.mp4"
        top = f"testsrc=s=320x200:d={d}" if moving else f"color=c=gray:s=320x200:d={d}"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", top, "-f", "lavfi", "-i", f"testsrc=s=320x40:d={d}",
                        "-filter_complex", "[0]pad=320:240[a];[a][1]overlay=0:200,format=yuv420p", "-r", "30", str(f)],
                       check=True)
        files.append(f)
    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{f}'\n" for f in files))
    out = tmp / "v.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)], check=True)
    return str(out)


def test_lists_a_long_freeze_with_its_beat(tmp_path):
    got = freezes(clip(tmp_path, [(2, True), (5, False), (2, True)]), BEATS, 9.0)
    assert len(got) == 1 and got[0]["beat"] == "B2" and abs(got[0]["at"] - 2.0) < 0.1 and abs(got[0]["seconds"] - 5.0) < 0.15


def test_short_freeze_and_moving_subtitles_are_not_listed(tmp_path):
    assert freezes(clip(tmp_path, [(2, True), (3, False), (2, True)]), BEATS, 7.0) == []


def test_freeze_to_the_end(tmp_path):
    got = freezes(clip(tmp_path, [(2, True), (6, False)]), BEATS, 8.0)
    assert len(got) == 1 and abs(got[0]["seconds"] - 6.0) < 0.15


def test_content_share_tells_an_empty_card_from_a_full_one():
    import numpy as np
    from PIL import Image
    from check import content_share
    ground = np.tile(np.linspace(225, 205, 1080)[:, None, None], (1, 1920, 3)).astype(np.uint8)   # a soft vertical gradient
    assert content_share(Image.fromarray(ground)) == 0.0
    photo = ground.copy()
    photo[40:780, 140:1780] = np.random.default_rng(1).integers(0, 255, (740, 1640, 3))           # a full-frame photo
    assert content_share(Image.fromarray(photo)) > 0.8
    side = ground.copy()
    side[100:700, 1300:1860] = 40                                                                  # only the host frame
    assert content_share(Image.fromarray(side), side=True) == 0.0


def test_a_subtitle_under_half_a_second_fails_the_check(tmp_path):
    import json
    from check import short_subtitles
    assert short_subtitles(tmp_path) == (None, None)                     # an older cut: no such item
    (tmp_path / "voice.cleaned").mkdir()
    data = {"source": "final.srt", "fail": [{"start": 12.34, "dur": 0.18, "text": "對"}], "warn": []}
    (tmp_path / "voice.cleaned/short_subs.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    got, item = short_subtitles(tmp_path)
    assert got == data and item["ok"] is False and item["value"] == "1 found" and "12.3s held 0.18s: 對" in item["notes"][0]
    assert "into one screen" in item["notes"][-1]
    data["fail"] = []
    (tmp_path / "voice.cleaned/short_subs.json").write_text(json.dumps(data), encoding="utf-8")
    item = short_subtitles(tmp_path)[1]
    assert item["ok"] is True and item["notes"] == []


def test_blank_opening_lists_a_code_beat_empty_for_its_first_second(tmp_path):
    """B1 code: plain ground 1.5 s, then a picture → listed. B2 code: picture from the start, B3 ve: plain ground (not drawn
    by code), B4 code: plain ground 0.5 s then a picture (a fade-in, not a blank opening) → not listed."""
    from check import blank_openings
    parts = [("color=c=0xf4ecd8:", 1.5), ("testsrc=", 1.5), ("testsrc=", 2), ("color=c=0xf4ecd8:", 2), ("color=c=0xf4ecd8:", 0.5), ("testsrc=", 1.5)]
    files = []
    for k, (src, d) in enumerate(parts):
        f = tmp_path / f"p{k}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"{src}s=1920x1080:d={d}", "-pix_fmt", "yuv420p",
                        "-r", "30", str(f)], check=True)
        files.append(f)
    (tmp_path / "list.txt").write_text("".join(f"file '{f}'\n" for f in files))
    mp4 = tmp_path / "v.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp_path / "list.txt"), "-c", "copy",
                    str(mp4)], check=True)
    beats = [{"id": "B1", "start": 0, "source": "code"}, {"id": "B2", "start": 3, "source": "code"},
             {"id": "B3", "start": 5, "source": "ve"}, {"id": "B4", "start": 7, "source": "code"}]
    got = blank_openings(str(mp4), beats, {}, tmp_path)
    assert [x["beat"] for x in got] == ["B1"] and len(got[0]["shares"]) == 4
