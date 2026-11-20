"""themes/styles.json: each styled theme has the palette keys and passes the same contrast rule as lecture.json, names a
shape, a ground and a VE look that exist, and changes all three layers (its css, its ground, its colours differ from the
others)."""
import json
import sys
from pathlib import Path

import pytest

DOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DOC / "scripts"))
sys.path.insert(0, str(DOC / "tests"))
from doc_themes import CODE_THEMES, GROUNDS, SHAPES, STYLES, VE_THEMES, code_theme, ve_look  # noqa: E402
from lecture_palette_check import AA, KEYS, TEXT_PAIRS, contrast  # noqa: E402

NAMES = [k for k in STYLES if not k.startswith("_")]


@pytest.mark.parametrize("name", NAMES)
def test_palette_keys_reason_and_contrast(name):
    t = STYLES[name]
    assert all(t.get(k) for k in KEYS) and isinstance(t.get("light"), bool)
    assert t.get("_why") and t.get("_from", "").count(":") == 1
    for a, b in TEXT_PAIRS:
        assert contrast(t[a], t[b]) >= AA, (name, a, b, round(contrast(t[a], t[b]), 2))


@pytest.mark.parametrize("name", NAMES)
def test_shape_ground_and_ve_look_exist(name):
    t = STYLES[name]
    assert t["shape"] in SHAPES and t["ground"] in GROUNDS and t["ve"] in VE_THEMES
    assert ve_look({}, name) == t["ve"] and ve_look({"ve_look": "collage"}, name) == "collage"


def test_three_layers_differ_between_themes():
    """no two styled themes share a shape, a ground or a background colour."""
    for key in ("shape", "ground", "bg"):
        vals = [STYLES[n][key] for n in NAMES]
        assert len(set(vals)) == len(vals), key


def test_rise_and_palette():
    """rise works on a styled theme (charts' up / down colours); an era palette stays collage-only."""
    assert "--up:" in code_theme("newsroom", rise="green")["vars"]
    with pytest.raises(ValueError, match="collage"):
        code_theme("newsroom", palette="被擄")
    assert all(n in CODE_THEMES for n in NAMES)
