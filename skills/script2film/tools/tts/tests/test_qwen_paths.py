"""qwen_paths.models_dir: the models folder, with the same default as doc_tts.py."""
import os
import sys
from pathlib import Path

os.environ.setdefault("S2F_CONFIG", "none")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import qwen_paths


def test_models_var_wins():
    assert qwen_paths.models_dir({"S2F_QWEN_TTS_MODELS": "/m", "S2F_QWEN_TTS_DIR": "/a/qwen"}) == Path("/m")


def test_old_name_still_read():
    assert qwen_paths.models_dir({"QWEN_TTS_MODELS": "/old"}) == Path("/old")


def test_falls_back_to_sibling_of_tts_dir():
    assert qwen_paths.models_dir({"S2F_QWEN_TTS_DIR": "/a/qwen"}) == Path("/a/_models")
    assert qwen_paths.models_dir({"QWEN_TTS_DIR": "/a/qwen"}) == Path("/a/_models")


def test_nothing_set():
    assert qwen_paths.models_dir({}) is None


def test_voice_language_defaults_to_chinese():
    assert qwen_paths.voice_language(None) == ("Chinese", True)
    assert qwen_paths.voice_language("zh") == ("Chinese", True)


def test_voice_language_english_is_not_converted():
    assert qwen_paths.voice_language("en") == ("English", False)


def test_voice_language_unknown_stops():
    import pytest
    with pytest.raises(SystemExit) as e:
        qwen_paths.voice_language("fr")
    assert "fr" in str(e.value)
