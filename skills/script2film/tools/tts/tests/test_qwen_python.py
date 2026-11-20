"""tools/tts/qwen_python.py。不載入模型，直譯器都是假的。"""
import ast
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools/tts"))
import qwen_python  # noqa: E402

SCRIPTS = ["skills/ve-director/doc/scripts/doc_tts.py", "tools/tts/design_voices.py", "tools/tts/clone_lines.py",
           "tools/tts/speak_lines.py"]
THIRD_PARTY = {"torch", "librosa", "soundfile", "qwen_tts", "numpy", "opencc"}


@pytest.fixture
def calls(monkeypatch):
    out = []
    monkeypatch.setattr(qwen_python.os, "execv", lambda py, argv: out.append((py, argv)))
    for k in ("S2F_QWEN_TTS_DIR", "QWEN_TTS_DIR", qwen_python.MARK):
        monkeypatch.setenv(k, "")            # 先登記再刪：ensure() 自己寫進去的記號，測試結束時才會被還原
        monkeypatch.delenv(k)
    monkeypatch.setattr(sys, "argv", ["doc_tts.py", "x/doc.json", "--n", "1"])
    return out


def have(monkeypatch, found):
    monkeypatch.setattr(qwen_python.importlib.util, "find_spec", lambda name: object() if found else None)


def venv(tmp_path):
    py = tmp_path / ".venv/bin/python"
    py.parent.mkdir(parents=True)
    py.write_text("", encoding="utf-8")
    return py


def test_nothing_happens_when_qwen_tts_is_importable(calls, monkeypatch):
    have(monkeypatch, True)
    qwen_python.ensure()
    assert calls == []


@pytest.mark.parametrize("key", ["S2F_QWEN_TTS_DIR", "QWEN_TTS_DIR"])
def test_hands_over_to_the_voice_python_once(calls, monkeypatch, tmp_path, key, capsys):
    have(monkeypatch, False)
    py = venv(tmp_path)
    monkeypatch.setenv(key, str(tmp_path))
    qwen_python.ensure()
    assert calls == [(str(py), [str(py), "doc_tts.py", "x/doc.json", "--n", "1"])]
    assert qwen_python.os.environ[qwen_python.MARK] == "1" and str(py) in capsys.readouterr().err


def test_stops_instead_of_handing_over_twice(calls, monkeypatch, tmp_path):
    have(monkeypatch, False)
    venv(tmp_path)
    monkeypatch.setenv("S2F_QWEN_TTS_DIR", str(tmp_path))
    monkeypatch.setenv(qwen_python.MARK, "1")
    with pytest.raises(SystemExit) as e:
        qwen_python.ensure()
    assert calls == [] and "qwen_tts" in str(e.value)


def test_stops_when_the_voice_python_is_not_there(calls, monkeypatch, tmp_path):
    have(monkeypatch, False)
    with pytest.raises(SystemExit) as e:
        qwen_python.ensure()
    assert calls == [] and "S2F_QWEN_TTS_DIR" in str(e.value)
    monkeypatch.setenv("S2F_QWEN_TTS_DIR", str(tmp_path))            # 資料夾在，裡面沒有 .venv
    with pytest.raises(SystemExit) as e:
        qwen_python.ensure()
    assert calls == [] and str(tmp_path) in str(e.value)


@pytest.mark.parametrize("script", SCRIPTS)
def test_every_voice_script_calls_ensure_before_any_third_party_import(script):
    body = ast.parse((REPO / script).read_text(encoding="utf-8")).body
    first = min(n.lineno for n in body if isinstance(n, (ast.Import, ast.ImportFrom))
                and {(a.name if isinstance(n, ast.Import) else n.module or "").split(".")[0]
                     for a in (n.names if isinstance(n, ast.Import) else [n])} & THIRD_PARTY)
    ensure = [n.lineno for n in body if isinstance(n, ast.Expr) and ast.unparse(n) == "qwen_python.ensure()"]
    assert ensure and ensure[0] < first, (script, ensure, first)
    n = len((REPO / script).relative_to(REPO).parts) - 1
    assert f'parents[{n}] / "tools/tts"' in (REPO / script).read_text(encoding="utf-8")
