"""peak_weight: generated shots on more than 40% of the lines are reported, never failed."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from doc_lint import peak_weight  # noqa: E402


def doc(kinds):
    """One line per beat; kind "ve", "gen" (a generated clip), "host" (a host clip) or "code"."""
    beats = []
    for i, k in enumerate(kinds, 1):
        b = {"id": f"B{i}", "lines": [i], "source": {"gen": "clip", "host": "clip"}.get(k, k)}
        if k in ("gen", "host"):
            b["clip"] = "host/tp_host.mp4" if k == "host" else "extra_live/ve_live/shot1.mp4"
        beats.append(b)
    return {"beats": beats, "lines": [{"text": "x"} for _ in kinds]}


def test_two_of_five_is_fine():
    assert peak_weight(doc(["ve", "code", "gen", "code", "code"])) == []


def test_three_of_five_is_reported():
    out = peak_weight(doc(["ve", "gen", "ve", "code", "code"]))
    assert len(out) == 1 and "3 of 5 lines (60%" in out[0]


def test_host_clips_are_not_generated():
    assert peak_weight(doc(["host", "host", "host", "ve", "code"])) == []
