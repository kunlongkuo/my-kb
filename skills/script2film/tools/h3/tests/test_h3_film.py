"""tools/h3/h3_film.py: planning, the guards before compute units are spent, and collecting into the film's folders."""
import json
import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools/h3"))
import h3_film  # noqa: E402

BREWING = REPO / "examples/brewing"


def test_country_check_follows_the_licence_territory():
    assert h3_film.country_of('{\n  "ip": "1.2.3.4",\n  "country": "SG",\n  "org": "AS396982 Google LLC"\n}') == "SG"
    assert h3_film.territory_ok("SG") and h3_film.territory_ok("TW") and h3_film.territory_ok("JP")
    for cc in ("US", "GB", "KR", "DE", "FR", "NL"):
        assert not h3_film.territory_ok(cc)
    assert h3_film.country_of("timeout") is None and not h3_film.territory_ok(None)   # unknown never passes


def test_host_lines_are_placed_inside_their_part():
    lines = [{"start": 0.08, "end": 3.49, "text": "一"}, {"start": 4.1, "end": 7.7, "text": "二"},
             {"start": 12.6, "end": 17.6, "text": "三"}]
    assert h3_film.host_lines(lines, {"start": 0.0, "end": 12.3}) == [(0.08, "一"), (4.1, "二")]
    got = h3_film.host_lines(lines, {"start": 12.3, "end": 22.4})
    assert len(got) == 1 and got[0][1] == "三" and abs(got[0][0] - 0.3) < 1e-9


def test_host_prompt_is_long_enough_and_carries_every_line_verbatim():
    said = [(0.08, "示意的小咖啡店，同一包豆子，有兩種做法。"), (4.1, "示意的手沖，一杯要等四分鐘，一天賣三十杯。")]
    p = h3_film.host_prompt("a man in his late thirties, grey shirt, green apron", "a bright cafe", said)
    assert "<d>[Mandarin] 示意的小咖啡店，同一包豆子，有兩種做法。</d>" in p and "At 00:04.100" in p
    assert "@圖片1" in p and "@音訊1" in p
    assert not h3_film.check_jobs([{"id": "host1", "type": "video", "prompt": p, "seconds": 12.3}])


def test_check_jobs_stops_drafts_short_prompts_and_bad_lengths():
    long = "word " * 400
    bad = h3_film.check_jobs([
        {"id": "shot1", "type": "video", "prompt": long, "seconds": 5, "draft": True},
        {"id": "shot2", "type": "video", "prompt": "a short prompt", "seconds": 5},
        {"id": "shot3", "type": "video", "prompt": long, "seconds": 20},
        {"id": "shot4", "type": "video", "prompt": long, "seconds": 5},
    ])
    assert [b.split(":")[0] for b in bad] == ["shot1", "shot2", "shot3"]


@pytest.fixture
def brewing(tmp_path):
    P = tmp_path / "brewing"
    (P / "tts").mkdir(parents=True)
    shutil.copy2(BREWING / "doc.json", P / "doc.json")
    shutil.copy2(BREWING / "premade/tts/lines.json", P / "tts/lines.json")
    # examples/*/beats.json is generated and gitignored, and doc_align needs a local transcriber: this is its output
    # for the premade voice
    shutil.copy2(Path(__file__).parent / "fixtures/brewing_beats.json", P / "beats.json")
    return P


def test_plan_shots_drafts_one_job_per_ve_beat(brewing):
    doc = json.loads((brewing / "doc.json").read_text(encoding="utf-8"))
    jobs = h3_film.plan_shots(doc, brewing, doc.get("theme", "collage"), "480P")
    ve = [b for b in json.loads((brewing / "beats.json").read_text(encoding="utf-8"))["beats"] if b["source"] == "ve"]
    assert [j["id"] for j in jobs] == [f"shot{k}" for k in range(1, len(ve) + 1)]
    assert all(j["draft"] and j["mode"] == "text" and 2 <= j["seconds"] <= 15 for j in jobs)
    assert h3_film.check_jobs(jobs)                     # drafts are never sent as they are


