"""doc_cut.bgm duck / lift / drops: the bed drops `duck` dB while the narration speaks, comes back in pauses and over lifted
beats, and stops for drop_s from the start of a dropped beat; without them the bed is untouched."""
import math
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_cut  # noqa: E402

TOTAL = 16.0
BEATS = [{"id": "B1", "start": 0.0, "end": 9.5}, {"id": "B2", "start": 9.5, "end": TOTAL}]


def project(tmp_path):
    """bed: a steady 220 Hz tone; narration: silent except 4-7 s (a 1 kHz tone stands in for speech)."""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=f=220:d={TOTAL}", "-ar", "48000",
                    str(tmp_path / "bed.wav")], check=True)
    (tmp_path / "voice.cleaned").mkdir()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=f=1000:d={TOTAL}", "-af",
                    "volume='between(t,4,7)':eval=frame", "-ar", "48000", str(tmp_path / "voice.cleaned/audio.m4a")],
                   check=True)
    return tmp_path


def level(path, a, b):
    """RMS dB of [a, b] s."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(a), "-t", str(b - a), "-i", str(path), "-f", "f32le", "-ac", "1",
                        "-"], capture_output=True, check=True).stdout
    import array
    x = array.array("f", r)
    return 10 * math.log10(sum(v * v for v in x) / len(x) + 1e-20)


def run(P, **bgm):
    doc_cut.bgm(P, {"bgm": {"src": "bed.wav", "lufs": -36, **bgm}}, TOTAL, BEATS)
    return P / "bgm" / "bgm.wav"


def test_duck_lowers_the_bed_under_speech_only(tmp_path):
    out = run(project(tmp_path), duck=6)
    gap, speech, after = level(out, 2.0, 3.4), level(out, 4.5, 6.5), level(out, 8.0, 9.0)
    assert abs((gap - speech) - 6) < 0.5          # ducked by the asked depth under speech
    assert abs(gap - after) < 0.5                 # back up once speech ends (ramp done 0.3 s after 7 s)


def test_lift_keeps_the_bed_up_under_speech(tmp_path):
    out = run(project(tmp_path), duck=6, lift=["B1"])
    assert abs(level(out, 2.0, 3.4) - level(out, 4.5, 6.5)) < 0.5


def test_drop_silences_the_beat_start(tmp_path):
    out = run(project(tmp_path), drops=["B2"], drop_s=2.5)
    assert level(out, 10.0, 11.8) < level(out, 8.0, 9.2) - 40   # off for 9.5-12.0
    assert abs(level(out, 12.6, 12.9) - level(out, 8.0, 9.2)) < 0.5   # back before the end fade (13 s)


def test_no_duck_no_drops_leaves_the_bed_steady(tmp_path):
    out = run(project(tmp_path))
    assert abs(level(out, 2.0, 3.4) - level(out, 4.5, 6.5)) < 0.3


def test_unknown_drop_beat_stops(tmp_path):
    with pytest.raises(SystemExit, match="no such beat B9"):
        run(project(tmp_path), drops=["B9"])


@pytest.mark.parametrize("asked,used", [(30, 12.0), (-5, 0.0)])
def test_duck_is_bounded(tmp_path, asked, used, capsys):
    run(project(tmp_path), duck=asked)
    assert (f"duck {used:g} dB" in capsys.readouterr().out) == bool(used)


@pytest.mark.parametrize("bgm, bad", [
    ({"lufs": -20}, True),                 # EP1 2026-11-11: loud bed, no duck
    ({"lufs": -25, "duck": 0}, True),
    ({"lufs": -20, "duck": 6}, False),     # a current-affairs episode
    ({"lufs": -30}, False),                # at the line
    ({"lufs": -36}, False),                # vox-host FORMAT §4
    ({}, False),                           # default -40
])
def test_bed_check(bgm, bad):
    assert (doc_cut.bed_check(bgm) is not None) is bad


def test_loud_bed_without_duck_stops_the_cut(tmp_path):
    P = project(tmp_path)
    with pytest.raises(SystemExit, match="no duck"):
        doc_cut.bgm(P, {"bgm": {"src": "bed.wav", "lufs": -20}}, TOTAL, BEATS)
    assert not (P / "bgm" / "bgm.wav").exists()
