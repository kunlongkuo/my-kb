"""doc_common.load: a missing doc.json, or one that is not valid JSON, stops the script with one line, not a traceback.
doc_tts.py loads through the same function but needs the voice environment to start, so it is not run here."""
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from doc_common import load  # noqa: E402

MAIN_PATH = ["doc_lint.py", "doc_voice.py", "doc_align.py", "doc_code.py", "doc_cut.py"]


def test_load_reads_a_good_doc(tmp_path):
    p = tmp_path / "doc.json"
    p.write_text('{"title": "x"}', encoding="utf-8")
    assert load(p) == ({"title": "x"}, tmp_path.resolve())


def test_load_missing_file(tmp_path):
    with pytest.raises(SystemExit) as e:
        load(tmp_path / "nope" / "doc.json")
    assert str(e.value.code) == f"✗ {(tmp_path / 'nope' / 'doc.json').resolve()}: no such file"


def test_load_bad_json_names_line_and_column(tmp_path):
    p = tmp_path / "doc.json"
    p.write_text('{\n "title": x\n}\n', encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        load(p)
    assert str(e.value.code) == f"✗ {p.resolve()}: not valid JSON (line 2, column 11: Expecting value)"


def test_load_not_utf8_and_a_folder(tmp_path):
    p = tmp_path / "doc.json"
    p.write_bytes(b'{"title": "\xff"}')
    with pytest.raises(SystemExit) as e:
        load(p)
    assert str(e.value.code) == f"✗ {p.resolve()}: not UTF-8 text"
    with pytest.raises(SystemExit) as e:
        load(tmp_path)
    assert str(e.value.code).startswith(f"✗ {tmp_path.resolve()}: cannot read it (")


@pytest.mark.parametrize("script", MAIN_PATH)
@pytest.mark.parametrize("bad", ["missing", "broken"])
def test_main_path_scripts_print_one_line(script, bad, tmp_path):
    p = tmp_path / "doc.json"
    if bad == "broken":
        p.write_text('{"title": "x",', encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPTS / script), str(p)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 1, r.stderr
    assert "Traceback" not in r.stderr
    lines = r.stderr.strip().splitlines()
    assert lines and lines[-1].startswith(f"✗ {p.resolve()}: ")
