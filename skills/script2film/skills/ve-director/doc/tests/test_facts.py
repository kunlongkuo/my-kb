"""doc_facts: scripture references, the facts.md table, and the `facts` rule on episode 12's code beats."""
import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import doc_facts  # noqa: E402
from doc_lint import DEFAULT, check  # noqa: E402

EP12 = Path(__file__).resolve().parent / "fixtures/facts_ep12"


def one(text):
    (r,) = doc_facts.refs(text)
    return r[1:]


def test_references():
    assert one("出埃及記 14:13") == one("出 14:13") == one("出埃及記 14：13") == ("出埃及記", (14, 13), (14, 13))
    assert one("出 15:24") != one("出 15:25")
    assert one("約翰福音 6:35")[0] == "約翰福音" and one("約 6:35")[0] == "約翰福音" and one("約一 1:9")[0] == "約翰一書"
    assert one("出 14:13–14") == ("出埃及記", (14, 13), (14, 14))
    assert one("出 14:13-15:2") == ("出埃及記", (14, 13), (15, 2))
    for chapters in ("出埃及記 13–21 章", "出埃及記 19–20", "出埃及記13-21", "創 1–11"):
        assert doc_facts.refs(chapters) == []
    row = {"出處": "出 14:13–14"}
    assert doc_facts.covers(row, doc_facts.refs("出埃及記 14:14")[0]) and not doc_facts.covers(row, doc_facts.refs("出 14:15")[0])


def episode(tmp_path):
    shutil.copytree(EP12, tmp_path / "ep")
    return json.loads((tmp_path / "ep/doc.json").read_text()), tmp_path / "ep"


def edit(base, old, new):
    f = base / "facts.md"
    s = f.read_text()
    assert old in s
    f.write_text(s.replace(old, new, 1))


def test_episode_12_passes(tmp_path):
    doc, base = episode(tmp_path)
    assert doc_facts.check(doc, base) == []


@pytest.mark.parametrize("old,new,where", [
    ("| 我曾將你領出來 | 原始 | 出 20:2 |", "| 我曾將你領出來 | 原始 | 出 20:3 |", "B27"),           # a reference with no row
    ("吃得飽足 | 原始", "吃得飽 | 原始", "B14"),                                                   # quote text changed in the list
    ("| 40 年、吃嗎哪 |", "| 4 年、吃嗎哪 |", "B18"),                                            # the number
    ("| 第 7 年、自由 | 原始 | 出 21:2 |", "| 第 7 年、自由 | 原始 | 出 21:3 |", "B31"),           # a caption's reference
    ("| 我如鷹將你們背在翅膀上 | 原始 |", "| 我如鷹將你們背在翅膀上 | 線索 |", "線索"),             # clue tier on screen
])
def test_each_mismatch_blocks(tmp_path, old, new, where):
    doc, base = episode(tmp_path)
    edit(base, old, new)
    out = doc_facts.check(doc, base)
    assert out and any(where in m for m in out), out


def test_quote_must_be_in_the_excerpt(tmp_path):
    doc, base = episode(tmp_path)
    b10 = next(b for b in doc["beats"] if b["id"] == "B10")
    edit(base, f"| {b10['params']['text']} | 原始 | 出埃及記 14:13 | {b10['params']['text']} |",
         f"| {b10['params']['text']} | 原始 | 出埃及記 14:13 | 不要懼怕 |")
    assert any("B10" in m and "excerpt" in m for m in doc_facts.check(doc, base))


def test_fact_false_skips_and_screen_text_is_walked(tmp_path):
    doc, base = episode(tmp_path)
    b4 = next(b for b in doc["beats"] if b["id"] == "B4")
    del b4["params"]["fact"]
    assert any(m.startswith("facts: B4 quote card") for m in doc_facts.check(doc, base))
    doc2 = copy.deepcopy(doc)
    next(b for b in doc2["beats"] if b["id"] == "B26")["params"]["left"]["text"] = "（出 32:1）"
    assert any("B26" in m and "出 32:1" in m for m in doc_facts.check(doc2, base))


@pytest.mark.parametrize("text,msg", [
    ("| 畫面 | 等級 | 出處 | 備註 |\n|---|---|---|---|\n", "lacks the column 原文摘錄/excerpt"),
    ("| 畫面 | 等級 | 出處 | 原文摘錄 | 備註 |\n|---|---|---|---|---|\n| 甲 | 一手 | 出 1:1 | 甲 | B1 |\n", 'line 3: tier "一手"'),
    ("沒有表格\n", "has no table with a 畫面/on screen column"),
])
def test_bad_table(tmp_path, text, msg):
    (tmp_path / "facts.md").write_text(text)
    assert any(msg in m for m in doc_facts.check({"facts": "facts.md", "beats": []}, tmp_path))


def test_lint_rule_switch_and_paths(tmp_path):
    assert "facts" in DEFAULT
    assert doc_facts.check({"beats": []}, tmp_path) == []                       # no "facts" key: no check
    with pytest.raises(SystemExit, match="no such file"):
        check({"lang": "zh", "facts": "facts.md", "lines": [], "beats": [], "shots": {}}, {"facts": True}, base=tmp_path)
    doc, base = episode(tmp_path)
    r = subprocess.run([sys.executable, str(SCRIPTS / "doc_lint.py"), str(base / "doc.json"), "--off", "facts"],
                       capture_output=True, text=True)
    assert "unknown rule" not in r.stdout


