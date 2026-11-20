"""pytest for the vox-host format helpers: doc_build (beat builders) and doc_lint (script checks)."""
import copy
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import doc_build  # noqa: E402
from doc_lint import DEFAULT, lint  # noqa: E402

# Reference copied verbatim from episode 10's make_doc.py of the author's own series (not in this repository)
# :55 TTS_FIX, :56 HOST, :57-60 the four lambdas, :189-193 tts_of
TTS_FIX = {"撒但": "撒旦", "長子": "掌子", "名分": "名份", "背著": "杯著", "差我": "拆我"}
HOST = {"source": "clip", "clip": "host/tp_host.mp4", "clip_sync": True, "vf": "scale=1920:1080,setsar=1"}
ve = lambda i, n, shot, **k: {"id": i, "lines": n if isinstance(n, list) else [n], "source": "ve", "shot": shot, **k}  # noqa: E731
code = lambda i, n, scene, params, **k: {"id": i, "lines": n if isinstance(n, list) else [n], "source": "code", "scene": scene, "params": params, **k}  # noqa: E731
host = lambda i, n, **k: {"id": i, "lines": n if isinstance(n, list) else [n], **HOST, **k}  # noqa: E731
Q = lambda text, by, at, size=72: {"text": text, "by": by, "at": at, "size": size}  # noqa: E731


def tts_of(t):
    for a, b in TTS_FIX.items():
        t = t.replace(a, b)
    return t


def test_doc_build_matches_episode_10_helpers():
    cases = [
        (ve("B3", 3, "hook_waiting"), doc_build.ve("B3", 3, "hook_waiting")),
        (ve("B7", [6, 7], "jacob_journey", **{"from": "雅各"}), doc_build.ve("B7", [6, 7], "jacob_journey", **{"from": "雅各"})),
        (code("B4", 4, "quote_card", Q("四百多年的沉默", "創世記", 0.15, 120)),
         doc_build.code("B4", 4, "quote_card", doc_build.Q("四百多年的沉默", "創世記", 0.15, 120))),
        (code("B6", 5, "timeline", {"hot": 1}, **{"from": "背景是"}), doc_build.code("B6", 5, "timeline", {"hot": 1}, **{"from": "背景是"})),
        (host("B17", [20, 21]), doc_build.host("B17", [20, 21])),
        (host("B26", 30, at=0.2), doc_build.host("B26", 30, at=0.2)),
        (Q("a", "b", 0.1), doc_build.Q("a", "b", 0.1)),
    ]
    for want, got in cases:
        assert json.dumps(got, ensure_ascii=False) == json.dumps(want, ensure_ascii=False)
    L = ["撒但回了一句話", "沒有要改的字", "長子的名分", "背著"]
    want = [{"text": t, **({"tts": tts_of(t)} if tts_of(t) != t else {})} for t in L]
    assert doc_build.tts_lines(L, TTS_FIX) == want


def good_doc():
    """A small doc that passes every default rule."""
    lines = [{"text": t} for t in ["大家好。", "今天講一件事。", "第一點。", "第二點。", "謝謝收看。"]]
    beats = [
        doc_build.code("B1", [1, 2], "cover", {"title": "t"}),
        doc_build.code("B2", 3, "quote_card", doc_build.Q("q", "by", 0.1)),
        doc_build.ve("B3", 4, "s1", **{"from": "第二"}),
        doc_build.code("B4", 4, "stat", {"n": 1}),
        doc_build.host("B5", 5),
    ]
    return {"lang": "zh", "lines": lines, "beats": beats, "shots": {"s1": {}},
            "pip": {"beats": ["B1"]}, "wipes": ["B3"]}


def test_good_doc_passes():
    assert lint(good_doc()) == []


