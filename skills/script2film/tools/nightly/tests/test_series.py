"""series.json（FORMAT §8）：新系列只改設定不改腳本；缺欄位、缺檔要停下並說出路徑與欄位。"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from yt_meta import meta  # noqa: E402

SERIES = {"name": "試做系列", "title_fmt": "【{book}】第 {day} 集｜{chap}", "start": "2027-01-01", "publish_time": "19:30", "tz": "+08:00",
          "playlist": "PLtest", "tags": ["試做", "測試"], "backup": "projects/試做/backup.sh",
          "desc_head": "試做系列 第 {day} 集", "desc_body": "{hook}\n下一集：{next}\n配樂：{credit}", "hook_lines": [2]}
DOC = {"lines": [{"text": "問候"}, {"text": "鉤子一句"}],
       "beats": [{"id": "B1", "lines": [1, 2], "source": "code", "scene": "cover",
                  "params": {"title": "會議紀錄", "sub": "第 3 章", "badge": "第 3 天"}}],
       "bgm": {"credit": "本頻道自製（程式作曲）"}}


def episode(tmp_path, series=SERIES):
    ep = tmp_path / "試做" / "003_test"
    ep.mkdir(parents=True)
    if series is not None:
        (ep.parent / "series.json").write_text(json.dumps(series, ensure_ascii=False), encoding="utf-8")
    (ep / "doc.json").write_text(json.dumps(DOC, ensure_ascii=False), encoding="utf-8")
    return ep


def test_other_series_uses_its_own_format(tmp_path):
    ep = episode(tmp_path)
    title, desc, publish_at = meta(ep / "doc.json", "第 4 章")
    assert title == "【會議紀錄】第 3 集｜3 章"
    assert publish_at == "2027-01-03T19:30:00+08:00"
    assert desc == "試做系列 第 3 集\n\n鉤子一句\n下一集：第 4 章\n配樂：本頻道自製（程式作曲）\n"


def test_missing_field_names_field_and_path(tmp_path):
    ep = episode(tmp_path, {k: v for k, v in SERIES.items() if k != "start"})
    with pytest.raises(SystemExit) as e:
        meta(ep / "doc.json", "x")
    assert "start" in str(e.value) and str(ep.parent / "series.json") in str(e.value)


def test_no_series_json_names_path(tmp_path):
    ep = episode(tmp_path, None)
    with pytest.raises(SystemExit) as e:
        meta(ep / "doc.json", "x")
    assert str(ep.parent / "series.json") in str(e.value)


def test_cli_prints_list_joined_and_fails_on_unknown_field(tmp_path):
    ep = episode(tmp_path)
    run = lambda *a: subprocess.run([sys.executable, HERE / "series.py", ep, *a], capture_output=True, text=True)
    assert run("tags").stdout.strip() == "試做,測試"
    assert run("nope").returncode == 1


def _playlists(ep):
    return subprocess.run([sys.executable, str(HERE / "series.py"), str(ep), "playlists"], capture_output=True, text=True)


def test_playlists_adds_part_playlist_for_episode_in_range(tmp_path):
    ep = episode(tmp_path, {**SERIES, "parts": [{"from": 1, "to": 3, "playlist": "PLpart1"}, {"from": 4, "to": 9, "playlist": "PLpart2"}]})
    r = _playlists(ep)
    assert r.returncode == 0 and r.stdout.strip() == "PLtest,PLpart1"


def test_playlists_without_matching_part_warns_and_keeps_main(tmp_path):
    ep = episode(tmp_path, {**SERIES, "parts": [{"from": 10, "to": 20, "playlist": "PLlater"}]})
    r = _playlists(ep)
    assert r.returncode == 0 and r.stdout.strip() == "PLtest" and "episode 3" in r.stderr
