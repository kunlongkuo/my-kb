import pytest

from styles import degree_chord, parse_chord


@pytest.mark.parametrize("name,pcs", [("Em", [4, 7, 11]), ("F#m", [6, 9, 1]), ("Bb", [10, 2, 5]), ("C", [0, 4, 7])])
def test_parse_chord(name, pcs):
    assert parse_chord(name) == pcs


@pytest.mark.parametrize("name", ["Cdim", "Csus4", "Cm7b5"])
def test_parse_chord_rejects_unknown_quality(name):  # 支援 maj7／m7／7（lounge），其餘仍拒絕
    with pytest.raises(ValueError):
        parse_chord(name)


@pytest.mark.parametrize("roman,name", [("V", "B"), ("III", "G"), ("i", "Em"), ("iv", "Am"), ("VI", "C"), ("VII", "D")])
def test_degree_chord_e_minor(roman, name):
    assert degree_chord(4, roman) == name


def test_bazaar_differs_from_story():  # 新風格要跟 story 聽得出不同：主題、旋律、分解和弦三個音色都換
    from styles import STYLES
    a, b = STYLES["bazaar"]["programs"], STYLES["story"]["programs"]
    assert all(a[k] != b[k] for k in ("motif", "lead", "arp"))
