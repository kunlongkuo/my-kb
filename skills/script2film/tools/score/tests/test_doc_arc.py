import pytest

from adapters.doc_arc import ArcError, build_parts, phrase_at, role_of

TOK = lambda s, t0: [[c, round(t0 + 0.2 * i, 2)] for i, c in enumerate(s)]
BEATS = [{"id": "B1", "source": "code", "start": 0.0, "duration": 5.0, "tokens": TOK("大家好", 0.3)},
         {"id": "B2", "source": "ve", "start": 5.0, "duration": 6.0, "tokens": TOK("答案是甲沒錯", 0.1)},
         {"id": "B3", "source": "code", "start": 11.0, "duration": 4.0, "tokens": TOK("一百零三次", 0.5)},
         {"id": "B4", "source": "clip", "start": 15.0, "duration": 6.0, "tokens": TOK("真的重要嗎", 0.2)},
         {"id": "B5", "source": "code", "start": 21.0, "duration": 5.0, "tokens": TOK("留言", 0.1)}]
DOC = {"beats": [{"id": "B1", "source": "code", "scene": "cover"}, {"id": "B2", "source": "ve"},
                 {"id": "B3", "source": "code", "scene": "stat_count", "params": {"slam": True, "at": "一百零三"}},
                 {"id": "B4", "source": "clip"}, {"id": "B5", "source": "code", "scene": "credits"}],
       "bgm": {"arc": [{"from": "B1", "style": "story"}, {"from": "B3", "style": "scifi", "gain": 2}, {"from": "B4", "style": "story"}],
               "drops": ["B4"]}}


def test_parts_split_at_the_arc_and_keep_their_own_clock():
    p = build_parts(DOC, BEATS, "t")
    assert [(x["style"], x["duration"]) for x in p] == [("story", 11.0), ("scifi", 4.0), ("story", 11.0)]
    assert [s["role"] for s in p[0]["sections"]] == ["intro", "body"]
    assert p[1]["sections"] == [{"t": 0.0, "role": "title", "label": "B3"}]
    assert [s["role"] for s in p[2]["sections"]] == ["pause", "outro"] and p[2]["sections"][1]["t"] == 6.0
    assert p[1]["hits"] == [{"t": 0.62, "label": "B3 slam"}] and p[1]["_gain"] == 2.0


def test_no_arc_is_one_story_part_and_roles_can_be_overridden():
    doc = {"beats": DOC["beats"], "bgm": {"roles": {"B2": "warm"}}}
    p = build_parts(doc, BEATS, "t")
    assert len(p) == 1 and p[0]["style"] == "story" and p[0]["duration"] == 26.0
    assert role_of({"id": "B2", "source": "ve"}, doc) == "warm"
    with pytest.raises(ArcError):
        role_of({"id": "B2"}, {"bgm": {"roles": {"B2": "chorus"}}})


def test_arc_must_start_on_the_first_beat_and_follow_the_film():
    with pytest.raises(ArcError):
        build_parts({"beats": [], "bgm": {"arc": [{"from": "B2", "style": "story"}]}}, BEATS, "t")
    with pytest.raises(ArcError):
        build_parts({"beats": [], "bgm": {"arc": [{"from": "B1"}, {"from": "B4"}, {"from": "B3"}]}}, BEATS, "t")


def test_phrase_at_ignores_punctuation():
    assert phrase_at(BEATS[1], "是甲，") == 0.5 and phrase_at(BEATS[1], "丙丁") is None
