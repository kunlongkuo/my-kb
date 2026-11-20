"""plan_diff.py（s2f-1b D6）：以命令列執行，看 exit code 與輸出。"""
import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "plan_diff.py"

PLAN = {
    "total": 12.0, "width": 1920, "height": 1080, "fps": 30,
    "media": [
        {"path": "/a/shot1.mp4", "name": "shot1.mp4", "kind": "video", "hasAudio": False, "duration": 5.833333,
         "width": 1920, "height": 1080},
        {"path": "/a/shot2.mp4", "name": "shot2.mp4", "kind": "video", "hasAudio": False, "duration": 6.0,
         "width": 1920, "height": 1080},
        {"path": "/a/01_阿明.wav", "name": "01_阿明.wav", "kind": "audio", "hasAudio": True, "duration": 5.0},
        {"path": "/a/bgm.wav", "name": "bgm.wav", "kind": "audio", "hasAudio": True, "duration": 12.0},
    ],
    "tracks": [
        {"type": "video", "segs": [
            {"path": "/a/shot1.mp4", "name": "shot1.mp4", "start": 0.0, "dur": 5.834, "src": 0.0, "vol": 1.0},
            {"path": "/a/shot2.mp4", "name": "shot2.mp4", "start": 5.834, "dur": 6.0, "src": 0.0, "vol": 1.0}]},
        {"type": "text", "segs": [
            {"text": "第一句", "start": 0.5, "end": 3.0, "y": -0.8, "bg": "#000000", "bga": 0.7},
            {"text": "第二句", "start": 3.0, "end": 6.0, "y": -0.8, "bg": "#000000", "bga": 0.7}]},
        {"type": "audio", "segs": [
            {"path": "/a/01_阿明.wav", "name": "01_阿明.wav", "start": 0.0, "dur": 5.0, "src": 0.0, "vol": 1.4142}]},
        {"type": "audio", "segs": [
            {"path": "/a/bgm.wav", "name": "bgm.wav", "start": 0.0, "dur": 12.0, "src": 0.0, "vol": 1.0}]},
    ],
}


def run(tmp_path, old, new):
    a, b = tmp_path / "old.json", tmp_path / "new.json"
    a.write_text(json.dumps(old, ensure_ascii=False), encoding="utf-8")
    b.write_text(json.dumps(new, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), str(a), str(b)], capture_output=True, text=True)
    assert "Traceback" not in r.stderr, r.stderr
    return r


def test_01_same_plan_exit_0(tmp_path):
    r = run(tmp_path, PLAN, PLAN)
    assert r.returncode == 0, r.stdout
    assert "differences: 0" in r.stdout


def test_02_start_plus_1ms_passes_and_reports_0_001(tmp_path):
    new = copy.deepcopy(PLAN)
    assert new["tracks"][0]["segs"][1]["start"] == 5.834
    new["tracks"][0]["segs"][1]["start"] = 5.835
    r = run(tmp_path, PLAN, new)
    assert r.returncode == 0, r.stdout
    assert "track 0 video: segments 2 / 2, max time difference 0.001" in r.stdout


def test_03_start_plus_2ms_fails(tmp_path):
    new = copy.deepcopy(PLAN)
    new["tracks"][0]["segs"][1]["start"] = 5.836
    r = run(tmp_path, PLAN, new)
    assert r.returncode == 1
    assert "track 0 (video) segment 1 start: 5.834 != 5.836 (off by 0.002)" in r.stdout


def test_04_text_segment_removed_fails(tmp_path):
    new = copy.deepcopy(PLAN)
    del new["tracks"][1]["segs"][1]
    r = run(tmp_path, PLAN, new)
    assert r.returncode == 1
    assert "track 1 (text) segment count: 2 != 1" in r.stdout


def test_05_other_folder_same_filename_passes(tmp_path):
    new = json.loads(json.dumps(PLAN).replace('"/a/', '"/b/c/'))
    assert new["tracks"][0]["segs"][0]["path"] == "/b/c/shot1.mp4"
    r = run(tmp_path, PLAN, new)
    assert r.returncode == 0, r.stdout


def test_06_volume_change_fails(tmp_path):
    new = copy.deepcopy(PLAN)
    new["tracks"][3]["segs"][0]["vol"] = 1.4142
    r = run(tmp_path, PLAN, new)
    assert r.returncode == 1
    assert "track 3 (audio) segment 0 vol: 1.0 != 1.4142" in r.stdout


def test_07_track_order_swapped_fails(tmp_path):
    new = copy.deepcopy(PLAN)
    new["tracks"][0], new["tracks"][1] = new["tracks"][1], new["tracks"][0]
    r = run(tmp_path, PLAN, new)
    assert r.returncode == 1
    assert "track type order: ['video', 'text', 'audio', 'audio'] != ['text', 'video', 'audio', 'audio']" in r.stdout


@pytest.mark.parametrize("a,b,expect", [(5.834, 5.835, 1), (5.076, 5.077, 1), (0.1, 0.3, 200)])
def test_ms_is_integer_milliseconds(a, b, expect):
    sys.path.insert(0, str(SCRIPT.parent))
    from plan_diff import ms
    assert abs(ms(a) - ms(b)) == expect
