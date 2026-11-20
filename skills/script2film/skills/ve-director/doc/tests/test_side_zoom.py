"""pytest for doc_code.stage_left (side.zoom): the left area stays centred on x 630 and the zoom is clamped."""
import re
import sys
from pathlib import Path

DOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DOC / "scripts"))
from doc_code import stage_left  # noqa: E402


def geometry(zoom):
    css = stage_left({"side": {"zoom": zoom}} if zoom is not None else {})
    tx, k = map(float, re.search(r"translateX\(([-\d.]+)px\) scale\(([\d.]+)\)", css).groups())
    return tx, k


def test_default_is_the_old_layout():
    tx, k = geometry(None)
    assert abs(k - 1180 / 1920) < 1e-4 and abs(tx - 40) < 0.1


def test_zoom_keeps_the_centre():
    for z in (1.0, 1.3, 1.5):
        tx, k = geometry(z)
        assert abs(tx + 960 * k - 630) < 0.1


def test_zoom_is_clamped():
    assert geometry(9)[1] == geometry(1.5)[1]
    assert geometry(-2)[1] == geometry(1.0)[1]
