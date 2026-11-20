"""S2F_ prefix on the tool variables (s2f-naming D6): S2F_<name> when set (non-empty), otherwise the old name <name>.
Covers doc_common.s2f_env and qwen_models_dir with either name, both, or neither; need_local_asr reads S2F_WHISPER_CPP_MODEL
(no old name: the mlx-whisper folder it replaced is only named in the stop message)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_common  # noqa: E402

NAMES = ("MLX_WHISPER_DIR", "QWEN_TTS_DIR", "QWEN_TTS_MODELS")


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    for n in NAMES:
        monkeypatch.delenv(n, raising=False)
        monkeypatch.delenv(f"S2F_{n}", raising=False)
    monkeypatch.delenv("S2F_WHISPER_CPP_MODEL", raising=False)


def test_s2f_env_only_new(monkeypatch):
    monkeypatch.setenv("S2F_QWEN_TTS_DIR", "/new")
    assert doc_common.s2f_env("QWEN_TTS_DIR") == "/new"


def test_s2f_env_only_old(monkeypatch):
    monkeypatch.setenv("QWEN_TTS_DIR", "/old")
    assert doc_common.s2f_env("QWEN_TTS_DIR") == "/old"


def test_s2f_env_both_takes_new(monkeypatch):
    monkeypatch.setenv("S2F_QWEN_TTS_DIR", "/new")
    monkeypatch.setenv("QWEN_TTS_DIR", "/old")
    assert doc_common.s2f_env("QWEN_TTS_DIR") == "/new"


def test_s2f_env_neither_is_none():
    assert doc_common.s2f_env("QWEN_TTS_DIR") is None


def test_need_local_asr_with_the_model_set(monkeypatch, tmp_path):
    monkeypatch.setenv("S2F_WHISPER_CPP_MODEL", str(tmp_path / "model.bin"))
    doc_common.need_local_asr()


@pytest.mark.parametrize("old", ["MLX_WHISPER_DIR", "S2F_MLX_WHISPER_DIR"])
def test_need_local_asr_old_mlx_folder_alone_stops(monkeypatch, tmp_path, old):
    monkeypatch.setenv(old, str(tmp_path))
    with pytest.raises(SystemExit) as e:
        doc_common.need_local_asr()
    assert "S2F_WHISPER_CPP_MODEL" in str(e.value) and "replaced by whisper.cpp" in str(e.value)


def test_need_local_asr_neither_stops_with_new_name():
    with pytest.raises(SystemExit) as e:
        doc_common.need_local_asr()
    assert "S2F_WHISPER_CPP_MODEL" in str(e.value) and "replaced" not in str(e.value)


def test_qwen_models_dir_only_old_tts_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("QWEN_TTS_DIR", str(tmp_path / "qwen3-tts"))
    assert doc_common.qwen_models_dir() == tmp_path / "_models"


def test_qwen_models_dir_neither_stops():
    with pytest.raises(SystemExit) as e:
        doc_common.qwen_models_dir()
    assert "S2F_QWEN_TTS_DIR" in str(e.value)
