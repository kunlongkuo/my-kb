"""doc_code.relation_params: the relation scene's nodes, rows, links and focus must hang together before anything renders."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from doc_code import missing_triggers, relation_params  # noqa: E402

BEAT = {"id": "B10"}
GOOD = {"nodes": [{"id": "david", "label": "大衛", "x": 960, "y": 200},
                  {"id": "ado", "label": "亞多尼雅", "x": 430, "y": 470, "hot": True},
                  {"id": "sol", "label": "所羅門", "x": 1490, "y": 470}],
        "links": [{"from": "david", "to": "ado", "kind": "tree"}, {"from": "ado", "to": "sol", "kind": "dash", "label": "沒有請"}],
        "focus": {"ids": ["ado", "sol"], "at": "沒有請"}}
ROWS = {"nodes": [{"id": "a", "label": "甲"}, {"id": "b", "label": "乙"}, {"id": "c", "label": "丙"}],
        "rows": [["a"], ["b", "c"]], "links": [{"from": "a", "to": "b", "kind": "tree"}, {"from": "a", "to": "c", "kind": "tree"}]}


def test_good_params_pass(tmp_path):
    relation_params(tmp_path, BEAT, GOOD)
    relation_params(tmp_path, BEAT, ROWS)
    relation_params(tmp_path, BEAT, {**GOOD, "links": [{"from": "ado", "to": "sol", "kind": "arrow"}], "focus": None})


def test_picture_node_must_exist(tmp_path):
    (tmp_path / "stills").mkdir()
    (tmp_path / "stills/sol.jpg").write_bytes(b"x")
    nodes = GOOD["nodes"][:2] + [{**GOOD["nodes"][2], "src": "stills/sol.jpg"}]
    relation_params(tmp_path, BEAT, {**GOOD, "nodes": nodes})
    with pytest.raises(SystemExit, match="src not found"):
        relation_params(tmp_path, BEAT, {**GOOD, "nodes": GOOD["nodes"][:2] + [{**GOOD["nodes"][2], "src": "stills/none.jpg"}]})


@pytest.mark.parametrize("change,msg", [
    ({"nodes": GOOD["nodes"][:1]}, "at least 2 nodes"),
    ({"nodes": [GOOD["nodes"][0], {**GOOD["nodes"][1], "id": "david"}, GOOD["nodes"][2]]}, "unique"),
    ({"nodes": [GOOD["nodes"][0], {**GOOD["nodes"][1], "label": ""}, GOOD["nodes"][2]]}, "needs a label"),
    ({"nodes": [GOOD["nodes"][0], {**GOOD["nodes"][1], "y": 950}, GOOD["nodes"][2]]}, "y 120-820"),
    ({"nodes": [GOOD["nodes"][0], {"id": "ado", "label": "亞多尼雅"}, GOOD["nodes"][2]]}, "x / y or a place in rows"),
    ({"rows": [["david"], ["zzz"]]}, "rows must name each node id once"),
    ({"rows": [["david"], ["david"]]}, "rows must name each node id once"),
    ({"links": []}, "at least 1 link"),
    ({"links": [{"from": "ado", "to": "zzz"}]}, "join two different nodes"),
    ({"links": [{"from": "ado", "to": "ado"}]}, "join two different nodes"),
    ({"links": [{"from": "ado", "to": "sol", "kind": "zigzag"}]}, "kind must be one of"),
    ({"focus": {"ids": ["ado", "zzz"]}}, "focus.ids"),
    ({"focus": {"ids": []}}, "focus.ids"),
])
def test_bad_params_stop(tmp_path, change, msg):
    with pytest.raises(SystemExit, match=msg):
        relation_params(tmp_path, BEAT, {**GOOD, **change})


def test_trigger_phrases_are_checked():
    """title_at / note_at / focus.at / node and link at are time keys: a phrase not in the narration is reported."""
    text = "唯獨先知拿單比拿雅勇士和他的兄弟所羅門他都沒有請"
    beat = {"id": "B10", "tokens": [[c, k * .3] for k, c in enumerate(text)]}
    ok = {**GOOD, "title_at": "拿單", "note_at": "勇士", "links": [{"from": "ado", "to": "sol", "at": {"w": "兄弟", "d": .4}}]}
    bad = {**GOOD, "title_at": "約押", "note_at": "亞比亞他"}
    assert missing_triggers(ok, beat, "zh") == []
    assert sorted(missing_triggers(bad, beat, "zh")) == ["note_at='亞比亞他'", "title_at='約押'"]


def test_relation_overlaps_measures_clear_space():
    from doc_code import relation_overlaps
    assert relation_overlaps([["a", 0, 0, 100, 50], ["b", 108, 0, 100, 50]]) == []          # 8 px apart: clear
    assert relation_overlaps([["a", 0, 0, 100, 50], ["b", 104, 0, 100, 50]]) == ["a and b overlap by 4 px"]
    assert relation_overlaps([["a", 0, 0, 100, 50], ["b", 50, 200, 100, 50]]) == []         # side by side in x, far in y
    assert relation_overlaps([["a", -5, 0, 100, 50], ["b", 1830, 200, 100, 50]]) == ["a runs off the frame", "b runs off the frame"]


def build(tmp_path, params, lang):
    import doc_code
    return doc_code.build(tmp_path, {"lang": lang}, {"id": "B1", "duration": 5.0, "tokens": []},
                          {"scene": "relation", "params": params}, "lecture-light")


def test_a_row_of_long_labels_is_respread_and_one_too_wide_stops(tmp_path):
    """2026-11-17 (a DeepSeek trial): three long English labels in one row drew on top of each other."""
    import doc_code
    long = {"nodes": [{"id": "y", "label": "Yawning"}] + [{"id": k, "label": t, "sub": "Contagious response"} for k, t in
                      (("a", "Brain Cooling"), ("b", "Social Empathy Signal"), ("c", "Oxygen Myth"))],
            "rows": [["y"], ["a", "b", "c"]], "links": [{"from": "y", "to": k, "kind": "tree"} for k in "abc"]}
    out, _ = build(tmp_path, long, "en")                                     # re-spread by width: fits
    cards = doc_code.page_value(out, "window.__relcards")
    assert doc_code.relation_overlaps(cards) == []
    assert [c[0] for c in sorted(cards, key=lambda c: c[1]) if c[0] != "y"] == ["a", "b", "c"]   # same order, left to right
    wide = {**long, "nodes": long["nodes"][:1] + [{"id": k, "label": t, "sub": "Contagious response"} for k, t in   # each about 690 px
                    (("a", "Social Empathy Signal"), ("b", "Brain Cooling Response"), ("c", "Oxygen Intake Theory"))]}
    with pytest.raises(SystemExit, match="relation cards do not fit: .*runs off the frame"):
        build(tmp_path, wide, "en")
    build(tmp_path, {**wide, "rows": [["y"], ["a", "b"], ["c"]]}, "en")       # split the row: fits
    build(tmp_path, GOOD, "zh")
    build(tmp_path, ROWS, "zh")


def test_board_look(tmp_path):
    """look "board": accepted; anything else stops. On the page the notes are paper with a pin each, and the same size and
    place as without the look (layout and the overlap check unchanged)."""
    relation_params(tmp_path, BEAT, {**GOOD, "look": "board"})
    with pytest.raises(SystemExit, match="look must be"):
        relation_params(tmp_path, BEAT, {**GOOD, "look": "cork"})
    import doc_code
    beat = {"id": "B10", "duration": 6.0, "tokens": [["沒", 1.0], ["有", 1.2], ["請", 1.4]]}
    read = """(() => { tl.seek(D); return [...document.querySelectorAll('#content .blk.card')].map(b =>
      [b.offsetLeft, b.offsetTop, b.offsetWidth, b.offsetHeight, !!b.querySelector('.board-pin'), getComputedStyle(b).backgroundColor]); })()"""
    got = {}
    for look in (None, "board"):
        params = {**GOOD, "look": look} if look else GOOD
        out, _ = doc_code.build(tmp_path / str(look), {"lang": "zh"}, beat, {"scene": "relation", "params": params}, "collage")
        got[look] = doc_code.page_value(out, read)
    assert [c[:4] for c in got[None]] == [c[:4] for c in got["board"]]
    assert all(c[4] for c in got["board"]) and not any(c[4] for c in got[None])
    assert {c[5] for c in got["board"]} == {"rgb(246, 239, 220)"}
