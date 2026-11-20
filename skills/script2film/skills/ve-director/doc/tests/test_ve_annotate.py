"""doc_code.ve_media: the VE clip is played, held on one frame for `hold` s, then played on; bad timing stops the build."""
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from doc_code import ve_media  # noqa: E402

DOC = {"lang": "zh"}
BEAT = {"id": "B9", "tokens": [["前", 0.2], ["面", 0.4], ["後", 1.0], ["面", 1.2]], "duration": 4.0}


def project(tmp_path):
    """A 3 s clip: 1 s red, 1 s green, 1 s blue (1920 x 1080), so held frames are easy to tell apart."""
    clip = tmp_path / "shot1.mp4"
    src = sum((["-f", "lavfi", "-i", f"color={c}:s=1920x1080:d=1:r=30"] for c in ("red", "green", "blue")), [])
    subprocess.run(["ffmpeg", "-v", "error", "-y", *src, "-filter_complex", "[0][1][2]concat=n=3:v=1[v]", "-map", "[v]",
                    "-pix_fmt", "yuv420p", str(clip)], check=True)
    out = tmp_path / "out"
    out.mkdir()
    return out


def colour_at(path, t):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(path), "-frames:v", "1", "-vf", "scale=1:1",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return max(range(3), key=lambda i: r[i])   # 0 red, 1 green, 2 blue


def test_freeze_holds_the_frame_then_plays_on(tmp_path):
    out = project(tmp_path)
    media, p = ve_media(tmp_path, DOC, BEAT, {"src": "shot1.mp4", "freeze": "後面", "hold": 1.5}, out, 4.0)
    assert 'id="vean"' in media and p["_ve"] == {"freeze": 1.0, "hold": 1.5}
    v = out / "vean.mp4"
    assert colour_at(v, 0.5) == 0          # playing: red
    assert colour_at(v, 1.3) == 1          # frozen on the first green frame...
    assert colour_at(v, 2.3) == 1          # ...for the whole hold (source green would be over by then)
    assert colour_at(v, 3.6) == 2          # played on: blue


@pytest.mark.parametrize("params,msg", [
    ({"freeze": "沒有"}, "freeze must be"),
    ({"freeze": "後面", "hold": 3.5}, "runs past the beat"),
    ({"freeze": "後面", "note": [{"text": "a"}, {"text": "b"}]}, "one note"),
])
def test_bad_freeze_stops(tmp_path, params, msg):
    out = project(tmp_path)
    with pytest.raises(SystemExit, match=msg):
        ve_media(tmp_path, DOC, BEAT, {"src": "shot1.mp4", **params}, out, 4.0)
