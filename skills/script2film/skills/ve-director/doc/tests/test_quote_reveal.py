"""quote_card reveal "blur": the words come out of a blur one character after another, following the voice."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_code  # noqa: E402

TEXT = "耶和華是我的牧者，我必不致缺乏。他使我躺臥在青草地上"
# the narration says the first part from 0.5 s and the second from 3.0 s; the third part is not said
VOICE = [[c, 0.5 + k * 0.2] for k, c in enumerate("耶和華是我的牧者")] + [[c, 3.0 + k * 0.2] for k, c in enumerate("我必不致缺乏")]
BEAT = {"id": "B3", "duration": 8.0, "tokens": VOICE}
DOC = {"lang": "zh"}
READ = """(t => { tl.seek(t); const q = document.querySelector('#content .blk.card');
  return { h: q.offsetHeight, w: q.offsetWidth, n: q.querySelectorAll('.rv').length,
           shown: [...q.querySelectorAll('.rv')].map(s => +getComputedStyle(s).opacity > .99 ? 1 : 0) }; })"""


def page(tmp_path, params, t):
    out, _ = doc_code.build(tmp_path, DOC, BEAT, {"scene": "quote_card", "params": params}, "collage")
    return doc_code.page_value(out, f"{READ}({t})")


def test_same_box_with_and_without_reveal(tmp_path):
    """the card is the same size with the reveal: the lines break in the same places."""
    plain = page(tmp_path / "a", {"text": TEXT, "at": 0.3}, 8.0)
    blur = page(tmp_path / "b", {"text": TEXT, "at": 0.3, "reveal": "blur"}, 8.0)
    assert (plain["h"], plain["w"]) == (blur["h"], blur["w"]) and plain["n"] == 0 and blur["n"] == len(TEXT)
    assert blur["shown"] == [1] * len(TEXT)


def test_parts_follow_the_voice(tmp_path):
    """part 1 starts at 0.5 s (said), part 2 waits for 3.0 s (said), part 3 (not said) follows part 2 at once."""
    p = {"text": TEXT, "at": 0.3, "reveal": "blur"}
    at2 = page(tmp_path, p, 2.6)["shown"]           # part 1 (9 characters with its comma) done, part 2 not started
    assert at2[:9] == [1] * 9 and at2[9:] == [0] * (len(TEXT) - 9)
    # at 4.0 s: part 2 (3.0 s + 6 × 0.05 + 0.45 = 3.75) done; part 3 runs on from 3.35 s at 0.06 s a character, so its
    # first 4 are done (3.35 + 3 × 0.06 + 0.45 = 3.98) and its last (3.89 + 0.45) is not
    at4 = page(tmp_path, p, 4.0)["shown"]
    assert at4[:20] == [1] * 20 and at4[-1] == 0
    assert page(tmp_path, p, 7.0)["shown"] == [1] * len(TEXT)


def test_bad_reveal_stops(tmp_path):
    with pytest.raises(SystemExit, match="reveal must be"):
        doc_code.build(tmp_path, DOC, BEAT, {"scene": "quote_card", "params": {"text": TEXT, "reveal": "fade"}}, "collage")
