"""flow: a level link's glowing core shows (2026-11-17: in pipe and lanes the core of a link with both ends at the same y did not
draw: the #flowglow filter region is a share of the path's box, and a level path's box has no height; a 1 px slope showed a
2 px sliver). Read at the end of the beat, packets hidden: the column through the middle of each link must carry the core's
colour about as thick as its stroke (pipe 12 px)."""
import io
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_code  # noqa: E402

BEAT = {"id": "B1", "duration": 4.0, "tokens": []}
NODES = [{"id": "a", "x": 360, "y": 460, "label": "A", "icon": "container", "at": .2},
         {"id": "b", "x": 960, "y": 460, "label": "B", "icon": "target", "at": .5},
         {"id": "c", "x": 1560, "y": 560, "label": "C", "icon": "shield", "at": .8}]
LINKS = [{"from": "a", "to": "b", "at": .4}, {"from": "b", "to": "c", "at": 1.0}]   # level, then sloping


def core_rows(tmp_path, look, theme):
    out, _ = doc_code.build(tmp_path, {"lang": "en"}, BEAT, {"scene": "flow", "params": {"look": look, "nodes": NODES, "links": LINKS}}, theme)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        pg = br.new_page(viewport={"width": 1920, "height": 1080})
        pg.goto((out / "index.html").resolve().as_uri(), wait_until="load")
        colour = pg.evaluate("""async () => { await window.__built; tl.seek(D, false);
          document.querySelectorAll('#ink g g').forEach(g => { if (g.querySelector('circle') && !g.querySelector('rect')) g.style.display = 'none'; });
          return [...document.querySelectorAll('#ink path')].find(p => (p.getAttribute('filter') || '').includes('flowglow')).getAttribute('stroke'); }""")
        im = Image.open(io.BytesIO(pg.screenshot(type="png"))).convert("RGB")
        br.close()
    want = tuple(int(colour[i:i + 2], 16) for i in (1, 3, 5))
    near = lambda px: sum(abs(a - b) for a, b in zip(px, want)) < 60
    # middle of each link (between the node frames): x 660 on the level link, x 1260 on the sloping one
    return [sum(near(im.getpixel((x, y))) for y in range(380, 640)) for x in (660, 1260)]


@pytest.mark.parametrize("look,theme", [("pipe", "lecture-food"), ("pipe", "collage"), ("lanes", "lecture-light")])
def test_level_link_core_shows(tmp_path, look, theme):
    level, sloped = core_rows(tmp_path, look, theme)
    assert level >= 8, (level, sloped)          # the stroke is 12 px; anti-aliased edges miss the colour test
    assert abs(level - sloped) <= 4, (level, sloped)   # as thick as on a link that slopes
