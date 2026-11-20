"""gen_sfx_ve.py: the prompts list, what is left to make, the manifest entry and the confirmation (no browser)."""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import gen_sfx_ve as g  # noqa: E402

sys.path.insert(0, str(HERE.parents[2] / "skills/ve-director/doc/scripts"))
import doc_sfx  # noqa: E402


def item(i="door", **kw):
    return {"id": i, "prompt": "Old door creaking, no music, no voice", "tags": ["door"], "tags_zh": ["開門"], **kw}


def test_example_file_parses():
    ps = g.parse_prompts(json.loads((HERE.parent / "sfx_prompts.example.json").read_text(encoding="utf-8")))
    assert len(ps) == 3 and [p["duration"] for p in ps] == [5, 3, 5]


@pytest.mark.parametrize("bad, word", [
    ([], "non-empty"),
    ({"id": "a"}, "non-empty"),
    ([item("Door")], "lower-case"),
    ([item("../x")], "lower-case"),
    ([item("a"), item("a")], "twice"),
    ([item(prompt="  ")], "prompt is empty"),
    ([item(tags="door")], "tags must be"),
    ([item(duration=8)], "2 to 7"),
    ([item(duration=4.5)], "2 to 7"),
    ([item(duration=True)], "2 to 7"),
])
def test_bad_prompts_stop(bad, word):
    with pytest.raises(g.PromptError, match=word):
        g.parse_prompts(bad)


def test_select_only():
    ps = g.parse_prompts([item("a"), item("b")])
    assert [p["id"] for p in g.select(ps, ["b"])] == ["b"]
    assert g.select(ps, None) == ps
    with pytest.raises(g.PromptError, match="not in the prompts file"):
        g.select(ps, ["c"])


def test_split_done_needs_entry_and_file(tmp_path):
    ps = g.parse_prompts([item("a"), item("b"), item("c")])
    man = [{"id": "a", "file": g.file_for("a")}, {"id": "b", "file": g.file_for("b")}]
    (tmp_path / "ve-gen").mkdir()
    (tmp_path / g.file_for("a")).write_bytes(b"x")           # b has an entry but no file: made again
    todo, done = g.split_done(ps, man, tmp_path)
    assert [p["id"] for p in todo] == ["b", "c"] and [p["id"] for p in done] == ["a"]
    todo, done = g.split_done(ps, man, None)                  # no user layer: everything is left to make
    assert len(todo) == 3 and not done


def test_entry_and_merge():
    p = g.parse_prompts([item("a", duration=3)])[0]
    e = g.make_entry(p, "u-1", "2026-11-17", 3.004)
    assert e["file"] == "ve-gen/a.mp3" and e["query"] == p["prompt"] and e["duration_hint"] == 3.0
    assert e["source_url"].endswith("/generated_audio/u-1.mp3") and e["downloaded_at"] == "2026-11-17"
    assert g.make_entry(p, "u-1", "d")["duration_hint"] == 3
    man = [{"id": "x"}, {"id": "a", "old": True}]
    assert g.merge(man, e) == [{"id": "x"}, e]                # replaced in place
    assert g.merge([{"id": "x"}], e) == [{"id": "x"}, e]


def test_licence_is_accepted_by_doc_sfx():
    assert any(x in g.LICENSE for x in doc_sfx.LICENSED)


def test_confirm():
    assert g.confirm(3, True, False)
    assert g.confirm(0, False, False)
    assert not g.confirm(3, False, False)                     # no terminal: never waits for an answer
    assert g.confirm(3, False, True, ask=lambda _: "y")
    assert not g.confirm(3, False, True, ask=lambda _: "")


def test_plan_lines(tmp_path):
    ps = g.parse_prompts([item("a"), item("b")])
    text = "\n".join(g.plan_lines(ps[:1], ps[1:], tmp_path))
    assert "to generate: 1 sound(s); each one uses VideoExpress credits" in text and "skipped): 1: b" in text
    assert "S2F_ASSETS_LOCAL is not set" in "\n".join(g.plan_lines(ps, [], None))


def test_pending_jobs(tmp_path):
    assert g.with_pending({}, "a", "u1") == {"a": "u1"}
    assert g.with_pending({"a": "u1", "b": "u2"}, "a", None) == {"b": "u2"}
    p = g.pending_path(tmp_path)
    assert g.read_pending(p) == {}
    g.write_pending(p, {"a": "u1"})
    assert g.read_pending(p) == {"a": "u1"}
    ps = g.parse_prompts([item("a"), item("b")])
    text = "\n".join(g.plan_lines(ps, [], tmp_path, {"a": "u1"}))
    assert "to generate: 1 sound(s)" in text and "only downloaded now (no credits): a" in text


def test_dry_run_opens_no_browser(tmp_path, monkeypatch, capsys):
    f = tmp_path / "p.json"
    f.write_text(json.dumps([item("a")]), encoding="utf-8")
    monkeypatch.setenv("S2F_ASSETS_LOCAL", str(tmp_path / "layer"))
    monkeypatch.setattr(g, "run", lambda *a: pytest.fail("run() called on a dry run"))
    g.main([str(f), "--dry-run"])
    assert "dry run: nothing generated" in capsys.readouterr().out
