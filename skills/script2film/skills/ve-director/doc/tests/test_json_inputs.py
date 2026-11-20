"""JSON files read in besides doc.json (doc_common.read_json / read_beats): doc_lint --beats, the previous episode's
doc.json, beats.json for the scripts after doc_align, and drama_sheet's drama.json. Missing, broken or the wrong shape:
one line naming the file and exit 1, not a traceback (the same wording as doc_common.load)."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]
SCRIPTS = REPO / "skills/ve-director/doc/scripts"
COFFEE = REPO / "examples/coffee/doc.json"


def run(*args):
    r = subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, timeout=60)
    assert "Traceback" not in r.stderr, r.stderr
    lines = r.stderr.strip().splitlines()
    return r.returncode, lines[-1] if lines else ""


@pytest.mark.parametrize("bad,tail", [
    ("missing", "no such file (run doc_align.py first)"),
    ("broken", "not valid JSON (line 1, column 12: Expecting value)"),
    ("shape", 'no "beats" list (not a beats.json from doc_align.py)'),
])
def test_doc_lint_bad_beats_file(tmp_path, bad, tail):
    b = tmp_path / "beats.json"
    if bad == "broken":
        b.write_text('{"beats": [', encoding="utf-8")
    elif bad == "shape":
        b.write_text('{"total": 3}', encoding="utf-8")
    rc, last = run(SCRIPTS / "doc_lint.py", COFFEE, "--beats", b)
    assert rc == 1 and last == f"✗ {b.resolve()}: {tail}"


def test_doc_lint_broken_previous_episode(tmp_path):
    (tmp_path / "002_now").mkdir()
    shutil.copy(COFFEE, tmp_path / "002_now/doc.json")
    (tmp_path / "001_before").mkdir()
    prev = tmp_path / "001_before/doc.json"
    prev.write_text('{"title": ', encoding="utf-8")
    rc, last = run(SCRIPTS / "doc_lint.py", tmp_path / "002_now/doc.json")
    assert rc == 1 and last.startswith(f"✗ {prev.resolve()}: not valid JSON (line 1")


@pytest.mark.parametrize("script", ["doc_code.py", "doc_cut.py", "doc_runsheet.py"])
def test_scripts_after_align_without_beats(tmp_path, script):
    shutil.copy(COFFEE, tmp_path / "doc.json")
    rc, last = run(SCRIPTS / script, tmp_path / "doc.json")
    assert rc == 1 and last == f"✗ {(tmp_path / 'beats.json').resolve()}: no such file (run doc_align.py first)"


def test_doc_sfx_broken_beats(tmp_path):
    doc = json.loads(COFFEE.read_text(encoding="utf-8"))
    (tmp_path / "doc.json").write_text(json.dumps({**doc, "sfx_on": True}), encoding="utf-8")
    (tmp_path / "beats.json").write_text("[", encoding="utf-8")
    rc, last = run(SCRIPTS / "doc_sfx.py", tmp_path / "doc.json")
    assert rc == 1 and last.startswith(f"✗ {(tmp_path / 'beats.json').resolve()}: not valid JSON")


def test_drama_sheet_broken_file(tmp_path):
    d = tmp_path / "drama.json"
    rc, last = run(REPO / "skills/ve-director/scripts/drama_sheet.py", d)
    assert rc == 1 and last == f"✗ {d.resolve()}: no such file"
    d.write_text("{,}", encoding="utf-8")
    rc, last = run(REPO / "skills/ve-director/scripts/drama_sheet.py", d)
    assert rc == 1 and last.startswith(f"✗ {d.resolve()}: not valid JSON (line 1, column 2")