def test_plan_host_refuses_parts_over_15_s(brewing):
    doc = json.loads((brewing / "doc.json").read_text(encoding="utf-8"))
    (brewing / "host/parts").mkdir(parents=True)
    (brewing / "host/parts.json").write_text(json.dumps([{"k": 1, "start": 0.0, "end": 22.4}]), encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        h3_film.plan_host(doc, brewing, BREWING / "refs/host_look.jpg", "a man", None, "480P")
    assert "--max 15 --min 4" in str(e.value)


def test_plan_host_writes_locked_jobs(brewing):
    doc = json.loads((brewing / "doc.json").read_text(encoding="utf-8"))
    parts = brewing / "host/parts"
    parts.mkdir(parents=True)
    (brewing / "host/parts.json").write_text(json.dumps([{"k": 1, "start": 0.0, "end": 12.3}, {"k": 2, "start": 12.3, "end": 22.4}]))
    for k in (1, 2):
        (parts / f"part{k}.mp3").write_bytes(b"x")
    jobs = h3_film.plan_host(doc, brewing, BREWING / "refs/host_look.jpg", "a man, grey shirt, green apron", "a cafe", "480P")
    assert [(j["id"], j["mode"], j["drive_audio"], j["seconds"]) for j in jobs] == [
        ("host1", "ref", "inputs/part1.mp3", 12.3), ("host2", "ref", "inputs/part2.mp3", 10.1)]
    assert (brewing / "h3/inputs/look.jpg").exists() and (brewing / "h3/inputs/part2.mp3").exists()
    assert not h3_film.check_jobs(jobs)


def test_collect_puts_clips_where_the_cut_reads_them(brewing):
    doc = json.loads((brewing / "doc.json").read_text(encoding="utf-8"))
    out = brewing / "h3/out"
    out.mkdir(parents=True)
    for n in ("shot1.mp4", "host1.mp4", "results.json", "shot1_strip.mp4"):
        (out / n).write_bytes(b"new")
    from doc_themes import ve_look
    look = ve_look(doc, doc.get("theme", "collage"))
    old = brewing / "host/parts/part1.mp4"
    old.parent.mkdir(parents=True)
    old.write_bytes(b"old")
    h3_film.collect(doc, brewing, doc.get("theme", "collage"))
    assert (brewing / f"ve_{look}/shot1.mp4").read_bytes() == b"new"
    assert old.read_bytes() == b"new" and (brewing / "host/parts/part1.bak.mp4").read_bytes() == b"old"


def test_run_stops_before_any_gpu_without_confirmation(brewing, monkeypatch):
    calls = []
    monkeypatch.setattr(h3_film, "colab", lambda *a, **k: calls.append(a) or "")
    (brewing / "h3").mkdir()
    job = {"id": "host1", "type": "video", "prompt": "word " * 400, "seconds": 10}
    (brewing / "h3/manifest.json").write_text(json.dumps({"jobs": [dict(job, draft=True)]}))
    with pytest.raises(SystemExit) as e:
        h3_film.run(brewing, {"gpu": "L4", "keep": 0, "confirmed": True, "skip": None})
    assert "draft" in str(e.value)
    (brewing / "h3/manifest.json").write_text(json.dumps({"jobs": [job]}))
    with pytest.raises(SystemExit) as e:
        h3_film.run(brewing, {"gpu": "L4", "keep": 0, "confirmed": False, "skip": None})
    assert "--confirmed" in str(e.value) and calls == []


def test_run_releases_the_gpu_outside_the_territory(brewing, monkeypatch, tmp_path):
    calls = []
    def fake_colab(*a, **k):
        calls.append(a[0])
        return '{"country": "US"}' if a[0] == "exec" else ""
    monkeypatch.setattr(h3_film, "colab", fake_colab)
    monkeypatch.setattr(h3_film, "upstream", lambda: tmp_path)
    import checklist
    monkeypatch.setattr(checklist, "gate", lambda *a, **k: None)
    (brewing / "h3").mkdir()
    (brewing / "h3/manifest.json").write_text(json.dumps({"jobs": [{"id": "host1", "type": "video", "prompt": "word " * 400, "seconds": 10}]}))
    with pytest.raises(SystemExit) as e:
        h3_film.run(brewing, {"gpu": "L4", "keep": 0, "confirmed": True, "skip": None})
    assert "US" in str(e.value) and calls == ["sessions", "new", "exec", "stop"]


def test_region_from_the_machine_url():
    url = "https://8080-gpu-a100-s-ass1c0-3kk87d95esmg1-c.asia-southeast1.prod.r.colab.dev"
    assert h3_film.region_of(url) == "asia-southeast1" and h3_film.region_country("asia-southeast1") == "SG"
    assert h3_film.region_country("asia-northeast3") == "KR" and not h3_film.territory_ok("KR")   # Seoul is outside
    assert h3_film.region_country("us-central1") == "US"
    assert h3_film.region_country("europe-west4") is None and h3_film.region_of(None) is None    # unknown never passes


def _sessions(tmp_path, monkeypatch, url):
    f = tmp_path / "sessions.json"
    f.write_text(json.dumps({"s": {"url": url}} if url else {}))
    monkeypatch.setenv("COLAB_CLI_SESSIONS", str(f))


def test_machine_country_retries_then_reads_the_region(tmp_path, monkeypatch):
    answers = iter(["timeout", "timeout", '{"country": "SG"}'])
    monkeypatch.setattr(h3_film, "colab", lambda *a, **k: next(answers))
    assert h3_film.machine_country("s", "probe.py", wait=0) == ("SG", "IP lookup")      # third try answers
    calls = []
    monkeypatch.setattr(h3_film, "colab", lambda *a, **k: calls.append(a) or "timeout")
    _sessions(tmp_path, monkeypatch, "https://8080-x-c.asia-east1.prod.r.colab.dev")
    assert h3_film.machine_country("s", "probe.py", wait=0) == ("TW", "region asia-east1") and len(calls) == 3
    _sessions(tmp_path, monkeypatch, None)
    assert h3_film.machine_country("s", "probe.py", wait=0) == (None, "no machine URL")


def test_run_says_when_the_machine_did_not_boot(brewing, monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(h3_film, "colab", lambda *a, **k: calls.append(a[0]) or "")
    monkeypatch.setattr(h3_film, "upstream", lambda: tmp_path)
    monkeypatch.setattr(h3_film, "PROBE_WAIT", 0)
    monkeypatch.setattr(h3_film.time, "sleep", lambda s: None)
    _sessions(tmp_path, monkeypatch, None)
    import checklist
    monkeypatch.setattr(checklist, "gate", lambda *a, **k: None)
    (brewing / "h3").mkdir()
    (brewing / "h3/manifest.json").write_text(json.dumps({"jobs": [{"id": "host1", "type": "video", "prompt": "word " * 400, "seconds": 10}]}))
    with pytest.raises(SystemExit) as e:
        h3_film.run(brewing, {"gpu": "L4", "keep": 0, "confirmed": True, "skip": None})
    assert "did not boot" in str(e.value) and calls == ["sessions", "new", "exec", "exec", "exec", "stop"]
