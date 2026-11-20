"""Dialogue in a doc film: lines[].speaker picks a voice from doc.json "voices" (doc_common.voice_of), so one film can have a
second voice (an off-screen stall keeper answering the host). Lines without "speaker" behave exactly as before."""
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "skills/ve-director/doc/scripts"))
import doc_common  # noqa: E402
import doc_lint  # noqa: E402
import doc_voice  # noqa: E402


@pytest.fixture
def P(tmp_path):
    (tmp_path / "refs").mkdir()
    for name, data in (("host", b"host-voice"), ("keeper", b"keeper-voice")):
        (tmp_path / f"refs/{name}.wav").write_bytes(data)
        (tmp_path / f"refs/{name}.txt").write_text(f"{name} reference text", encoding="utf-8")
    return tmp_path


def doc(**extra):
    d = {"lang": "zh", "speaker": "Emma",
         "voice": {"ref_wav": "refs/host.wav", "ref_text": "refs/host.txt", "seed": 11, "tail_fade": 0.08},
         "voices": {"老闆": {"ref_wav": "refs/keeper.wav", "ref_text": "refs/keeper.txt", "seed": 21}},
         "lines": [{"text": "這些黑黑的是什麼？"}, {"text": "那是珍珠啦。", "speaker": "老闆"}],
         "beats": [{"id": "B1", "lines": [1, 2], "source": "code", "scene": "cover", "params": {}}]}
    d.update(extra)
    return d


def test_a_line_takes_its_speakers_voice_over_the_film_voice():
    d = doc()
    host, keeper = (doc_common.voice_of(d, x) for x in d["lines"])
    assert host is d["voice"]
    assert keeper["ref_wav"] == "refs/keeper.wav" and keeper["seed"] == 21
    assert keeper["tail_fade"] == 0.08                       # what the entry does not give comes from "voice"
    assert doc_common.voice_of(d, {"text": "x", "speaker": "Emma"}) is d["voice"]   # the film's own speaker
    assert [doc_common.speaker_of(d, x) for x in d["lines"]] == ["Emma", "老闆"]


def test_an_unknown_speaker_stops():
    with pytest.raises(SystemExit) as e:
        doc_common.voice_of(doc(), {"text": "x", "speaker": "路人"})
    assert "路人" in str(e.value) and "voices" in str(e.value)


def test_line_key_follows_the_voice(P):
    d = doc()
    same_text_other_voice = {"text": d["lines"][0]["text"], "speaker": "老闆"}
    assert doc_common.line_key(d, P, d["lines"][0]) != doc_common.line_key(d, P, same_text_other_voice)
    plain = doc()
    del plain["voices"]
    assert doc_common.line_key(plain, P, plain["lines"][0]) == doc_common.line_key(d, P, d["lines"][0])   # old takes stay valid


def test_who_says_a_line_is_part_of_the_approved_script():
    d = doc()
    before = doc_common.lines_hash(d)
    d["lines"][1]["speaker"] = "Emma2"
    assert doc_common.lines_hash(d) != before
    plain = {"lines": [{"text": "一"}, {"text": "二"}]}
    import hashlib
    assert doc_common.lines_hash(plain) == hashlib.sha256("一\n二".encode()).hexdigest()[:12]   # films without speakers: unchanged


def test_lint_reports_speakers_without_a_voice(P):
    assert doc_common.speaker_problems(doc(), P) == []
    bad = doc(lines=[{"text": "一", "speaker": "路人"}], voices={"老闆": {"ref_wav": "refs/none.wav"}})
    got = doc_common.speaker_problems(bad, P)
    assert 'line 1 speaker "路人" has no entry in "voices"' in got[0]
    assert any("has no ref_text" in g for g in got) and any("refs/none.wav not found" in g for g in got)
    assert any(p.startswith("speakers:") for p in doc_lint.lint(bad, {}, P))


def test_pitch_is_matched_within_each_speaker():
    take = lambda f0: (1.0, Path(f"t{f0}"), [], 0, 1.0, None, 0.0, f0)   # (score, take, cuts, hits, speech, raw, gap, f0)
    host = [[take(220), take(260)], [take(230), take(250)]]
    keeper = [[take(110), take(130)]]
    t_host, _ = doc_voice.by_pitch(host, 0.05)
    t_keeper, _ = doc_voice.by_pitch(keeper, 0.05)
    assert t_host == float(np.median([220, 260, 230, 250])) and t_keeper == 120.0
    targets, ok = doc_voice.pitch_targets([host[0], keeper[0], host[1]], ["Emma", "老闆", "Emma"], 0.05)
    assert targets == {"Emma": t_host, "老闆": 120.0}          # not one film-wide median that pulls the keeper up
    assert [len(o) for o in ok] == [2, 2, 2]
