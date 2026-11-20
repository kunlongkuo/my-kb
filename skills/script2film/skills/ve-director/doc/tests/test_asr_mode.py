"""doc.json "asr" (s2f-1a D3): "local" (the default) transcribes with whisper.cpp only, never asks for a Groq key and never
runs Scribe; an empty local transcript is cached instead of falling back to Groq; "cloud" keeps the Groq + Scribe path.
local_asr is faked: no model runs and no online service is called."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import doc_align  # noqa: E402
import doc_common  # noqa: E402
import doc_voice  # noqa: E402

TAKES = ["aaa_1.wav", "aaa_2.wav", "bbb_1.wav"]
HEARD = {"aaa_1.wav": "第一句", "aaa_2.wav": "", "bbb_1.wav": "第二句"}   # one take transcribes to an empty string
WORDS = {"segments": [{"text": "第一句", "start": 0.4, "end": 1.2,
                       "words": [{"word": "第一句", "start": 0.4, "end": 1.2}]}]}


def no_groq_key():
    raise AssertionError("groq_key called in local mode")


@pytest.fixture
def env(monkeypatch, tmp_path):
    """Local mode setup: S2F_WHISPER_CPP_MODEL set, groq_key raises, local_asr is fake, every subprocess.run is recorded."""
    monkeypatch.setenv("S2F_WHISPER_CPP_MODEL", str(tmp_path / "model.bin"))
    monkeypatch.setattr(doc_common, "groq_key", no_groq_key)
    calls, asr_calls = [], []

    def fake_local_asr(paths, lang, words=False):
        asr_calls.append(([Path(p).name for p in paths], words))
        return {Path(p): (WORDS if words else HEARD[Path(p).name]) for p in paths}

    real_run = subprocess.run

    def recording_run(cmd, *a, **kw):
        calls.append(" ".join(map(str, cmd)))
        return real_run(cmd, *a, **kw)

    for mod in (doc_common, doc_voice, doc_align):
        if hasattr(mod, "local_asr"):
            monkeypatch.setattr(mod, "local_asr", fake_local_asr)
    monkeypatch.setattr(subprocess, "run", recording_run)
    return {"mp": monkeypatch, "calls": calls, "asr_calls": asr_calls, "P": tmp_path / "proj"}


def no_local(mp):
    """No local transcription model (a shell that exports it, or the retired mlx folder, must not leak in)."""
    for name in ("S2F_WHISPER_CPP_MODEL", "S2F_MLX_WHISPER_DIR", "MLX_WHISPER_DIR"):
        mp.delenv(name, raising=False)


def takes(P):
    (P / "tts_lines").mkdir(parents=True)
    paths = []
    for name in TAKES:
        (P / "tts_lines" / name).write_bytes(b"")
        paths.append(P / "tts_lines" / name)
    return [paths[:2], paths[2:]]


def doc(**kw):
    return {"lang": "zh", "lines": [{"text": "第一句"}, {"text": "第二句"}], **kw}


def aligned_project(P):
    (P / "voice.cleaned/aligned").mkdir(parents=True)
    (P / "voice.cleaned/audio.m4a").write_bytes(b"")
    (P / "tts").mkdir(parents=True, exist_ok=True)
    (P / "tts/voice.wav").write_bytes(b"")


def test_default_is_local():
    assert doc_common.asr_mode(doc()) == "local"
    assert doc_common.asr_mode(doc(asr="local")) == "local"


def test_cloud():
    assert doc_common.asr_mode(doc(asr="cloud")) == "cloud"


def test_other_value_stops():
    with pytest.raises(SystemExit) as e:
        doc_common.asr_mode(doc(asr="x"))
    assert "asr" in str(e.value) and "'x'" in str(e.value)


def test_local_never_calls_groq_or_scribe(env):
    P = env["P"]
    cands = takes(P)
    cache, key = doc_voice.transcribe_takes(doc(), P, cands)
    assert key is None
    on_disk = json.loads((P / "tts/asr_cache.json").read_text())
    assert set(on_disk) == set(TAKES) and on_disk["aaa_2.wav"] == ""   # the empty transcript is cached, not retried
    assert cache == on_disk
    # a second run finds every take cached (the empty one included) and transcribes nothing
    n = len(env["asr_calls"])
    doc_voice.transcribe_takes(doc(), P, cands)
    assert len(env["asr_calls"]) == n

    aligned_project(P)
    sj = doc_align.word_times(doc(), P)
    assert json.loads(sj.read_text())["segments"] == WORDS["segments"]
    assert not any("api.elevenlabs.io" in c for c in env["calls"])
    assert not any("api.groq.com" in c for c in env["calls"])


def test_local_without_a_model_stops(env):
    no_local(env["mp"])
    P = env["P"]
    cands = takes(P)
    with pytest.raises(SystemExit) as e:
        doc_voice.transcribe_takes(doc(), P, cands)
    assert "S2F_WHISPER_CPP_MODEL" in str(e.value)
    aligned_project(P)
    with pytest.raises(SystemExit) as e:
        doc_align.word_times(doc(), P)
    assert "S2F_WHISPER_CPP_MODEL" in str(e.value)


def test_cloud_asks_for_the_groq_key(env):
    count = []

    def counting_key():
        count.append(1)
        return "test-key"

    env["mp"].setattr(doc_common, "groq_key", counting_key)
    env["mp"].setattr(doc_voice, "groq", lambda path, key, lang, give_up_on_limit=False: HEARD[Path(path).name] or "有字")
    P = env["P"]
    cache, key = doc_voice.transcribe_takes(doc(asr="cloud"), P, takes(P))
    assert len(count) >= 1 and key == "test-key"
    assert set(cache) == set(TAKES)


def test_local_word_times_marked_whisper_cpp(env):
    P = env["P"]
    aligned_project(P)
    sj = doc_align.word_times(doc(), P)
    assert json.loads(sj.read_text())["source"] == "whisper.cpp"


# ElevenLabs Scribe called directly (s2f-naming D1). No test reaches the network: subprocess.run, scribe_words or
# local_words are fakes, and a key comes from monkeypatch (HOME points at tmp_path, so no real key file is read).

FAKE_KEY = "fake-eleven-key-0000"
SCRIBE_RESP = {"words": [
    {"text": "第一", "type": "word", "start": 0.4, "end": 0.7},
    {"text": " ", "type": "spacing", "start": 0.7, "end": 0.75},
    {"text": "(笑)", "type": "audio_event", "start": 0.75, "end": 0.9},
    {"text": "句", "type": "word", "start": None, "end": 1.2},
    {"text": "话", "type": "word", "start": 0.9, "end": 1.2},
]}


def no_key(mp, tmp_path):
    mp.delenv("ELEVENLABS_API_KEY", raising=False)
    mp.delenv("ELEVEN_API_KEY", raising=False)
    mp.setenv("HOME", str(tmp_path))


def with_key(mp, tmp_path):
    no_key(mp, tmp_path)
    mp.setenv("ELEVENLABS_API_KEY", FAKE_KEY)


def counting_local_words(env):
    n = []

    def fake(audio, lang, sj):
        n.append(1)
        sj.write_text(json.dumps({**WORDS, "source": "whisper.cpp"}), encoding="utf-8")
    env["mp"].setattr(doc_align, "local_words", fake)
    return n


def failing_scribe(audio, lang, sj):
    raise doc_align.ScribeError("HTTP 401: invalid key")


def fake_run(mp, rc, stdout, seen=None):
    def run(cmd, *a, **kw):
        if seen is not None:
            seen.append((list(map(str, cmd)), kw.get("input")))
        return subprocess.CompletedProcess(cmd, rc, stdout, "")
    mp.setattr(subprocess, "run", run)


def test_scribe_to_segments_keeps_timed_words_only():
    segs = doc_align.scribe_to_segments(SCRIBE_RESP, "en")
    assert segs == [{"words": [{"word": "第一", "start": 0.4, "end": 0.7}, {"word": "话", "start": 0.9, "end": 1.2}]}]


def test_scribe_to_segments_zh_traditional_en_unchanged():
    resp = {"words": [{"text": "简体说话", "type": "word", "start": 0.0, "end": 1.0}]}
    assert doc_align.scribe_to_segments(resp, "zh")[0]["words"][0]["word"] == "簡體說話"
    assert doc_align.scribe_to_segments(resp, "en")[0]["words"][0]["word"] == "简体说话"


def test_cloud_scribe_success_skips_local(env, tmp_path):
    with_key(env["mp"], tmp_path)
    n = counting_local_words(env)

    def ok(audio, lang, sj):
        sj.write_text(json.dumps({"segments": WORDS["segments"], "source": "elevenlabs scribe_v2"}), encoding="utf-8")
    env["mp"].setattr(doc_align, "scribe_words", ok)
    P = env["P"]
    aligned_project(P)
    sj = doc_align.word_times(doc(asr="cloud"), P)
    assert n == [] and json.loads(sj.read_text())["source"] == "elevenlabs scribe_v2"


def test_cloud_scribe_error_falls_back_to_local(env, tmp_path):
    with_key(env["mp"], tmp_path)
    n = counting_local_words(env)
    env["mp"].setattr(doc_align, "scribe_words", failing_scribe)
    P = env["P"]
    aligned_project(P)
    doc_align.word_times(doc(asr="cloud"), P)
    assert len(n) == 1


def test_cloud_scribe_error_without_local_stops(env, tmp_path):
    with_key(env["mp"], tmp_path)
    no_local(env["mp"])
    n = counting_local_words(env)
    env["mp"].setattr(doc_align, "scribe_words", failing_scribe)
    P = env["P"]
    aligned_project(P)
    with pytest.raises(SystemExit) as e:
        doc_align.word_times(doc(asr="cloud"), P)
    msg = str(e.value)
    assert e.value.code != 0 and "ELEVENLABS_API_KEY" in msg and "S2F_WHISPER_CPP_MODEL" in msg and n == []


def test_cloud_no_key_with_local_skips_scribe(env, tmp_path):
    no_key(env["mp"], tmp_path)
    n = counting_local_words(env)

    def must_not_call(audio, lang, sj):
        raise AssertionError("scribe_words called without a key")
    env["mp"].setattr(doc_align, "scribe_words", must_not_call)
    P = env["P"]
    aligned_project(P)
    doc_align.word_times(doc(asr="cloud"), P)
    assert len(n) == 1


def test_scribe_key_only_on_stdin(monkeypatch, tmp_path):
    with_key(monkeypatch, tmp_path)
    seen = []
    fake_run(monkeypatch, 0, json.dumps(SCRIBE_RESP), seen)
    sj = tmp_path / "audio.words.json"
    doc_align.scribe_words(tmp_path / "audio.m4a", "zh", sj)
    (cmd, stdin), = seen
    assert not any(FAKE_KEY in c for c in cmd)
    assert FAKE_KEY in stdin and "xi-api-key" in stdin
    assert "--config" in cmd and "-" in cmd and "api.elevenlabs.io" in " ".join(cmd)
    assert "timestamps_granularity=word" in cmd and "language_code=zh" in cmd
    assert json.loads(sj.read_text())["source"] == "elevenlabs scribe_v2"


def test_eleven_key_order(monkeypatch, tmp_path):
    no_key(monkeypatch, tmp_path)
    assert doc_common.eleven_key() is None
    monkeypatch.setenv("ELEVEN_API_KEY", "b")
    assert doc_common.eleven_key() == "b"
    monkeypatch.setenv("ELEVENLABS_API_KEY", "a")
    assert doc_common.eleven_key() == "a"


def scribe_fails(monkeypatch, tmp_path, rc, stdout):
    with_key(monkeypatch, tmp_path)
    fake_run(monkeypatch, rc, stdout)
    sj = tmp_path / "audio.words.json"
    with pytest.raises(doc_align.ScribeError) as e:
        doc_align.scribe_words(tmp_path / "audio.m4a", "zh", sj)
    assert not sj.exists()
    assert FAKE_KEY not in str(e.value)
    return str(e.value)


def test_scribe_nonzero_exit_raises(monkeypatch, tmp_path):
    assert "unauthorized" in scribe_fails(monkeypatch, tmp_path, 22, '{"detail": "unauthorized"}')


def test_scribe_not_json_raises(monkeypatch, tmp_path):
    scribe_fails(monkeypatch, tmp_path, 0, "<html>gateway</html>")


def test_scribe_json_without_words_raises(monkeypatch, tmp_path):
    scribe_fails(monkeypatch, tmp_path, 0, json.dumps({"text": "x"}))


def test_scribe_only_spacing_and_events_raises(monkeypatch, tmp_path):
    resp = {"words": [w for w in SCRIBE_RESP["words"] if w["type"] != "word"]}
    scribe_fails(monkeypatch, tmp_path, 0, json.dumps(resp))


def test_cloud_no_key_no_local_stops(env, tmp_path):
    no_key(env["mp"], tmp_path)
    no_local(env["mp"])
    P = env["P"]
    aligned_project(P)
    with pytest.raises(SystemExit) as e:
        doc_align.word_times(doc(asr="cloud"), P)
    msg = str(e.value)
    assert e.value.code != 0 and "ELEVENLABS_API_KEY" in msg and "S2F_WHISPER_CPP_MODEL" in msg


def test_need_local_asr_message_has_no_cloud(monkeypatch):
    no_local(monkeypatch)
    with pytest.raises(SystemExit) as e:
        doc_common.need_local_asr()
    assert "S2F_WHISPER_CPP_MODEL" in str(e.value) and "cloud" not in str(e.value)


def test_only_the_retired_mlx_folder_set_says_how_to_move(monkeypatch, tmp_path):
    """Only the retired S2F_MLX_WHISPER_DIR set: not a local transcriber any more; the stop says it was replaced."""
    no_local(monkeypatch)
    monkeypatch.setenv("S2F_MLX_WHISPER_DIR", str(tmp_path))
    assert doc_common.has_local_asr() is False
    with pytest.raises(SystemExit) as e:
        doc_common.need_local_asr()
    assert "replaced by whisper.cpp" in str(e.value) and "S2F_WHISPER_CPP_MODEL" in str(e.value)
