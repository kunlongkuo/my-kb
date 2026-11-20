"""pytest for the lecture themes (lecture-style): tokens from themes/lecture.json, the light flag."""
import json
import re
import sys
from pathlib import Path

import pytest

DOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DOC / "scripts"))
from doc_themes import CODE_THEMES, code_theme  # noqa: E402

TOKENS = json.loads((DOC / "themes/lecture.json").read_text(encoding="utf-8"))
sys.path.insert(0, str(DOC / "tests"))
from lecture_palette_check import KEYS, PALETTES, contrast, find_source  # noqa: E402


def var(th, name):
    return re.search(rf"--{name}:\s*([^;]+);", th["vars"])[1].strip()


def test_lecture_themes_read_tokens():
    for mode in PALETTES:
        th, t = CODE_THEMES[f"lecture-{mode}"], TOKENS[mode]
        assert var(th, "bg") == t["bg"] and var(th, "red") == t["accent"] and var(th, "must") == t["accent2"]
        assert var(th, "fg") == t["fg"] and var(th, "strip") == t["panel"] and var(th, "hi") == t["hi"]
        assert th["dim"] == t["dim"] and th["torn"] is False


def test_every_theme_has_the_same_keys_and_a_light_flag():
    keys = set(CODE_THEMES["collage"])
    assert all(set(th) == keys for th in CODE_THEMES.values())
    assert {k: th["light"] for k, th in CODE_THEMES.items()} == \
        {"collage": True, "live": False, "lecture-light": True, "lecture-dark": False,
         "lecture-story": False, "lecture-finance": True, "lecture-food": True,
         "lecture-tech": False, "lecture-history": True, "lecture-faith": True,
         "dark-gold": False, "newsroom": False, "vintage-poster": True, "editorial-serif": True, "cinematic-dark": False}


def test_code_theme_copies_lecture():
    assert code_theme("lecture-dark") == CODE_THEMES["lecture-dark"]


def test_ve_look_defaults_and_flat_keys():
    from doc_themes import VE_THEMES, ve_look
    assert ve_look({}, "collage") == "collage" and ve_look({}, "live") == "live"
    assert ve_look({}, "lecture-light") == ve_look({}, "lecture-dark") == "flat"
    assert ve_look({"ve_look": "live"}, "lecture-dark") == "live"
    assert all(set(th) == set(VE_THEMES["collage"]) for th in VE_THEMES.values())


def stops(fn, *a):
    import pytest
    with pytest.raises(SystemExit) as e:
        fn(*a)
    return str(e.value)


def test_doc_cut_stops_on_contradicting_host_layers_before_rendering():
    from doc_cut import check_layers, pill_times
    beats = [{"id": "B1", "source": "code"}, {"id": "B2", "source": "clip"}]
    assert "B1" in stops(check_layers, {"beats": beats, "side": {"beats": ["B1"]}, "pip": {"beats": ["B1"]}})
    assert "B2" in stops(check_layers, {"beats": beats, "side": {"beats": ["B2"]}})
    check_layers({"beats": beats, "side": {"beats": ["B1"]}, "pip": {"beats": []}})
    timed = [{"id": "B1", "tokens": [["今", .25], ["天", .41], ["這", .57], ["兩", .7]]}]
    doc = {"lang": "zh", "pills": [{"beat": "B1", "text": "x", "at": "這兩"}]}
    assert pill_times(doc, timed) == {0: (.57, "B1")}
    doc["pills"][0]["at"] = "明天"
    assert "B1" in stops(pill_times, doc, timed)
    doc["pills"][0].update(at="這兩", pos="left")
    assert "B1" in stops(pill_times, doc, timed)
    doc["pills"][0]["pos"] = "corner"   # 2026-11-10: the small upper-left grade label
    assert pill_times(doc, timed) == {0: (.57, "B1")}


def test_rise_swaps_up_and_down():
    red, green = TOKENS["_rise"]["red"], TOKENS["_rise"]["green"]
    assert f"--up:{red}; --down:{green};" in CODE_THEMES["lecture-finance"]["vars"]   # default: red up (Taiwan)
    th = code_theme("lecture-finance", rise="green")
    assert f"--up:{green}; --down:{red};" in th["vars"] and f"--up:{red}" not in th["vars"]
    assert f"--up:{red}; --down:{green};" in CODE_THEMES["lecture-finance"]["vars"]   # the table itself is unchanged


def test_rise_rejects_bad_values():
    with pytest.raises(ValueError):
        code_theme("lecture-finance", rise="up")
    with pytest.raises(ValueError):
        code_theme("collage", rise="green")


def test_palette_list_is_the_eight_we_ship():
    assert PALETTES == ["light", "dark", "story", "finance", "food", "tech", "history", "faith"]


@pytest.mark.parametrize("mode", PALETTES)
def test_palette_has_all_keys_and_says_where_it_came_from(mode):
    t = TOKENS[mode]
    assert [k for k in KEYS if k not in t] == []
    assert t.get("_why") or mode in TOKENS["_source"]      # light, dark: per-pixel record in _source instead
    if mode not in ("light", "dark"):
        assert isinstance(t.get("light"), bool) and t["_why"]


@pytest.mark.parametrize("mode", PALETTES)
def test_palette_text_contrast_is_aa(mode):
    t = TOKENS[mode]
    for a, b in (("fg", "bg"), ("fg", "panel"), ("muted", "bg")):
        assert contrast(t[a], t[b]) >= 4.5, f"{mode} {a}/{b} {contrast(t[a], t[b]):.2f}"


def test_contrast_formula_on_known_pairs():
    assert round(contrast("#000000", "#ffffff"), 2) == 21.0
    assert round(contrast("#777777", "#ffffff"), 2) == 4.48      # the classic just-below-AA grey


@pytest.mark.parametrize("mode", ["tech", "history", "faith"])
def test_new_palette_source_exists(mode, monkeypatch):
    src = TOKENS[mode]["_from"]
    assert re.fullmatch(r"[^:/]+:[^:]+", src)
    state, where = find_source(src)
    if state == "no-repo":
        pytest.skip(f"{mode}: its colour source is not shipped; set PALETTE_SRC_ROOTS to a folder that holds it")
    assert state == "ok", f"{mode}: {where} does not exist"


def test_source_lookup_tells_missing_repo_from_missing_file(tmp_path, monkeypatch):
    (tmp_path / "Repo").mkdir()
    (tmp_path / "Repo/a.jpg").write_bytes(b"x")
    monkeypatch.setenv("PALETTE_SRC_ROOTS", str(tmp_path))
    assert find_source("Repo:a.jpg")[0] == "ok"
    assert find_source("Repo:b.jpg")[0] == "no-file"
    assert find_source("Other:a.jpg")[0] == "no-repo"


def test_source_lookup_has_no_default_roots(monkeypatch):
    monkeypatch.delenv("PALETTE_SRC_ROOTS", raising=False)
    assert find_source("Repo:a.jpg") == ("no-repo", "PALETTE_SRC_ROOTS not set")
