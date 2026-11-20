"""paths.py：音色庫從環境變數或自己的素材層找，找不到要說去哪下載；工作資料夾的三層順序。"""
import sys
from pathlib import Path

import pytest

import paths
from adapters import doc_arc


def test_soundfont_from_env_then_user_assets(tmp_path, monkeypatch):
    sf2 = tmp_path / "my.sf2"
    sf2.write_bytes(b"x")
    monkeypatch.setenv("S2F_SOUNDFONT", str(sf2))
    assert paths.soundfont() == sf2
    monkeypatch.delenv("S2F_SOUNDFONT")
    (tmp_path / "soundfonts").mkdir()
    (tmp_path / "soundfonts" / paths.SF2_NAME).write_bytes(b"x")
    monkeypatch.setenv("S2F_ASSETS_LOCAL", str(tmp_path))
    assert paths.soundfont() == tmp_path / "soundfonts" / paths.SF2_NAME


def test_missing_soundfont_says_where_to_get_it(tmp_path, monkeypatch):
    monkeypatch.delenv("S2F_SOUNDFONT", raising=False)
    monkeypatch.setenv("S2F_ASSETS_LOCAL", str(tmp_path))
    with pytest.raises(SystemExit) as e:
        paths.soundfont()
    assert paths.SF2_URL in str(e.value) and "S2F_SOUNDFONT" in str(e.value)
    monkeypatch.delenv("S2F_ASSETS_LOCAL")
    with pytest.raises(SystemExit, match="neither"):
        paths.soundfont()


def test_work_folder_order(tmp_path, monkeypatch):
    monkeypatch.delenv("S2F_SCORE_WORK", raising=False)
    monkeypatch.chdir(tmp_path)
    assert paths.work_dir() == (tmp_path / "score_out").resolve()                       # score.py, compose.py
    assert paths.work_dir(None, tmp_path / "ep" / "score") == (tmp_path / "ep" / "score").resolve()   # doc_arc.py's default
    monkeypatch.setenv("S2F_SCORE_WORK", str(tmp_path / "env"))
    assert paths.work_dir(None, tmp_path / "ep" / "score") == (tmp_path / "env").resolve()
    assert paths.work_dir(str(tmp_path / "arg"), tmp_path / "ep" / "score") == (tmp_path / "arg").resolve()
    assert doc_arc.work_dir is paths.work_dir and Path(doc_arc.SC) == Path(paths.__file__).resolve().parent
    assert str(doc_arc.SC) in sys.path
