"""doc_approval.py and the check at the top of doc_tts.py: no voice for a script the user has not approved.

The blocked runs start doc_tts.py for real: the check comes before the voice environment and the model, so they end in
about a second and make nothing. Runs that pass the check are not started here (they would load the voice model and
take minutes); approval itself is tested through doc_approval's functions, which doc_tts.py calls."""
import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]
SCRIPTS = REPO / "skills/ve-director/doc/scripts"
sys.path.insert(0, str(SCRIPTS))
import doc_approval  # noqa: E402
from doc_common import lines_hash  # noqa: E402

EXAMPLES = sorted(p.parent for p in (REPO / "examples").glob("*/expected.json"))


def project(tmp_path, example="coffee", edit=None):
    """A copy of a bundled example's doc.json (no expected.json); edit=(line index, new text) changes one line."""
    P = tmp_path / "proj"
    P.mkdir()
    doc = json.loads((REPO / "examples" / example / "doc.json").read_text(encoding="utf-8"))
    if edit:
        doc["lines"][edit[0]]["text"] = edit[1]
    (P / "doc.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return P, doc


def tts(P, *args):
    return subprocess.run([sys.executable, str(SCRIPTS / "doc_tts.py"), str(P / "doc.json"), *args],
                          capture_output=True, text=True, timeout=60)


def test_unapproved_script_is_stopped_before_any_voice(tmp_path):
    P, _ = project(tmp_path, edit=(0, "A new first line the user has not seen."))
    r = tts(P)
    assert r.returncode == doc_approval.EXIT_NOT_APPROVED == 4, r.stderr
    assert "has not been approved by the user" in r.stderr and "--script-approved" in r.stderr
    assert "do it all and report back" in r.stderr and "Traceback" not in r.stderr
    assert not (P / "tts_lines").exists() and not (P / "tts").exists() and not (P / doc_approval.RECORD).exists()
    assert "script approved" not in r.stdout


def test_flag_approves_and_records_before_any_voice(tmp_path):
    P, doc = project(tmp_path, edit=(0, "A line the user read and approved."))
    assert doc_approval.check(doc, P, flag=False)[0] is False
    ok, why = doc_approval.check(doc, P, flag=True)
    assert ok and "--script-approved" in why
    rec = json.loads((P / doc_approval.RECORD).read_text(encoding="utf-8"))["approved"]
    assert list(rec) == [lines_hash(doc, "doc")]
    assert rec[lines_hash(doc, "doc")]["source"] == "--script-approved" and rec[lines_hash(doc, "doc")]["at"]


def test_same_narration_needs_no_flag_again(tmp_path):
    P, doc = project(tmp_path, edit=(0, "A line the user read and approved."))
    doc_approval.check(doc, P, flag=True)
    first = (P / doc_approval.RECORD).read_text(encoding="utf-8")
    assert doc_approval.check(doc, P, flag=False) == (True, f"recorded in {doc_approval.RECORD}")
    doc_approval.check(doc, P, flag=True)                     # doc_tts.py checks twice when it hands itself over
    assert (P / doc_approval.RECORD).read_text(encoding="utf-8") == first


def test_changing_one_line_needs_a_new_approval(tmp_path):
    P, doc = project(tmp_path, edit=(0, "A line the user read and approved."))
    doc_approval.check(doc, P, flag=True)
    doc["lines"][2]["text"] += " Really."
    (P / "doc.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    assert doc_approval.check(doc, P, flag=False) == (False, None)
    r = tts(P)
    assert r.returncode == 4 and not (P / "tts_lines").exists(), r.stderr


def test_unreadable_record_counts_as_not_approved(tmp_path):
    P, doc = project(tmp_path, edit=(0, "Changed."))
    (P / doc_approval.RECORD).write_text("{not json", encoding="utf-8")
    assert doc_approval.check(doc, P, flag=False) == (False, None)
    assert tts(P).returncode == 4


@pytest.mark.parametrize("example", [p.name for p in EXAMPLES])
def test_bundled_example_passes_by_its_fingerprint(tmp_path, example):
    P, doc = project(tmp_path, example)                       # a copy without expected.json, as check-standalone's P4
    assert doc_approval.check(doc, P, flag=False) == (True, f"bundled example {example}")
    assert not (P / doc_approval.RECORD).exists()


@pytest.mark.parametrize("example", [p.name for p in EXAMPLES])
def test_bundled_example_with_a_changed_line_is_stopped(tmp_path, example):
    P, doc = project(tmp_path, example)
    doc["lines"][-1]["text"] += " (changed)"
    (P / "doc.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    assert doc_approval.check(doc, P, flag=False) == (False, None)
    r = tts(P)
    assert r.returncode == 4 and not (P / "tts_lines").exists(), r.stderr


@pytest.mark.parametrize("ex", EXAMPLES, ids=lambda p: p.name)
def test_example_fingerprint_matches_its_doc_json(ex):
    """Changed an example's narration? Have it reviewed, then put the new lines_hash in its expected.json."""
    want = json.loads((ex / "expected.json").read_text(encoding="utf-8")).get("script_approved")
    doc = json.loads((ex / "doc.json").read_text(encoding="utf-8"))
    assert want == lines_hash(doc, "doc"), f"{ex.name}/expected.json script_approved should be {lines_hash(doc, 'doc')}"


def test_doc_tts_checks_before_the_voice_environment():
    """The check sits above qwen_python.ensure() and every voice-model import, so a blocked run loads nothing."""
    body = ast.parse((SCRIPTS / "doc_tts.py").read_text(encoding="utf-8")).body
    src = [ast.unparse(n) for n in body]
    check = next(i for i, s in enumerate(src) if "doc_approval.check(" in s)
    stop = next(i for i, s in enumerate(src) if "EXIT_NOT_APPROVED" in s and s.startswith("if not ok"))
    ensure = src.index("qwen_python.ensure()")
    model = next(i for i, n in enumerate(body) if isinstance(n, (ast.Import, ast.ImportFrom))
                 and ("qwen_tts" in src[i] or "torch" in src[i]))
    assert check < stop < ensure < model


def test_no_switch_turns_the_check_off():
    """No environment variable or config key: the code (docstring aside) reads neither."""
    tree = ast.parse((SCRIPTS / "doc_approval.py").read_text(encoding="utf-8"))
    names = {n.attr if isinstance(n, ast.Attribute) else n.id for n in ast.walk(tree) if isinstance(n, (ast.Attribute, ast.Name))}
    mods = {a.name for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names}
    assert not names & {"environ", "getenv"} and not mods & {"os", "s2f_config"}


def test_help_names_the_flag_and_the_exit_code():
    r = subprocess.run([sys.executable, str(SCRIPTS / "doc_tts.py"), "--help"], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0 and "--script-approved" in r.stdout and "Exit code 4" in r.stdout


def lint_tail(P):
    r = subprocess.run([sys.executable, str(SCRIPTS / "doc_lint.py"), str(P / "doc.json")], capture_output=True,
                       text=True, timeout=60)
    return r.returncode, r.stdout.strip().splitlines()


def test_doc_lint_prints_the_next_step_for_an_unapproved_script(tmp_path):
    P, doc = project(tmp_path, edit=(0, "A first line nobody has approved."))
    rc, out = lint_tail(P)
    assert rc == 0 and out[-2] == "doc_lint: ok" and out[-1].startswith("Next: show the user the narration")
    assert "--script-approved" in out[-1]
    doc_approval.check(doc, P, flag=True)
    assert lint_tail(P) == (0, out[:-1])                     # approved: `doc_lint: ok` is the last line again


def test_doc_lint_on_a_bundled_example_ends_with_ok(tmp_path):
    P, _ = project(tmp_path)
    rc, out = lint_tail(P)
    assert rc == 0 and out[-1] == "doc_lint: ok"
