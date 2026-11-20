import json
import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import flow_ingest as fi  # noqa: E402


def touch(p: Path, age_s: float, now: float) -> Path:
    p.write_bytes(b"x")
    os.utime(p, (now - age_s, now - age_s))
    return p


def test_kind_of():
    assert fi.kind_of(Path("a.MP4")) == "video"
    assert fi.kind_of(Path("a.wav")) == "music"
    assert fi.kind_of(Path("a.jpg")) is None


def test_pick_latest_newest_of_kind(tmp_path):
    now = time.time()
    old = touch(tmp_path / "old.mp4", 120, now)
    new = touch(tmp_path / "new.mp4", 10, now)
    touch(tmp_path / "song.mp3", 5, now)
    assert fi.pick_latest([old, new, tmp_path / "song.mp3"], "video", 600, now) == new


def test_pick_latest_ignores_files_outside_window(tmp_path):
    now = time.time()
    stale = touch(tmp_path / "stale.mp4", 3600, now)
    assert fi.pick_latest([stale], "video", 600, now) is None


def test_pick_latest_waits_for_newer_partial(tmp_path):
    now = time.time()
    done = touch(tmp_path / "a.mp4", 30, now)
    part = touch(tmp_path / "b.mp4.crdownload", 5, now)
    assert fi.pick_latest([done, part], "video", 600, now) is None


def test_sidecar_fields():
    m = fi.sidecar(kind="music", model="Lyria", settings="", prompt="p", source_name="s.mp3", sha256="ab",
                   seconds=180.5, created="2026-11-21T00:00:00")
    assert m["provider"] == "Google Flow Music"
    assert "SynthID" in m["notice"] and "Flow Music" in m["notice"]
    assert m["seconds"] == 180.5 and m["prompt"] == "p"


def test_set_bgm_keeps_other_keys():
    doc = {"bgm": {"src": "old.wav", "gain_db": -36}, "title": "t"}
    out = fi.set_bgm(doc, "flow_bgm.mp3", "c")
    assert out["bgm"] == {"src": "flow_bgm.mp3", "gain_db": -36, "credit": "c"}
    assert doc["bgm"]["src"] == "old.wav"  # input untouched


def test_main_moves_and_writes_sidecar(tmp_path, monkeypatch):
    monkeypatch.setattr(fi, "probe_seconds", lambda p: 3.0)
    dl = tmp_path / "dl"
    dl.mkdir()
    (dl / "Untitled.mp3").write_bytes(b"audio")
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "doc.json").write_text(json.dumps({"bgm": {"gain_db": -36}}), encoding="utf-8")
    (tmp_path / "p.txt").write_text("jazz lullaby\n", encoding="utf-8")
    rc = fi.main(["--latest", "music", "--downloads", str(dl), "--to", str(proj / "flow_bgm.mp3"),
                  "--model", "Flow Music", "--prompt-file", str(tmp_path / "p.txt"), "--doc", str(proj / "doc.json")])
    assert rc == 0
    assert not (dl / "Untitled.mp3").exists()
    side = json.loads((proj / "flow_bgm.mp3.flow.json").read_text(encoding="utf-8"))
    assert side["prompt"] == "jazz lullaby" and side["source_name"] == "Untitled.mp3" and len(side["sha256"]) == 64
    doc = json.loads((proj / "doc.json").read_text(encoding="utf-8"))
    assert doc["bgm"] == {"gain_db": -36, "src": "flow_bgm.mp3",
                          "credit": "Music: Google Flow Music (Flow Music), AI-generated"}


def test_main_refuses_overwrite_and_wrong_extension(tmp_path, monkeypatch):
    monkeypatch.setattr(fi, "probe_seconds", lambda p: None)
    src = tmp_path / "a.mp4"
    src.write_bytes(b"v")
    dest = tmp_path / "shot1.mp4"
    dest.write_bytes(b"old")
    with pytest.raises(SystemExit):
        fi.main(["--from", str(src), "--to", str(dest), "--model", "m"])
    with pytest.raises(SystemExit):
        fi.main(["--from", str(src), "--to", str(tmp_path / "shot1.mov"), "--model", "m"])
    assert src.exists() and dest.read_bytes() == b"old"


def test_main_doc_rejected_for_video(tmp_path):
    src = tmp_path / "a.mp4"
    src.write_bytes(b"v")
    with pytest.raises(SystemExit):
        fi.main(["--from", str(src), "--to", str(tmp_path / "s.mp4"), "--model", "m", "--doc", str(tmp_path / "d.json")])
    assert src.exists()
