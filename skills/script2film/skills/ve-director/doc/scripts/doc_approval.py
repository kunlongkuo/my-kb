"""Has the user approved this script's narration? doc_tts.py asks before voicing anything; doc_lint.py prints the next step.

Approved, in this order:
  1. doc_tts.py was run with --script-approved: the user has seen the narration and the beat table and said yes to this
     script. That is written to <project>/script_approval.json (time, narration fingerprint, source), so later runs on the
     same narration need no flag.
  2. <project>/script_approval.json already holds the fingerprint of the narration as it is now.
  3. The narration is one of the bundled examples as shipped: examples/*/expected.json "script_approved" holds the
     fingerprint of its reviewed narration.
Anything else is not approved. The fingerprint is doc_common.lines_hash (every lines[].text), so changing any line
needs a new approval. There is no setting or environment variable that turns this check off.
"""
import datetime, json
from pathlib import Path

from doc_common import lines_hash

EXIT_NOT_APPROVED = 4   # doc_tts.py's exit code for a script without approval (0–3 and 64 are taken elsewhere)
RECORD = "script_approval.json"
FLAG = "--script-approved"
EXAMPLES = Path(__file__).resolve().parents[4] / "examples"


def fingerprint(doc):
    return lines_hash(doc, "doc")


def bundled(examples=EXAMPLES):
    """{fingerprint: example name} from examples/*/expected.json "script_approved"."""
    out = {}
    for f in sorted(Path(examples).glob("*/expected.json")):
        try:
            h = json.loads(f.read_text(encoding="utf-8")).get("script_approved")
        except (OSError, ValueError, AttributeError):
            continue
        if isinstance(h, str) and h:
            out[h] = f.parent.name
    return out


def read_record(project):
    """The approvals recorded in <project>/script_approval.json, {fingerprint: entry}; missing or unreadable → {}
    (unreadable counts as not approved, never as a crash)."""
    try:
        got = json.loads((Path(project) / RECORD).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    a = got.get("approved") if isinstance(got, dict) else None
    return a if isinstance(a, dict) else {}


def status(doc, project, examples=EXAMPLES):
    """Why this narration counts as approved ("recorded in script_approval.json" / "bundled example <name>"), or None."""
    h = fingerprint(doc)
    if h in read_record(project):
        return f"recorded in {RECORD}"
    if h in (b := bundled(examples)):
        return f"bundled example {b[h]}"
    return None


def record(doc, project, now=None):
    """Write the flag's approval for this narration into <project>/script_approval.json. Kept as it is when the same
    fingerprint is already there (doc_tts.py checks twice when it hands itself over to the voice environment's Python)."""
    h = fingerprint(doc)
    have = read_record(project)
    if h in have:
        return
    when = (now or datetime.datetime.now().astimezone()).isoformat(timespec="seconds")
    have[h] = {"at": when, "source": FLAG, "lines": len(doc.get("lines", []))}
    (Path(project) / RECORD).write_text(json.dumps({"approved": have}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def check(doc, project, flag, examples=EXAMPLES):
    """(approved?, reason). With flag: approved, and recorded before any voice is made, so a run that stops halfway
    does not need the flag again. Without: status()."""
    if flag:
        record(doc, project)
        return True, f"{FLAG} (recorded in {RECORD})"
    why = status(doc, project, examples)
    return why is not None, why


def not_approved_message(doc_path):
    return "\n".join([
        f"✗ The narration in {doc_path} has not been approved by the user yet. No voice was made.",
        "  Show the user every narration line and the beat table first: the \"lines\" in doc.json (each line's text) and",
        "  the \"beats\" (for each beat: which lines, which picture). Then wait for them to say yes to this script.",
        f"  After the user approves, run this command again with {FLAG}.",
        "  \"Make me a film\", \"do it all and report back\" or \"don't ask me questions\" is not approval of this script.",
        "  If the user is not there, stop here with the script saved (doc.json, and facts.md when there is one).",
        f"  Passing {FLAG} without the user's yes to this script is reporting an approval that was not given.",
    ])


def next_step(doc, project):
    """doc_lint.py's last line after `doc_lint: ok`: the next step for a script not yet approved, else None."""
    if status(doc, project):
        return None
    return (f"Next: show the user the narration and the beat table and wait for their OK; "
            f"then run doc_tts.py with {FLAG}")
