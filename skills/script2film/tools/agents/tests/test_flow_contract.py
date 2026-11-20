"""docs/FLOW.md 寫給「換別家平台」的檔名約定，要和程式組路徑的字串一致。
程式改了檔名而文件沒改，這裡會紅。"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
FLOW = (REPO / "docs/FLOW.md").read_text(encoding="utf-8")
SCRIPTS = REPO / "skills/ve-director/doc/scripts"


def test_flow_names_the_shot_and_host_files():
    for pattern in ("ve_<look>/shotK.mp4", "host/parts/partK.mp3", "host/parts/partK.mp4", "storyboard_<look>.md"):
        assert pattern in FLOW, pattern


def test_the_code_still_builds_those_names():
    cut = (SCRIPTS / "doc_cut.py").read_text(encoding="utf-8")
    assert 'f"ve_{ve_look(doc, theme)}"' in cut and 'f"shot{' in cut
    host = (SCRIPTS / "doc_host.py").read_text(encoding="utf-8")
    assert 'f"part{k}.mp3"' in host and "f\"part{p['k']}.mp4\"" in host and '"host/parts"' in host
    assert 'f"storyboard_{' in (SCRIPTS / "doc_runsheet.py").read_text(encoding="utf-8")
    assert 'theme.startswith("lecture-")' in (SCRIPTS / "doc_themes.py").read_text(encoding="utf-8")


def test_flow_tells_the_agent_to_check_text_timing_after_f3():
    """s2f-3d-host-late-reveal D2: the step is in F3 and names both reports; doc_lint still prints them."""
    f3 = FLOW[FLOW.index("## F3 Timing"):FLOW.index("## F4 ")]
    assert "--beats <project>/beats.json" in f3 and "late_reveal" in f3 and "read_time" in f3
    lint = (SCRIPTS / "doc_lint.py").read_text(encoding="utf-8")
    assert '"late_reveal: ok"' in lint and '"read_time: ok"' in lint


def test_flow_settles_the_look_image_before_the_host_commands():
    """s2f-3d-host-late-reveal D1: reference photo is not the look; the user picks; the voice fits the person."""
    b = FLOW[FLOW.index("## Optional B"):FLOW.index("## Optional C")]
    look, cmds = b.index("### The look image"), b.index("tp_host.py <project>")
    assert look < cmds
    for phrase in ("reference material", "head to waist", "TP_ASPECT", "let the user pick", "tp_upimg.py",
                   "The voice has to fit the person on screen"):
        assert phrase in b[look:cmds], phrase


def test_example_outputs_are_ignored_but_tools_are_not():
    """s2f-3d-host-late-reveal D4: rules are scoped to examples/*/, so tools/tts/ and friends stay tracked."""
    import subprocess
    def ignored(path):
        return subprocess.run(["git", "check-ignore", "-q", path], cwd=REPO).returncode == 0
    for path in ("examples/x/tts/voice.wav", "examples/x/host/tp_host.mp4", "examples/x/ve_flat/shot1.mp4",
                 "examples/x/beats.json", "examples/x/nightly/sheet.jpg", "examples/x/checklist_answers.json",
                 "examples/x/script_approval.json"):
        assert ignored(path), path
    for path in ("tools/tts/README.md", "tools/nightly/check.py", "examples/x/doc.json", "examples/x/facts.md",
                 "examples/x/refs/narrator.wav"):
        assert not ignored(path), path


def test_examples_named_in_the_documents_exist_and_premade_files_are_tracked():
    """s2f-3e-two-examples: every examples/<name> a document points at is there; the premade files are not ignored
    although the same names one level up (the film's own outputs) are."""
    import re
    import subprocess
    names = set()
    for doc in ("docs/FLOW.md", "README.md", "README.zh-TW.md", "AGENTS.md", "skills/script2film/SKILL.md"):
        names |= set(re.findall(r"examples/([a-z][a-z0-9_-]*)", (REPO / doc).read_text(encoding="utf-8")))
    assert {"coffee", "brewing"} <= names
    for name in names:
        assert (REPO / "examples" / name / "doc.json").exists(), name
    for path in ("examples/brewing/premade/tts/voice.wav", "examples/brewing/premade/tts/lines.json",
                 "examples/brewing/premade/ve_flat/shot1.mp4", "examples/brewing/premade/host/parts.json",
                 "examples/brewing/premade/host/parts/part1.mp4"):
        assert (REPO / path).exists(), path
        assert subprocess.run(["git", "check-ignore", "-q", path], cwd=REPO).returncode != 0, path
