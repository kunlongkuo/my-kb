"""送 VE、送 TP、上傳三支程式開頭的清單：集過不了就在碰瀏覽器或網路之前退出；不在集資料夾裡的照常往下走。
後面真的會做事的函式都換成一叫就失敗的替身。"""
import json
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[2]
for d in ("checklist", "tp", "ve-runner", "youtube"):
    sys.path.insert(0, str(TOOLS / d))
import checklist  # noqa: E402
import items  # noqa: E402


class Reached(Exception):
    """替身被叫到：表示清單放行了。"""


def boom(*a, **k):
    raise Reached()


def failing_episode(tmp_path, monkeypatch):
    monkeypatch.setattr(items, "ITEMS", [{"id": "a", "layer": "base", "format": None, "stage": "start", "na_ok": False,
                                          "label": "a", "fn": lambda c: [("a", False, "故意不過")]}])
    ep = tmp_path / "系列" / "EP01"
    (ep / "host").mkdir(parents=True)
    (ep / "doc.json").write_text("{}", encoding="utf-8")
    (ep / "host/parts.json").write_text(json.dumps([{"k": 1}]), encoding="utf-8")
    return ep


def test_broken_item_counts_as_failed_not_crash(tmp_path):
    ep = tmp_path / "EP"
    ep.mkdir()
    (ep / "doc.json").write_text("{}", encoding="utf-8")       # 沒有 voice、lines：格式層的項目會丟例外
    out = checklist.run(ep, "start", write=False)
    assert not out["ok"] and any("could not check" in r["detail"] for r in out["items"])


def test_tp_host_stops_before_browser(tmp_path, monkeypatch, capsys):
    import tp_host
    ep = failing_episode(tmp_path, monkeypatch)
    monkeypatch.setattr(tp_host, "ensure_serve", boom)
    monkeypatch.setattr(sys, "argv", ["tp_host.py", str(ep), "--prefix", "x", "--dry-run"])
    with pytest.raises(SystemExit) as e:
        tp_host.main()
    assert e.value.code == 1 and "✗ a 故意不過" in capsys.readouterr().out


def test_tp_host_skip_goes_on_and_logs(tmp_path, monkeypatch):
    import tp_host
    ep = failing_episode(tmp_path, monkeypatch)
    monkeypatch.setattr(tp_host, "ensure_serve", boom)
    monkeypatch.setattr(sys, "argv", ["tp_host.py", str(ep), "--prefix", "x", "--dry-run", "--skip-checklist", "測試"])
    with pytest.raises(Reached):
        tp_host.main()
    row = json.loads((ep / "nightly/checklist_skips.jsonl").read_text(encoding="utf-8"))
    assert row["step"] == "tp" and row["reason"] == "測試" and row["failed"] == ["a"]


def test_ve_runner_stops_before_run(tmp_path, monkeypatch, capsys):
    import ve_runner
    ep = failing_episode(tmp_path, monkeypatch)
    sheet = ep / "runsheet.md"
    sheet.write_text("", encoding="utf-8")
    monkeypatch.setattr(ve_runner, "run", boom)
    monkeypatch.setattr(sys, "argv", ["ve_runner.py", str(sheet)])
    with pytest.raises(SystemExit) as e:
        ve_runner.main()
    assert e.value.code == 1 and "checklist for" in capsys.readouterr().out


def test_ve_runner_outside_episode_goes_on(tmp_path, monkeypatch, capsys):
    import ve_runner
    sheet = tmp_path / "story" / "board.md"
    sheet.parent.mkdir()
    sheet.write_text("", encoding="utf-8")
    monkeypatch.setattr(ve_runner, "run", boom)
    monkeypatch.setattr(sys, "argv", ["ve_runner.py", str(sheet)])
    with pytest.raises(Reached):
        ve_runner.main()
    assert "checklist does not apply" in capsys.readouterr().out


def test_ve_runner_inspect_has_no_gate(monkeypatch, capsys):
    import ve_runner
    monkeypatch.setattr(ve_runner, "run", boom)
    monkeypatch.setattr(sys, "argv", ["ve_runner.py", "--inspect"])
    with pytest.raises(Reached):
        ve_runner.main()
    assert "checklist" not in capsys.readouterr().out


def test_yt_upload_stops_before_connecting(tmp_path, monkeypatch, capsys):
    pytest.importorskip("google_auth_oauthlib")   # 上傳程式的套件裝在它自己的虛擬環境；沒有就跳過，另有實跑驗收
    import yt_upload
    ep = failing_episode(tmp_path, monkeypatch)
    monkeypatch.setattr(items, "ITEMS", [dict(items.ITEMS[0], stage="release")])
    monkeypatch.setattr(yt_upload, "build", boom)
    monkeypatch.setattr(yt_upload, "creds", boom)
    monkeypatch.setattr(sys, "argv", ["yt_upload.py", "upload", str(ep / "film.mp4"), "--title", "t", "--desc-file", str(ep / "d.txt")])
    with pytest.raises(SystemExit) as e:
        yt_upload.main()
    assert e.value.code == 1 and "✗ a 故意不過" in capsys.readouterr().out
