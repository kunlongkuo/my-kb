"""pytest for doc_screen's parts that need no browser (lecture-screen T1): steps parsing, the login rule, --dry pages.
The recording itself is checked by screen_sync_check.py on a real run (see tasks.md T1)."""
import json
import sys
from pathlib import Path

import pytest

DOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DOC / "scripts"))
from doc_screen import is_login_url, load_steps, pages  # noqa: E402

FIX = DOC / "tests/fixtures"


def write(tmp, spec):
    p = tmp / "s.steps.json"
    p.write_text(json.dumps(spec), encoding="utf-8")
    return p


def test_relative_urls_are_files_next_to_the_steps():
    first, steps = load_steps(FIX / "screen_password.steps.json")
    assert first == (FIX / "screen_selftest.html").resolve().as_uri()
    assert pages(first, steps) == [first, (FIX / "screen_password.html").resolve().as_uri()]


def test_absolute_urls_are_kept(tmp_path):
    first, steps = load_steps(write(tmp_path, {"url": "https://example.com/a", "steps": [{"do": "goto", "url": "http://x.org/b"}]}))
    assert pages(first, steps) == ["https://example.com/a", "http://x.org/b"]


@pytest.mark.parametrize("spec", [
    {"url": "a.html", "steps": [{"do": "hover", "sel": "#a"}]},                 # unknown action
    {"url": "a.html", "steps": [{"do": "type", "sel": "#a"}]},                  # missing text
    {"url": "a.html", "steps": [{"do": "goto", "url": "javascript:alert(1)"}]},  # scheme outside the whitelist
    {"url": "ftp://x.org/a", "steps": []},
])
def test_bad_steps_stop(tmp_path, spec):
    with pytest.raises(SystemExit):
        load_steps(write(tmp_path, spec))


def test_login_rule_reads_the_path():
    for u in ("https://x.org/login", "https://x.org/SignIn/", "https://x.org/oauth/cb", "http://127.0.0.1:8765/signin/"):
        assert is_login_url(u), u
    for u in ("https://x.org/", "https://x.org/docs?next=/login", "https://login.x.org/home"):
        assert not is_login_url(u), u


def screen_project(tmp_path, steps, **params):
    """A project whose log has one click at t=0.7 s, for screen_media's checks (they stop before any ffmpeg work)."""
    from doc_code import screen_media
    (tmp_path / "log.json").write_text(json.dumps({"steps": [{"n": 2, "do": "click", "t": 0.7, "box": [300, 200, 180, 60]}]}))
    (tmp_path / "s.webm").write_bytes(b"")
    beat = {"id": "S1", "duration": 3.0, "tokens": [["先", 0.2], ["按", 0.32], ["這", 0.44], ["裡", 0.56], ["再", 1.4], ["看", 1.52]]}
    doc = {"lang": "zh", "side": params.pop("side", {})}
    return lambda: screen_media(tmp_path, doc, beat, {"src": "s.webm", "log": "log.json", "steps": steps, **params}, tmp_path, 3.2)


def test_phrase_at_matches_lib_js():
    from doc_code import phrase_at
    beat = {"tokens": [["先", 0.2], ["按", 0.32], ["這", 0.44], ["裡", 0.56]]}
    assert phrase_at(beat, "這裡", "zh") == 0.44
    assert phrase_at(beat, {"w": "按", "d": 0.1}, "zh") == pytest.approx(0.42)
    assert phrase_at(beat, 1.5, "zh") == 1.5
    assert phrase_at(beat, "沒有", "zh") is None


@pytest.mark.parametrize("steps, params, says", [
    ([{"n": 1, "label": "x", "at": "再看", "step": 2}], {}, "set clip explicitly"),           # narration reaches the step before the recording does
    ([{"n": 1, "label": "x", "at": "這裡", "step": 2}], {"clip": [0, 10.5]}, "at most"),
    ([{"n": 1, "label": "x", "at": "這裡", "step": 2}], {"side": {"beats": ["S1"]}}, "pip, not side"),
    ([{"n": 1, "label": "x", "at": "這裡", "step": 9}], {}, "needs box"),
    ([{"n": 1, "label": "x", "at": "這裡", "step": 2}], {"frame": "phone"}, "frame must be"),
    ([{"n": 1, "label": "x", "at": "這裡", "step": 2}], {"zoom": 0.8}, "above 1"),        # zoom ≥ 1 (living-screencast §6)
    ([{"n": 1, "label": "x", "at": "這裡", "step": 2}], {"zoom": True}, "above 1"),
])
def test_screen_step_stops(tmp_path, capsys, steps, params, says):
    with pytest.raises(SystemExit) as e:
        screen_project(tmp_path, steps, **params)()
    assert says in str(e.value)
