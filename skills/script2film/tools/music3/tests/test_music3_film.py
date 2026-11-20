"""tools/music3/music3_film.py: the plan, the guards before compute units are spent, the watch loop, collect."""
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools/music3"))
import music3_film as M  # noqa: E402

CAPTION = " ".join(["word"] * 30)


def test_plan_instrumental_takes_the_film_length(tmp_path):
    (tmp_path / "tts").mkdir()
    (tmp_path / "tts/lines.json").write_text(json.dumps({"lines": [{"start": 0, "end": 5.0}, {"start": 5, "end": 41.5}]}))
    job = M.plan(tmp_path, CAPTION)
    assert job["id"] == "bgm" and job["seconds"] == 44.5 and "[Instrumental]" in job["lyrics"]
    assert json.loads((tmp_path / "music3/job.json").read_text())["seconds"] == 44.5


def test_plan_song_needs_seconds_and_a_real_caption(tmp_path):
    with pytest.raises(SystemExit, match="--seconds"):
        M.plan(tmp_path, CAPTION, "[Verse]\n夜深了")
    with pytest.raises(SystemExit, match="caption"):
        M.plan(tmp_path, "jazz, female", "[Verse]\n夜深了", 200)
    with pytest.raises(SystemExit, match="outside"):
        M.plan(tmp_path, CAPTION, "[Verse]\n夜深了", 900)
    assert M.plan(tmp_path, CAPTION, "[Verse]\n夜深了", 240)["id"] == "song"


def test_run_spends_nothing_without_confirmation_or_with_a_bad_gpu(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(M, "colab", lambda *a, **k: calls.append(a) or "")
    M.plan(tmp_path, CAPTION, "[Verse]\n夜深了", 60)
    with pytest.raises(SystemExit, match="--confirmed"):
        M.run(tmp_path, "L4", confirmed=False)
    with pytest.raises(SystemExit, match="--gpu"):
        M.run(tmp_path, "A10", confirmed=True)
    assert calls == []


def test_run_releases_the_gpu_when_the_machine_does_not_boot(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(M, "colab", lambda *a, **k: calls.append(a[0]) or "")
    M.plan(tmp_path, CAPTION, "[Verse]\n夜深了", 60)
    with pytest.raises(SystemExit, match="did not boot"):
        M.run(tmp_path, "L4", confirmed=True)
    assert calls == ["sessions", "new", "sessions", "stop"]


def _clock():
    t = [0.0]
    return (lambda: t[0]), (lambda s: t.__setitem__(0, t[0] + s))


def test_watch_ignores_dropped_connections_and_ends_only_on_the_machine_state(monkeypatch):
    """A colab-cli 'RuntimeError: Connection was lost' (it contains 'Error') must not end the run."""
    outs = iter(["RuntimeError: Connection was lost.", 'STATE {"stage": "generating"}',
                 "Traceback ... Error", 'STATE {"stage": "done", "gen_s": 300}'])
    monkeypatch.setattr(M, "exec_code", lambda *a, **k: next(outs))
    clock, sleep = _clock()
    assert M.watch("s", poll=1, clock=clock, sleep=sleep) == {"stage": "done", "gen_s": 300}


def test_watch_gives_up_after_failed_reads_or_time(monkeypatch):
    monkeypatch.setattr(M, "exec_code", lambda *a, **k: "Connection was lost")
    clock, sleep = _clock()
    assert "in a row" in M.watch("s", poll=1, clock=clock, sleep=sleep)["error"]
    monkeypatch.setattr(M, "exec_code", lambda *a, **k: 'STATE {"stage": "generating"}')
    clock, sleep = _clock()
    assert "not finished" in M.watch("s", poll=60, max_minutes=5, clock=clock, sleep=sleep)["error"]


def test_collect_sets_bgm_and_keeps_other_keys(tmp_path):
    M.plan(tmp_path, CAPTION, "[Verse]\n夜深了", 60)
    (tmp_path / "doc.json").write_text(json.dumps({"bgm": {"lufs": -40, "src": "old.wav"}}))
    (tmp_path / "music3/out").mkdir(parents=True)
    (tmp_path / "music3/out/song.wav").write_bytes(b"new")
    (tmp_path / "music3_bgm.wav").write_bytes(b"old")
    M.collect(tmp_path)
    bgm = json.loads((tmp_path / "doc.json").read_text())["bgm"]
    assert bgm == {"lufs": -40, "src": "music3_bgm.wav", "credit": M.CREDIT}
    assert (tmp_path / "music3_bgm.wav").read_bytes() == b"new" and (tmp_path / "music3_bgm.bak.wav").read_bytes() == b"old"
