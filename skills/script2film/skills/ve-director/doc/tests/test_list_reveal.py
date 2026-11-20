"""list_reveal (scenes/list_reveal.js): an item that wraps pushes the items below it down instead of being covered by them,
and the list stays above the subtitle band; a list whose items fit on one line keeps its places
(2026-11-17 trial: with big on, a wrapped item's second line sat under the next card)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_code  # noqa: E402

BEAT = {"id": "B1", "duration": 5.0, "tokens": [["a", 0.1]]}
LONG = "Chill the onion in the fridge for thirty minutes before you start cutting it"
# the cards once the page's fonts are in (the template builds the scene after them): [top, height, right edge, font size]
CARDS = """document.fonts.ready.then(() => new Promise(r => setTimeout(r, 50))).then(() =>
  [...document.querySelectorAll('.blk.card')].map(b => [b.offsetTop, b.offsetHeight, b.offsetLeft + b.offsetWidth, parseFloat(b.style.fontSize)]))"""


def cards(tmp_path, params):
    o, _ = doc_code.build(tmp_path, {"lang": "en"}, BEAT, {"scene": "list_reveal", "params": params}, "lecture-food")
    return doc_code.page_value(o, CARDS)


def items(*texts):
    return [{"text": t, "at": .5 + k * .7} for k, t in enumerate(texts)]


@pytest.mark.parametrize("big", [True, False])
def test_a_wrapped_item_pushes_the_next_down(tmp_path, big):
    c = cards(tmp_path, {"title": "How to stop the tears", "big": big, "hot": 1, "items": items(LONG, "Use a sharp knife")})
    assert c[0][1] > c[1][1]                                  # the long item really wraps
    assert c[1][0] >= c[0][0] + c[0][1] + 20                  # the next card starts below it, with a gap
    assert c[-1][0] + c[-1][1] <= 1080 - 200                  # above the subtitle band
    assert all(r <= 1920 - 100 for _, _, r, _ in c)           # cards stop short of the right edge


def test_three_wrapped_big_items_get_smaller_words_to_fit(tmp_path):
    c = cards(tmp_path, {"title": "How to stop the tears", "big": True, "items": items(LONG, LONG, LONG)})
    assert c[0][3] < 76
    assert all(c[k + 1][0] >= c[k][0] + c[k][1] for k in range(2))
    assert c[-1][0] + c[-1][1] <= 1080 - 200


def test_one_line_big_list_keeps_its_places(tmp_path):
    c = cards(tmp_path, {"title": "How to stop the tears", "big": True, "hot": 2,
                         "items": items("Chill the onion first", "Use a sharp knife", "Cut near a fan")})
    assert [t for t, _, _, _ in c] == [330, 520, 710]
    assert {s for _, _, _, s in c} == {76}
