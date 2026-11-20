"""讀音表：每條規則各一例、套兩次結果相同、語言不同不換、表本身的檢查。"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lexicon  # noqa: E402

CASES = [("姪兒來了", "侄兒來了"), ("不要罣慮", "不要掛慮"), ("徬徨的時候", "彷徨的時候"), ("仇敵常藉環境", "仇敵常借環境"),
         ("眾人唱和散那", "眾人唱，和散那"), ("什一奉獻", "十一奉獻"), ("使徒行傳十八章", "使徒行撰十八章"),
         ("一他連得銀子", "一「他連得」銀子"), ("讓應許成為禱告", "讓硬許成為禱告"), ("白髮為老年人的尊榮", "白法為老年人的尊榮"),
         ("帶著孩子", "帶着孩子")]


def test_table_has_these_eleven_rules():
    assert len(lexicon.load()) == len(CASES) == 11 and lexicon.problems(lexicon.load()) == []


@pytest.mark.parametrize("text,want", CASES)
def test_each_rule(text, want):
    assert lexicon.spoken(text, "zh") == want


@pytest.mark.parametrize("text,want", CASES)
def test_twice_is_the_same(text, want):
    assert lexicon.spoken(lexicon.spoken(text, "zh"), "zh") == want


def test_all_rules_together_twice():
    text = "".join(t for t, _ in CASES)
    once = lexicon.spoken(text, "zh")
    assert lexicon.spoken(once, "zh") == once and "「「" not in once


def test_known_side_effect_of_the_single_character_rule():
    """記錄現況，不是認可：「著作」該唸 zhù，也會被換。遇到就在表裡「著」那條上面加整個詞的規則。"""
    assert lexicon.spoken("他的著作", "zh") == "他的着作"


def test_other_language_untouched():
    assert lexicon.spoken("什一 tithe 著", "en") == "什一 tithe 著"


def test_changes_lists_what_was_replaced():
    assert lexicon.changes("什一奉獻帶著", "zh") == [("什一", "十一"), ("著", "着")]
    assert lexicon.changes("沒有要換的", "zh") == []


def test_problems():
    assert lexicon.problems([{"from": "", "to": "x"}]) == ["rule 1: from is empty"]
    assert lexicon.problems([{"from": "a", "to": "b", "lang": "zh"}, {"from": "a", "to": "c", "lang": "zh"}]) == ["rules 1 and 2 both have from a"]


def test_no_rule_feeds_another():
    """一條規則換出來的字不能又被別條規則換：那樣整張表套兩次結果會不同。"""
    rules = lexicon.load()
    for r in rules:
        assert lexicon.spoken(r["to"], r.get("lang", "zh"), rules) == r["to"], r
