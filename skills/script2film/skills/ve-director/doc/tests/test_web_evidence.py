"""doc_code.web_params: a quoted page must name its source, and the crop and highlight boxes must lie inside the image."""
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from doc_code import web_params  # noqa: E402

BEAT = {"id": "B13"}


def project(tmp_path):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=white:s=800x600", "-frames:v", "1",
                    str(tmp_path / "page.png")], check=True)
    return tmp_path


def test_good_params_get_the_image_size(tmp_path):
    p = web_params(project(tmp_path), BEAT, {"src": "page.png", "source": "example.com · 2026-10-29", "crop": [0, 100, 800, 300],
                                             "marks": [{"box": [10, 150, 200, 30], "at": "x"}]})
    assert p["_img"] == [800, 600]


@pytest.mark.parametrize("params,msg", [
    ({"src": "page.png"}, "needs source"),
    ({"src": "page.png", "source": "  "}, "needs source"),
    ({"src": "page.mp4", "source": "s"}, "png / jpg"),
    ({"src": "page.png", "source": "s", "crop": [0, 0, 900, 600]}, "crop must be"),
    ({"src": "page.png", "source": "s", "crop": [0, 100, 800, 300], "marks": [{"box": [10, 50, 200, 30]}]}, "mark box"),
    ({"src": "page.png", "source": "s", "marks": [{"box": [10, 50, 0, 30]}]}, "mark box"),
])
def test_bad_params_stop(tmp_path, params, msg):
    with pytest.raises(SystemExit, match=msg):
        web_params(project(tmp_path), BEAT, params)
