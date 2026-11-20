"""concat_export.export()：假的 Concat client（export_wait 時用 ffmpeg 生一支小片），驗紀錄、指紋、跳過與參數檢查。"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import concat_export as ce  # noqa: E402


def make_film(path, black=False):
    vf = "drawbox=c=black:t=fill:enable='between(t,1.5,1.53)'," if black else ""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=s=320x240:r=30:d=3", "-f", "lavfi",
                    "-i", "anoisesrc=c=pink:a=0.25:d=4", "-vf", vf + "format=yuv420p",
                    "-af", "loudnorm=I=-14:TP=-2,aresample=48000,atrim=duration=3", "-c:v", "libx264", "-c:a", "aac",
                    str(path)], check=True)


class FakeConcat:
    def __init__(self, black=False, fail=False):
        self.calls, self.black, self.fail = [], black, fail

    def tool(self, name, **kw):
        self.calls.append((name, kw))
        if name == "export_start":
            self.out = kw["output"]
            return {"job": "j1"}
        if self.fail:
            return {"state": "failed"}
        make_film(self.out, self.black)
        return {"state": "done"}


@pytest.fixture
def ep(tmp_path):
    d = tmp_path / "series" / "ep1"
    d.mkdir(parents=True)
    (d / "beats.json").write_text("{}")
    return d


LOUD_OFF = {**ce.film_check.DEFAULT, "skip": [{"item": "loudness", "why": "3 秒測試片"}, {"item": "peak", "why": "同上"}]}


def test_normal_export_writes_record_and_fingerprint(ep):
    out = ep / "film.mp4"
    final = ce.export(FakeConcat(), "proj", out, ep=ep, inputs=[ep / "beats.json", ep / "missing.wav"], standard=LOUD_OFF)
    rec = json.loads((ep / "film.check.json").read_text())
    fp = json.loads((ep / "film.inputs.json").read_text())
    assert final == str(out.resolve()) and rec["ok"]
    assert rec["sha256"] == ce.film_check.sha256(out)
    assert list(fp["files"]) == ["beats.json"]   # 不存在的檔不記


def test_crf_default_and_none(ep):
    c = FakeConcat()
    ce.export(c, "proj", ep / "a.mp4", ep=ep, standard=LOUD_OFF)
    assert c.calls[0][1]["crf"] == ce.export_crf()
    c = FakeConcat()
    ce.export(c, "proj", ep / "b.mp4", ep=ep, crf=None, standard=LOUD_OFF)
    assert "crf" not in c.calls[0][1]


def test_post_result_is_what_gets_checked(ep):
    graded = ep / "film_graded.mp4"

    def post(p):
        make_film(graded)
        return str(graded)
    final = ce.export(FakeConcat(), "proj", ep / "film.mp4", ep=ep, post=post, standard=LOUD_OFF)
    assert final == str(graded.resolve())
    assert (ep / "film_graded.check.json").exists() and (ep / "film_graded.inputs.json").exists()
    assert not (ep / "film.check.json").exists()


def test_failed_check_raises(ep):
    with pytest.raises(ce.FilmCheckFailed) as e:
        ce.export(FakeConcat(black=True), "proj", ep / "film.mp4", ep=ep, standard=LOUD_OFF)
    assert not e.value.result["ok"]


def test_failed_export_raises(ep):
    with pytest.raises(RuntimeError):
        ce.export(FakeConcat(fail=True), "proj", ep / "film.mp4", ep=ep)


def test_no_check_one_item_is_logged(ep):
    ce.export(FakeConcat(black=True), "proj", ep / "film.mp4", ep=ep, standard=LOUD_OFF, no_check=[("black_mid", "測試")])
    rec = json.loads((ep / "film.check.json").read_text())
    assert rec["ok"] and "black_mid" in rec["skipped"]
    log = [json.loads(x) for x in (ep / "nightly/checklist_skips.jsonl").read_text().splitlines()]
    assert log[-1]["step"] == "export" and log[-1]["item"] == "black_mid" and log[-1]["reason"] == "測試"


def test_no_check_all_writes_no_record(ep):
    ce.export(FakeConcat(black=True), "proj", ep / "film.mp4", ep=ep, no_check=[("all", "測試")])
    assert not (ep / "film.check.json").exists()
    assert (ep / "film.inputs.json").exists()


@pytest.mark.parametrize("bad", ["bogus:x", "black_mid:", "black_mid:   ", "black_mid"])
def test_parse_no_check_rejects(bad):
    ap = argparse.ArgumentParser()
    ce.add_no_check(ap)
    a = ap.parse_args(["--no-check", bad])
    with pytest.raises(SystemExit) as e:
        ce.parse_no_check(ap, a.no_check)
    assert e.value.code == 2


def test_parse_no_check_accepts():
    ap = argparse.ArgumentParser()
    ce.add_no_check(ap)
    a = ap.parse_args(["--no-check", "black_mid: 刻意黑場 ", "--no-check", "all:x"])
    assert ce.parse_no_check(ap, a.no_check) == [("black_mid", "刻意黑場"), ("all", "x")]
