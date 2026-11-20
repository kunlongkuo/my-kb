"""doc_voice pitch(): median speaking pitch; by_pitch(): the film's pitch and which takes may be picked."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_voice  # noqa: E402


def tone(hz, sec=1.0):
    t = np.arange(int(48000 * sec)) / 48000
    return (np.sin(2 * np.pi * hz * t) + .5 * np.sin(2 * np.pi * 2 * hz * t)).astype(np.float32)


def test_pitch_of_a_tone():
    assert abs(doc_voice.pitch(tone(120)) - 120) < 2
    assert abs(doc_voice.pitch(tone(220)) - 220) < 4


def test_pitch_of_silence_is_none():
    assert doc_voice.pitch(np.zeros(48000, np.float32)) is None
    assert doc_voice.pitch(np.zeros(100, np.float32)) is None


def take(score, f0):
    return (score, None, [], 0, 1.0, None, 0.0, f0)


def test_by_pitch_keeps_only_takes_near_the_best_score():
    rows = [[take(1.0, 120), take(0.97, 180), take(0.80, 125)], [take(0.9, 126), take(0.9, 200)]]
    target, ok = doc_voice.by_pitch(rows, 0.05)
    assert [c[7] for c in ok[0]] == [120, 180]          # the 0.80 take misreads the line: never picked for its pitch
    assert target == 153.0                              # median of 120, 180, 126, 200
    assert min(ok[1], key=lambda c: abs(c[7] - target))[7] == 126


def test_by_pitch_without_voiced_takes():
    assert doc_voice.by_pitch([[take(1.0, None)]], 0.05) == (None, [[]])
