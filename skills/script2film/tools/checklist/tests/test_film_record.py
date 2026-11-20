"""上傳前確認成片體檢紀錄（items.film_record／film_record_for）：所有片型都查，不只解說片。不跑 ffmpeg，只看紀錄與雜湊。"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "tools/nightly"))
import items  # noqa: E402
import film_check  # noqa: E402


def make(tmp_path, ok=True, inputs=True):
    ep = tmp_path / "day01"
    ep.mkdir()
    (ep / "day.json").write_text("{}")
    mp4 = ep / "daily_0501.mp4"
    mp4.write_bytes(b"film-bytes")
    src = ep / "draft_info.json"
    src.write_text("{}")
    film_check.write_record(mp4, {"ok": ok, "items": [], "listed": [], "skipped": [],
                                  "size": mp4.stat().st_size, "sha256": film_check.sha256(mp4)})
    if inputs:
        film_check.record_paths(mp4)[1].write_text(json.dumps({"base": str(ep), "files": {"draft_info.json": film_check.sha256(src)}}))
    return ep, mp4, src


def test_passing_record(tmp_path):
    ep, mp4, _ = make(tmp_path)
    assert items.film_record(mp4) == (True, mp4.name)
    assert items.film_record_for(ep)[0] is True        # 沒指定片：用資料夾裡最新那份紀錄


def test_no_record_blocks(tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    (ep / "a.mp4").write_bytes(b"x")
    assert items.film_record(ep / "a.mp4")[0] is False
    assert items.film_record_for(ep)[0] is False


def test_failed_record_blocks(tmp_path):
    _, mp4, _ = make(tmp_path, ok=False)
    assert items.film_record(mp4)[0] is False


def test_swapped_film_blocks(tmp_path):
    _, mp4, _ = make(tmp_path)
    mp4.write_bytes(b"film-bytez")                       # 同長度、內容不同
    ok, why = items.film_record(mp4)
    assert ok is False and "changed after it was checked" in why


def test_changed_input_blocks(tmp_path):
    _, mp4, src = make(tmp_path)
    src.write_text('{"x": 1}')
    ok, why = items.film_record(mp4)
    assert ok is False and "older than its inputs" in why


def test_no_fingerprint_passes_with_note(tmp_path):
    _, mp4, _ = make(tmp_path, inputs=False)
    ok, why = items.film_record(mp4)
    assert ok is True and "no inputs fingerprint" in why


def test_no_check_all_film_blocks_until_skip(tmp_path, monkeypatch):
    """--no-check all 出的片只有指紋、沒有體檢紀錄：上傳清單擋下；給 --skip-checklist 原因才放行並記帳。"""
    import checklist
    ep = tmp_path / "day02"
    ep.mkdir()
    (ep / "day.json").write_text("{}")
    mp4 = ep / "film.mp4"
    mp4.write_bytes(b"x")
    film_check.record_paths(mp4)[1].write_text(json.dumps({"base": str(ep), "files": {}}))
    monkeypatch.setattr(checklist.items, "ITEMS", [x for x in checklist.items.ITEMS if x["id"] == "film-check"])
    try:
        checklist.gate(str(mp4), "release", None, "upload", outside_ok=False)
        raise AssertionError("gate should have stopped")
    except SystemExit as e:
        assert e.code == 1
    checklist.gate(str(mp4), "release", "已人工看過", "upload", outside_ok=False)
    log = (ep / "nightly/checklist_skips.jsonl").read_text().splitlines()
    assert json.loads(log[-1])["reason"] == "已人工看過"
