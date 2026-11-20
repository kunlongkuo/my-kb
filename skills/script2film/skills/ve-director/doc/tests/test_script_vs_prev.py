"""doc_lint.script_vs_prev: hook type, main-line beat and line openings repeated from the last
episode; series fixed lines, short lines and English scripts are left out."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from doc_lint import check, earlier_episodes, fixed_lines, script_vs_prev  # noqa: E402


def doc(lines, hook="反問", main="quote_card", lang="zh"):
    beats = [{"id": "B1", "source": "code", "scene": "cover"}, {"id": "B3", "source": "ve", "shot": "s"},
             {"id": "B4", "source": "code", "scene": main}]
    return {"lang": lang, "hook": hook, "lines": [{"text": t} for t in lines], "beats": beats}


FIXED = ["大家好歡迎一起用示範系列"]
PREV = doc(["大家好，歡迎一起用示範系列的方式，來讀聖經。", "你有沒有等過一件事？", "好。", "雅各回家了。"])


def test_repeats_are_listed():
    out = script_vs_prev(doc(["大家好，歡迎一起用示範系列的方式。", "你有沒有做過一件事？", "好。", "約瑟去了埃及。"]), PREV, FIXED)
    assert "same hook type as the previous episode: 反問" in out and "same main-line shot as the previous episode: quote_card" in out
    (line,) = [x for x in out if x.startswith("line openings")]
    assert "你有沒有做過" in line and "大家好" not in line and "「好" not in line     # fixed line and 1-character line left out


def test_different_episode_is_quiet():
    assert script_vs_prev(doc(["二十塊銀子。"], hook="數字", main="stat_count"), PREV, FIXED) == []


def test_hook_labels():
    assert "this episode names no hook type (doc.json \"hook\")" in script_vs_prev(doc([], hook=None), PREV, FIXED)
    assert any("is not one of 反問" in x for x in script_vs_prev(doc([], hook="提問"), PREV, FIXED))
    out = script_vs_prev(doc([], hook="反問"), doc([], hook=None), FIXED)
    assert "the previous episode names no hook type: not compared" in out and not any("episode: 反問" in x for x in out)


def test_main_beat_override_and_missing():
    d = {**doc([], main="quote_card"), "main_beat": "B3"}
    assert not any(x.startswith("same main-line shot") for x in script_vs_prev(d, PREV, FIXED))   # B3 is ve, the last one's is quote_card
    assert "main_beat B9 is not a beat" in script_vs_prev({**d, "main_beat": "B9"}, PREV, FIXED)


def test_english_and_no_fixed_list():
    out = script_vs_prev(doc(["Have you ever waited?"], lang="en"), doc(["Have you ever lost?"], lang="en"), None)
    assert out[0].startswith("no fixed-line list") and "English script: line openings are not compared" in out and not any(x.startswith("line openings") for x in out)


def test_fixed_lines_from_series_json(tmp_path):
    ep = tmp_path / "002_x"
    ep.mkdir()
    assert fixed_lines(ep) is None
    (tmp_path / "series.json").write_text(json.dumps({"name": "x"}))
    assert fixed_lines(ep) is None
    (tmp_path / "series.json").write_text(json.dumps({"fixed_lines": ["下一集，我們一起讀"]}, ensure_ascii=False))
    assert fixed_lines(ep) == ["下一集我們一起讀"]


def test_check_prints_the_report(tmp_path, capsys):
    rules = {"lines_covered": True}
    prev = tmp_path / "001_a" / "doc.json"
    prev.parent.mkdir()
    prev.write_text(json.dumps({**PREV, "lines": PREV["lines"], "shots": {}}, ensure_ascii=False))
    d = {**doc(["你有沒有做過一件事？"]), "shots": {}}
    d["beats"] = [{**b, "lines": [1]} for b in d["beats"]]
    check(d, rules, prev=prev, base=tmp_path / "002_b")
    out = capsys.readouterr().out
    assert "script vs the last 1 episode(s)" in out and "same hook type as 001_a: 反問" in out
    check(d, rules, prev=None, base=tmp_path / "002_b")
    assert "script vs the last" not in capsys.readouterr().out


def test_report_looks_back_three_episodes_and_names_each(tmp_path, capsys):
    """Episodes 001–004 before 005: the report compares 004, 003 and 002 (COMPARE_LAST), not 001; a repeat from an
    older one names that episode."""
    def write(name, d):
        p = tmp_path / name / "doc.json"
        p.parent.mkdir()
        p.write_text(json.dumps({**d, "shots": {}}, ensure_ascii=False))
        return p
    write("001_a", doc([], hook="反問"))
    write("002_b", doc(["雅各回家了。"], hook="數字"))
    write("003_c", doc([], hook="衝突", main="stat_count"))
    last = write("004_d", doc([], hook="反常識", main="stat_count"))
    d = {**doc(["雅各回家了。"], hook="反問"), "shots": {}}
    d["beats"] = [{**b, "lines": [1]} for b in d["beats"]]
    check(d, {"lines_covered": True}, prev=last, base=tmp_path / "005_e")
    out = capsys.readouterr().out
    assert [x.split(")")[0] for x in out.splitlines() if x.startswith("vs_prev (")] == ["vs_prev (004_d", "vs_prev (003_c", "vs_prev (002_b"]
    assert "same hook type" not in out                       # 反問 was 001's, four back: not compared
    assert "line openings as in 002_b" in out


def test_a_missing_number_ends_the_chain(tmp_path):
    for name in ("001_a", "003_c"):
        (tmp_path / name).mkdir()
        (tmp_path / name / "doc.json").write_text("{}")
    assert earlier_episodes(tmp_path / "003_c" / "doc.json") == [tmp_path / "003_c" / "doc.json"]
