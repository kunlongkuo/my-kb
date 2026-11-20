import pytest

from ve_frames import SheetError, load_sheet, video_prompt

OK = {"shots": [{"id": "K1", "dur": 8, "first": 123, "last": "kick lands", "video": "they fight"},
                {"id": "K2", "dur": 8, "first": "chain", "last": "she lands", "video": "more fighting"}]}


def test_defaults():
    s = load_sheet(OK)
    assert (s["aspect"], s["takes"], s["suffix"]) == ("16:9", 1, "")


@pytest.mark.parametrize("patch,where", [
    ({"aspect": "4:3"}, "aspect"),
    ({"takes": 6}, "takes"),
    ({"shots": []}, "shots"),
])
def test_top_level_errors(patch, where):
    with pytest.raises(SheetError, match=where):
        load_sheet({**OK, **patch})


@pytest.mark.parametrize("shot,where", [
    ({"first": "chain"}, "first"),          # 第一段不能 chain
    ({"first": "46248150"}, "first"),       # 字串 id
    ({"dur": 2}, "dur"),
    ({"dur": 8.5}, "dur"),
    ({"last": " "}, "last"),
    ({"video": ""}, "video"),
])
def test_first_shot_errors(shot, where):
    with pytest.raises(SheetError, match=where):
        load_sheet({"shots": [{**OK["shots"][0], **shot}]})


def test_duplicate_id():
    with pytest.raises(SheetError, match="id"):
        load_sheet({"shots": [OK["shots"][0], {**OK["shots"][1], "id": "K1"}]})


def test_suffix_appended():
    s = load_sheet({**OK, "suffix": " Fast. "})
    assert video_prompt(s, s["shots"][0]) == "they fight Fast."
