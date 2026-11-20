"""lib.js chart helpers: sectorPath, polyPath, focusDim, evaluated in a built page."""
import re
import subprocess
import sys
from pathlib import Path

import pytest

DOC_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DOC_DIR / "scripts"))
import doc_code  # noqa: E402

DOC = {"lang": "zh"}
BEAT = {"id": "B1", "duration": 4.0, "tokens": [["甲", 0.2]]}
NUM = r"-?\d+(?:\.\d+)?(?:e-?\d+)?"


@pytest.fixture(scope="module")
def out(tmp_path_factory):
    P = tmp_path_factory.mktemp("lib")
    o, _ = doc_code.build(P, DOC, BEAT, {"scene": "bars", "params": {"items": [{"label": "a", "value": 1}, {"label": "b", "value": 2}]}},
                          "collage")
    return o


def test_sector_path_starts_on_the_outer_arc(out):
    """① sectorPath(0,0,0,100,0,π/2): first point (0,−100), the outer arc ends at (100,0) (0 at 12 o'clock, clockwise)."""
    d = doc_code.page_value(out, "sectorPath(0, 0, 0, 100, 0, Math.PI / 2)")
    m = re.match(rf"\s*M\s*({NUM})[ ,]+({NUM})\s*A\s*(?:{NUM}[ ,]+){{5}}({NUM})[ ,]+({NUM})", d)
    assert m, d
    x0, y0, x1, y1 = (float(v) for v in m.groups())
    assert abs(x0 - 0) <= 0.5 and abs(y0 + 100) <= 0.5
    assert abs(x1 - 100) <= 0.5 and abs(y1 - 0) <= 0.5
    assert "e-" not in d                                     # coordinates are rounded


def test_poly_path(out):
    """② polyPath([[0,0],[10,5]]) is 'M 0 0 L 10 5'."""
    assert doc_code.page_value(out, "polyPath([[0, 0], [10, 5]])") == "M 0 0 L 10 5"


def test_focus_dim(out):
    """③ focusDim(els, 1, t): after t + 0.4 the second element is at opacity 1, the others at 0.25."""
    ops = doc_code.page_value(out, """(() => {
      const els = [0, 1, 2].map(() => { const d = document.createElement('div'); CONTENT.appendChild(d); return d; });
      focusDim(els, 1, 1.0); tl.seek(1.4, false);
      return els.map(e => +getComputedStyle(e).opacity);
    })()""")
    assert ops == [pytest.approx(.25), pytest.approx(1), pytest.approx(.25)]


def test_lib_only_adds_lines():
    """lib.js: only new lines (git numstat deletions 0)."""
    r = subprocess.run(["git", "diff", "--numstat", "--", "lib/lib.js"], cwd=DOC_DIR, capture_output=True, text=True, check=True)
    for line in r.stdout.splitlines():
        assert line.split("\t")[1] == "0", line