def test_scripture_note(tmp_path, monkeypatch):
    assert "not with a full Bible text" in doc_facts.scripture_note({"facts": "facts.md"})
    assert doc_facts.scripture_note({}) is None
    monkeypatch.setenv("S2F_ASSETS_LOCAL", str(tmp_path))          # a file in the asset layer does not silence the note
    (tmp_path / "bible").mkdir(parents=True)
    (tmp_path / "bible/cuv.json").write_text("{}")
    assert doc_facts.scripture_note({"facts": "facts.md"}) is not None


FACTS_HEAD = "| 畫面 | 等級 | 出處 | 原文摘錄 | 備註 |\n|---|---|---|---|---|\n"


def chart_doc(scene, bid="B5"):
    return {"facts": "facts.md", "beats": [{"id": bid, "source": "code", "scene": scene, "params": {"title": "占比"}}]}


@pytest.mark.parametrize("scene", ["pie", "line_chart", "breakdown"])
def test_chart_needs_a_source_row(tmp_path, scene):
    """D11: a chart beat needs a facts.md row whose 備註 names the beat; B50 does not count for B5."""
    (tmp_path / "facts.md").write_text(FACTS_HEAD + "| 房租 45% | 原始 | 主計總處 2025 | 房租占 45% | B5 圖表 |\n")
    assert doc_facts.check(chart_doc(scene), tmp_path) == []
    (tmp_path / "facts.md").write_text(FACTS_HEAD + "| 房租 45% | 原始 | 主計總處 2025 | 房租占 45% | B50 圖表 |\n")
    out = doc_facts.check(chart_doc(scene), tmp_path)
    assert out == ["facts: B5 chart data has no row in facts.md (備註/note naming B5)"]


def test_formula_and_no_facts_key_are_not_checked(tmp_path):
    (tmp_path / "facts.md").write_text(FACTS_HEAD)
    assert doc_facts.check(chart_doc("formula"), tmp_path) == []
    doc = chart_doc("pie")
    del doc["facts"]
    assert doc_facts.check(doc, tmp_path) == []


def test_chart_row_at_clue_tier_blocks(tmp_path):
    (tmp_path / "facts.md").write_text(FACTS_HEAD + "| 房租 45% | 線索 | 網路文章 | 房租占 45% | B5 |\n")
    out = doc_facts.check(chart_doc("pie"), tmp_path)
    assert out == ['facts: line 3 is only a lead (tier "線索"): a lead does not go on screen']


EN_HEAD = "| On screen | Tier | Source | Excerpt | Note |\n|---|---|---|---|---|\n"


def test_english_column_names(tmp_path):
    """The five columns under their English names (any case) read the same as the Chinese ones."""
    (tmp_path / "facts.md").write_text(EN_HEAD + "| Rent 45% | 原始 | the shop's cost sheet | rent 45% | B5 pie |\n")
    assert doc_facts.check(chart_doc("pie"), tmp_path) == []
    (tmp_path / "facts.md").write_text(EN_HEAD + "| Rent 45% | 原始 | the shop's cost sheet | rent 45% | B50 pie |\n")
    assert doc_facts.check(chart_doc("pie"), tmp_path) == ["facts: B5 chart data has no row in facts.md (備註/note naming B5)"]


@pytest.mark.parametrize("tier", ["primary", "Secondary", "LEAD"])
def test_english_tiers(tmp_path, tier):
    """primary / secondary / lead are 原始 / 權威二手 / 線索; a lead still does not go on screen, named as written."""
    (tmp_path / "facts.md").write_text(FACTS_HEAD + f"| 房租 45% | {tier} | 主計總處 2025 | 房租占 45% | B5 |\n")
    out = doc_facts.check(chart_doc("pie"), tmp_path)
    assert out == ([f'facts: line 3 is only a lead (tier "{tier}"): a lead does not go on screen'] if tier == "LEAD" else [])


def test_chinese_and_english_mixed(tmp_path):
    """Chinese and English column names in one header, and both kinds of tier in one table."""
    head = "| 畫面 | tier | 出處 | excerpt | 備註 |\n|---|---|---|---|---|\n"
    (tmp_path / "facts.md").write_text(head + "| Rent 45% | primary | cost sheet | rent 45% | B5 |\n"
                                       "| Profit split | 權威二手 | ledger | coffee 8k | B6 |\n")
    doc = {"facts": "facts.md", "beats": [chart_doc("pie")["beats"][0], chart_doc("breakdown", "B6")["beats"][0]]}
    assert doc_facts.check(doc, tmp_path) == []
    rows, bad = doc_facts.read(tmp_path / "facts.md")
    assert bad == [] and [r["等級"] for r in rows] == ["原始", "權威二手"]


def test_unknown_english_tier_and_missing_english_column(tmp_path):
    (tmp_path / "facts.md").write_text(EN_HEAD + "| Rent 45% | confirmed | cost sheet | rent 45% | B5 |\n")
    assert doc_facts.check(chart_doc("pie"), tmp_path) == [
        'facts: facts.md line 3: tier "confirmed" is not one of 原始 / 權威二手 / 線索 (primary / secondary / lead)']
    (tmp_path / "facts.md").write_text("| On screen | Tier | Source | Note |\n|---|---|---|---|\n")
    assert doc_facts.check(chart_doc("pie"), tmp_path) == ["facts: facts.md line 1: the table lacks the column 原文摘錄/excerpt"]
