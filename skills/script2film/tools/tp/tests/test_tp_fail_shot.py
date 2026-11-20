"""tp_host.submit()：填表沒成功時不送渲染，並留一張頁面截圖。不碰瀏覽器。"""
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tp_host  # noqa: E402


def fake_browser(monkeypatch, shots, writes=True):
    def tp(*a, **k):
        if a[0] == "shot":
            shots.append(Path(a[1]))
            if writes:
                Path(a[1]).write_bytes(b"png")
        return ""
    monkeypatch.setattr(tp_host, "tp", tp)
    monkeypatch.setattr(tp_host, "ev", lambda js: [])
    monkeypatch.setattr(tp_host.subprocess, "run",
                        lambda *a, **k: subprocess.CompletedProcess(a, 1, stdout="card none\n", stderr=""))


def test_failed_submit_saves_a_screenshot_and_names_it(tmp_path, monkeypatch):
    shots = []
    fake_browser(monkeypatch, shots)
    with pytest.raises(SystemExit) as e:
        tp_host.submit("Ep01 part2", look="Host look", shot_dir=tmp_path)
    png = tmp_path / "fail_Ep01_part2.png"
    assert shots == [png] and str(png) in str(e.value) and "card none" in str(e.value) and "not rendering" in str(e.value)


def test_no_folder_or_no_file_keeps_the_original_error(tmp_path, monkeypatch):
    shots = []
    fake_browser(monkeypatch, shots, writes=False)
    with pytest.raises(SystemExit) as e:
        tp_host.submit("Ep01 part2", shot_dir=tmp_path)
    assert "page screenshot" not in str(e.value) and "not rendering" in str(e.value)
    with pytest.raises(SystemExit) as e:
        tp_host.submit("Ep01 part2")
    assert len(shots) == 1 and "page screenshot" not in str(e.value)