def bad(rule):
    d = good_doc()
    if rule == "no_em_dash":
        d["lines"][2]["text"] = "第一點——就是這樣。"
    elif rule == "zh_heteronyms":
        d["lines"][2]["text"] = "煮熟。"
    elif rule == "quote_card_cap":
        d["beats"] += [doc_build.code(f"Q{i}", 5, "quote_card", {}) if i % 2 else doc_build.ve(f"V{i}", 5, "s1") for i in range(24)]
    elif rule == "quote_card_run":
        d["beats"][3] = doc_build.code("B4", 4, "quote_card", {})
        d["beats"].insert(3, doc_build.code("B3b", 4, "quote_card", {}))
        d["beats"][2] = doc_build.code("B3", 4, "quote_card", {})
    elif rule == "banned_scenes":
        d["beats"][3] = doc_build.code("B4", 4, "seed_dot", {})
    elif rule == "needs_fresh_scene":
        d["beats"][3] = doc_build.code("B4", 4, "compare", {})
    elif rule == "from_in_line":
        d["beats"][2]["from"] = "第三"
    elif rule == "facts":
        d["facts"] = "nope.md"
    elif rule == "lines_covered":
        d["beats"][4]["lines"] = [6]
    elif rule == "ids_exist":
        d["wipes"] = ["B9"]
    elif rule == "shots_match":
        d["shots"]["unused"] = {}
    elif rule == "map_base":
        d["beats"][3] = doc_build.code("B4", 4, "map_route", {"stops": [{"name": "外", "x": 0, "y": 0}],
                                                              "base": {"crop": [100, 100, 900, 506]}})
    return d


WHERE = {"no_em_dash": "line 3", "zh_heteronyms": "line 3", "quote_card_cap": "13", "quote_card_run": "B4",
         "banned_scenes": "B4", "needs_fresh_scene": "cover", "from_in_line": "B3", "lines_covered": "B5",
         "ids_exist": "B9", "shots_match": "unused", "facts": "nope.md", "map_base": "B4"}


def test_every_rule_blocks_its_sample_and_names_where():
    assert set(WHERE) == set(DEFAULT)
    for rule, where in WHERE.items():
        msgs = [m for m in lint(bad(rule)) if m.startswith(rule)]
        assert msgs, rule
        assert any(where in m for m in msgs), (rule, msgs)


def test_rules_take_parameters():
    d = good_doc()
    assert lint(d, {**DEFAULT, "quote_card_cap": 0}) == ["quote_card_cap: 1 cards > 0"]
    d["lines"][0]["text"] = "大家熟悉。"
    assert lint(d, {**DEFAULT, "zh_heteronyms": "著"}) == []


def test_zhe_is_left_to_the_pronunciation_table():
    d = good_doc()
    d["lines"][0]["text"] = "他看著湖面。"
    assert lint(d) == []


def test_heteronyms_only_for_chinese():
    d = bad("zh_heteronyms")
    d["lang"] = "en"
    assert lint(d) == []


def run_cli(doc, *args, tmp):
    p = tmp / "doc.json"
    p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return subprocess.run([sys.executable, str(SCRIPTS / "doc_lint.py"), str(p), *args], capture_output=True, text=True)


def test_cli_exit_codes_and_off(tmp_path):
    assert run_cli(good_doc(), tmp=tmp_path).returncode == 0
    d = bad("zh_heteronyms")
    d["lines"][3]["text"] = "第二點——。"
    r = run_cli(d, tmp=tmp_path)
    assert r.returncode == 1 and "zh_heteronyms" in r.stdout and "no_em_dash" in r.stdout
    r = run_cli(d, "--off", "zh_heteronyms", tmp=tmp_path)
    assert r.returncode == 1 and "zh_heteronyms" not in r.stdout and "no_em_dash" in r.stdout
    assert run_cli(copy.deepcopy(good_doc()), "--off", "nope", tmp=tmp_path).returncode == 2


def test_ids_exist_covers_side_and_pills_and_layout_report():
    from doc_lint import host_layout
    d = good_doc()
    d["side"] = {"beats": ["B4", "B8"]}
    d["pills"] = [{"beat": "B9", "text": "x", "at": "第"}]
    msgs = lint(d)
    assert any("side.beats" in m and "B8" in m for m in msgs) and any("pills[].beat" in m and "B9" in m for m in msgs)
    d["side"]["beats"] = ["B4"]
    assert host_layout(d) == {"full": 1, "side": 1, "pip": 1, "none": 2}
