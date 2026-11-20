"""Word timing file voice.cleaned/aligned/audio.words.json (s2f-naming D7): the old name audio.scribe.json is still read
as the cache while it is not older than tts/voice.wav; new timing is always written under the new name. --retime (or
the old --rescribe) transcribes again. local_words is a fake that writes the file and counts calls: no model runs."""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_align  # noqa: E402

WORDS = {"segments": [{"words": [{"word": "第一句", "start": 0.4, "end": 1.2}]}], "source": "whisper.cpp"}
DOC = {"lang": "zh", "lines": [{"text": "第一句"}]}


@pytest.fixture
def proj(monkeypatch, tmp_path):
    """A project with tts/voice.wav at t=1000 and voice.cleaned/audio.m4a; local mode with a fake local_words."""
    monkeypatch.setenv("S2F_WHISPER_CPP_MODEL", str(tmp_path / "model.bin"))
    P = tmp_path / "proj"
    (P / "voice.cleaned/aligned").mkdir(parents=True)
    (P / "tts").mkdir()
    (P / "voice.cleaned/audio.m4a").write_bytes(b"")
    voice = P / "tts/voice.wav"
    voice.write_bytes(b"")
    os.utime(voice, (1000, 1000))
    calls = []

    def fake_local_words(audio, lang, sj):
        calls.append(sj.name)
        sj.write_text(json.dumps(WORDS), encoding="utf-8")
    monkeypatch.setattr(doc_align, "local_words", fake_local_words)
    return P, calls


def cache(P, name, t):
    f = P / "voice.cleaned/aligned" / name
    f.write_text(json.dumps(WORDS), encoding="utf-8")
    os.utime(f, (t, t))
    return f


def test_only_old_file_fresh_is_read_not_transcribed(proj):
    P, calls = proj
    old = cache(P, "audio.scribe.json", 2000)
    assert doc_align.word_times(DOC, P) == old
    assert calls == []
    assert not (P / "voice.cleaned/aligned/audio.words.json").exists()


def test_only_new_file_is_read(proj):
    P, calls = proj
    new = cache(P, "audio.words.json", 2000)
    assert doc_align.word_times(DOC, P) == new
    assert calls == []


def test_neither_transcribes_once_into_new_name(proj):
    P, calls = proj
    sj = doc_align.word_times(DOC, P)
    assert calls == ["audio.words.json"] and sj.name == "audio.words.json" and sj.exists()


def test_old_file_older_than_voice_transcribes_into_new_name(proj):
    P, calls = proj
    cache(P, "audio.scribe.json", 500)
    sj = doc_align.word_times(DOC, P)
    assert calls == ["audio.words.json"] and sj.name == "audio.words.json"


def test_rewritten_audio_m4a_does_not_expire_the_cache(proj):
    P, calls = proj
    new = cache(P, "audio.words.json", 2000)
    os.utime(P / "voice.cleaned/audio.m4a", (3000, 3000))   # main() rewrites audio.m4a on every run
    assert doc_align.word_times(DOC, P) == new
    assert calls == []


def test_retime_flag():
    assert doc_align.retime_flag(["doc_align.py", "doc.json", "--retime"]) is True
    assert doc_align.retime_flag(["doc_align.py", "doc.json", "--rescribe"]) is True
    assert doc_align.retime_flag(["doc_align.py", "doc.json"]) is False
