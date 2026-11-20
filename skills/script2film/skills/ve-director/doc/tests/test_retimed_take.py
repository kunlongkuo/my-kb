"""A narration retimed after a host take was made: the take is cut at its own timing ("clip_in"), and an unmatched
screen that opens its line waits for the line's voice (tts/lines.json)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from doc_align import LEAD, first_screen_at  # noqa: E402
from doc_cut import clip_start  # noqa: E402


def test_clip_in_overrides_the_beat_start():
    assert clip_start({"clip_in": 18.66}, {"start": 21.01}) == 18.66


def test_without_clip_in_the_take_is_cut_at_the_beat_start():
    assert clip_start({}, {"start": 21.01}) == 21.01


def test_unmatched_first_screen_waits_for_the_voice():
    # the previous line ended at 19.0, this line is voiced from 20.0: the screen starts at the voice, not at 19.0
    assert first_screen_at(19.0, 23.0, 20.0) == 20.0 + LEAD


def test_unmatched_first_screen_keeps_a_later_start():
    assert first_screen_at(21.0, 23.0, 20.0) == 21.0


def test_unmatched_first_screen_never_runs_past_its_end():
    assert first_screen_at(19.0, 20.2, 20.0) == 20.2 - 0.3


def test_the_picture_runs_on_after_the_last_word():
    from doc_align import END_HOLD, film_end
    assert film_end(100.0, {}) == round(100.0 + END_HOLD, 2)
    assert film_end(100.0, {"end_hold": 3}) == 103.0
    assert film_end(100.0, {"end_hold": 0}) == 100.6        # never shorter than the old 0.6 s
