"""金鑰檔的位置：只讀 ~/.config/script2film/secrets.json，家目錄別處的金鑰檔一律不讀。
HOME 指到 tmp_path，相關環境變數都清掉，檔裡只放假值。"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_common  # noqa: E402

KEYS = ("GROQ_API_KEY", "ELEVENLABS_API_KEY", "ELEVEN_API_KEY")


@pytest.fixture
def home(monkeypatch, tmp_path):
    for k in KEYS:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path


def write_new(home, data):
    f = home / ".config/script2film/secrets.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(data), encoding="utf-8")


def test_secret_new_file_only(home):
    write_new(home, {"GROQ_API_KEY": "new"})
    assert doc_common.secret("GROQ_API_KEY") == "new"
    assert doc_common.groq_key() == "new"


def test_only_the_new_file_is_read(home):
    assert doc_common.SECRET_FILES == ("~/.config/script2film/secrets.json",)


def test_other_secrets_files_in_home_are_not_read(home):
    for name in (".secrets.json", ".old_secrets.json"):
        (home / name).write_text(json.dumps({"GROQ_API_KEY": "old"}), encoding="utf-8")
    assert doc_common.secret("GROQ_API_KEY") is None
    write_new(home, {"GEMINI_API_KEY": "g"})
    assert doc_common.secret("GROQ_API_KEY") is None


def test_groq_key_missing_everywhere_stops(home):
    assert doc_common.secret("GROQ_API_KEY") is None
    with pytest.raises(SystemExit) as e:
        doc_common.groq_key()
    assert "script2film/secrets.json" in str(e.value)


def test_eleven_key_either_name(home):
    write_new(home, {"ELEVEN_API_KEY": "short-name"})
    assert doc_common.eleven_key() == "short-name"
    write_new(home, {"ELEVEN_API_KEY": "short-name", "ELEVENLABS_API_KEY": "long-name"})
    assert doc_common.eleven_key() == "long-name"
