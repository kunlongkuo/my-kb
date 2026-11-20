"""tools/tp/tp_upimg.py：比例檢查與名字比對。不碰瀏覽器。"""
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tp_upimg  # noqa: E402


def image(path, w, h):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=gray:s={w}x{h}", "-frames:v", "1", str(path)],
                   check=True)
    return path


@pytest.mark.parametrize("w,h,aspect,ok", [(1920, 1080, "16:9", True), (1366, 768, "16:9", True), (1280, 960, "16:9", False),
                                           (1080, 1920, "9:16", True), (1920, 1080, "9:16", False), (1920, 1082, "16:9", False)])
def test_aspect_ok(w, h, aspect, ok):
    assert tp_upimg.aspect_ok(w, h, aspect) is ok


def test_norm_treats_underscore_and_hyphen_as_space():
    assert tp_upimg.norm("host_look") == tp_upimg.norm("Host look") == tp_upimg.norm(" host-look ") == "host look"
    assert tp_upimg.norm("host look2") != tp_upimg.norm("host look")


def test_image_size_and_problem(tmp_path):
    p = image(tmp_path / "a.jpg", 1280, 960)
    assert tp_upimg.image_size(p) == (1280, 960)
    msg = tp_upimg.aspect_problem(p, "16:9")
    assert "1280×960" in msg and "720" in msg and "--as-is" in msg
    assert tp_upimg.aspect_problem(image(tmp_path / "b.jpg", 1920, 1080), "16:9") is None
    (tmp_path / "c.jpg").write_text("not an image")
    assert "cannot read width and height" in tp_upimg.aspect_problem(tmp_path / "c.jpg", "16:9")


def test_wrong_aspect_stops_before_the_browser(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(tp_upimg, "tp", lambda *a, **k: calls.append(a) or "")
    monkeypatch.delenv("TP_ASPECT", raising=False)
    with pytest.raises(SystemExit) as e:
        tp_upimg.main([str(image(tmp_path / "look.jpg", 1280, 960))])
    assert "1280×960" in str(e.value) and calls == []


def test_as_is_and_right_aspect_reach_the_browser(tmp_path, monkeypatch, capsys):
    calls = []

    def fake(*a, **k):
        calls.append(a)
        return '"Host look"' if a[0] == "eval" and "find(" in a[1] else "1"
    monkeypatch.setattr(tp_upimg, "tp", fake)
    monkeypatch.setattr(tp_upimg.time, "sleep", lambda s: None)
    monkeypatch.delenv("TP_ASPECT", raising=False)
    tp_upimg.main(["--as-is", str(image(tmp_path / "host_look.jpg", 1280, 960))])
    assert calls and '"Host look"' in capsys.readouterr().out
    calls.clear()
    tp_upimg.main([str(image(tmp_path / "wide.jpg", 1920, 1080))])
    assert calls


@pytest.mark.parametrize("w,h,aspect,box", [(1376, 768, "16:9", (1344, 756, 16, 6)), (1344, 768, "16:9", (1344, 756, 0, 6)),
                                            (1280, 960, "16:9", (1280, 720, 0, 120)), (1920, 1080, "9:16", (594, 1056, 663, 12))])
def test_fit_box_keeps_the_largest_centred_area(w, h, aspect, box):
    assert tp_upimg.fit_box(w, h, aspect) == box
    assert tp_upimg.aspect_ok(box[0], box[1], aspect)


def test_fit_uploads_a_cropped_copy_and_leaves_the_file(tmp_path, monkeypatch, capsys):
    sent = []

    def fake(*a, **k):
        if a[0] == "upload":
            sent.append(tp_upimg.image_size(a[2]))   # 上傳當下那個檔的尺寸（暫存副本事後會刪）
            assert Path(a[2]).name == "host_study.jpg"
        return "" if a[0] == "eval" and "find(" in a[1] and not sent else '"Host study"' if a[0] == "eval" and "find(" in a[1] else "1"
    monkeypatch.setattr(tp_upimg, "tp", fake)
    monkeypatch.setattr(tp_upimg.time, "sleep", lambda s: None)
    monkeypatch.delenv("TP_ASPECT", raising=False)
    src = image(tmp_path / "host_study.jpg", 1376, 768)
    tp_upimg.main(["--fit", str(src)])
    out = capsys.readouterr().out
    assert sent == [(1344, 756)] and tp_upimg.image_size(src) == (1376, 768)
    assert "1376×768 center-cropped to 1344×756" in out and '"Host study"' in out


def test_fit_message_and_exclusive_flags(tmp_path, monkeypatch):
    monkeypatch.setattr(tp_upimg, "tp", lambda *a, **k: pytest.fail("must not touch the browser"))
    monkeypatch.delenv("TP_ASPECT", raising=False)
    p = image(tmp_path / "a.jpg", 1376, 768)
    msg = tp_upimg.aspect_problem(p, "16:9")
    assert "--fit" in msg and "1344×756" in msg and "cuts 32 px left and right" in msg and "12 px top and bottom" in msg
    with pytest.raises(SystemExit) as e:
        tp_upimg.main(["--fit", "--as-is", str(p)])
    assert "only one of" in str(e.value)
    (tmp_path / "c.jpg").write_text("not an image")
    with pytest.raises(SystemExit) as e:
        tp_upimg.main(["--fit", str(tmp_path / "c.jpg")])
    assert "cannot read width and height" in str(e.value)


def test_page_problem_and_stop_on_login(tmp_path, monkeypatch):
    assert tp_upimg.page_problem('"ok"') is None and tp_upimg.page_problem("1") is None
    assert "log in" in tp_upimg.page_problem('"login"') and "serve" in tp_upimg.page_problem("")
    calls = []

    def fake(*a, **k):
        calls.append(a)
        return '"login"'
    monkeypatch.setattr(tp_upimg, "tp", fake)
    monkeypatch.delenv("TP_ASPECT", raising=False)
    with pytest.raises(SystemExit) as e:
        tp_upimg.main([str(image(tmp_path / "look.jpg", 1920, 1080))])
    assert "then rerun" in str(e.value) and len(calls) == 1   # 只問了一次頁面狀態，沒有去按上傳
