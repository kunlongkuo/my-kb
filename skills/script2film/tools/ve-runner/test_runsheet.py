"""pytest for the run-sheet parser (pure logic, no browser)."""
import pytest
from PIL import Image

from ve_runner import _check_lipsync, new_run_dir, parse_runsheet

HEAD = "# Actor portraits\nActor 1: woman puppet\nActor 2: man puppet\n\n# Shots\n"


def sheet(tmp_path, body):
    p = tmp_path / "rs.md"
    p.write_text(HEAD + body, encoding="utf-8")
    return parse_runsheet(p)


def shot(n, t2i, extra=""):
    return (f"## Shot {n}\n- **Duration:** 5s\n- **Text-To-Image Prompt:** {t2i}\n"
            f"- **Image-To-Video Prompt:** moves.\n{extra}\n")


def test_cast_defaults_to_actors_named_in_image_prompt_in_order(tmp_path):
    rs = sheet(tmp_path, shot(1, "Actor 2 faces Actor 1 across the table."))
    assert rs.shots[0].cast == ["Actor 2", "Actor 1"]
    assert rs.shots[0].start == "master"


def test_no_actor_named_means_no_cast(tmp_path):
    assert sheet(tmp_path, shot(1, "a bowl on a table")).shots[0].cast == []


def test_explicit_cast_overrides_and_none_clears(tmp_path):
    rs = sheet(tmp_path, shot(1, "Actor 1 alone", "- **Cast:** Actor 2") + shot(2, "Actor 1", "- **Cast:** none"))
    assert [s.cast for s in rs.shots] == [["Actor 2"], []]


def test_more_than_two_cast_is_rejected(tmp_path):
    with pytest.raises(SystemExit):
        sheet(tmp_path, shot(1, "x", "- **Cast:** Actor 1, Actor 2, Actor 3"))


def test_start_chain_parsed_and_bad_value_rejected(tmp_path):
    assert sheet(tmp_path, shot(1, "Actor 1", "- **Start:** chain")).shots[0].start == "chain"
    with pytest.raises(SystemExit):
        sheet(tmp_path, shot(2, "Actor 1", "- **Start:** last"))


def test_start_same_parsed(tmp_path):
    assert sheet(tmp_path, shot(2, "Actor 1", "- **Start:** same")).shots[0].start == "same"


def test_save_master_parsed_and_needs_generated_image(tmp_path):
    assert sheet(tmp_path, shot(1, "Actor 1", "- **Save:** master")).shots[0].save == "master"
    assert sheet(tmp_path, shot(1, "Actor 1")).shots[0].save == ""
    with pytest.raises(SystemExit):
        sheet(tmp_path, shot(1, "Actor 1", "- **Save:** video"))
    with pytest.raises(SystemExit):
        sheet(tmp_path, shot(2, "Actor 1", "- **Start:** same\n- **Save:** master"))


def test_duration_clamped_to_ve_slider(tmp_path):
    body = shot(1, "x").replace("5s", "12s")
    assert sheet(tmp_path, body).shots[0].duration == 10


def vshot(n, i2v):
    return f"## Shot {n}\n- **Duration:** 5s\n- **Text-To-Image Prompt:** Actor 1 and Actor 2\n- **Image-To-Video Prompt:** {i2v}\n\n"


def test_spoken_lines_carry_their_speaker(tmp_path):
    one = 'Actor 1 nods, and says in a calm accent: "喝茶。"'
    two = ('Actor 2, the man in the hat, says in a low voice: "喝茶。" Then Actor 1, the woman, '
           'says in a firm accent: "初五。"')
    rs = sheet(tmp_path, vshot(1, one) + vshot(2, two) + vshot(3, "Actor 1 nods."))
    assert [s.speech for s in rs.shots] == [[(1, "喝茶。")], [(2, "喝茶。"), (1, "初五。")], []]
    assert rs.shots[0].dialogue == "喝茶。" and rs.shots[2].dialogue is None


@pytest.mark.parametrize("i2v", [
    'Actor 1 says in a voice: "a" and Actor 1 says in a voice: "b"',                              # same actor twice
    'Actor 1 says in a voice: "a" Actor 2 says in a voice: "b" Actor 1 says in a voice: "c"',      # three lines
])
def test_two_lines_must_be_one_per_actor(tmp_path, i2v):
    # 2026-11-08: the limit is Lipsync HD's, so parsing accepts these and the Lipsync path refuses them (_run calls
    # _check_lipsync unless --speech-in-prompt, where one actor may speak in several timed beats)
    s = sheet(tmp_path, vshot(1, i2v)).shots[0]
    with pytest.raises(SystemExit):
        _check_lipsync(s.n, s.speech)


def test_one_actor_several_beats_parses(tmp_path):
    i2v = ('[ACTION 0-2s] Actor 1 says in a voice: "a" [ACTION 2-4s] Actor 1 says in a voice: "b" '
           '[ACTION 4-6s] Actor 1 holds still.')
    assert sheet(tmp_path, vshot(1, i2v)).shots[0].speech == [(1, "a"), (1, "b")]


def test_sheet_without_actors_parses_when_no_shot_casts(tmp_path):
    p = tmp_path / "rs.md"
    p.write_text("# Shots\n" + shot(1, "ink-wash mountains, no figures"), encoding="utf-8")
    rs = parse_runsheet(p)
    assert rs.actors == [] and rs.shots[0].cast == []


def test_sheet_without_actors_but_casting_exits(tmp_path):
    p = tmp_path / "rs.md"
    p.write_text("# Shots\n" + shot(1, "Actor 1 sits on a bench"), encoding="utf-8")
    with pytest.raises(SystemExit):
        parse_runsheet(p)


def test_new_run_dir_is_a_fresh_timestamp_folder_under_base(tmp_path):
    d = new_run_dir(tmp_path / "film" / "ve-runs")
    assert d.is_dir() and d.parent == tmp_path / "film" / "ve-runs" and len(d.name) == 15
    assert new_run_dir(tmp_path, "voice_").name.startswith("voice_")


def test_narration_resolves_relative_to_the_sheet(tmp_path):
    (tmp_path / "b1.wav").write_bytes(b"x")
    rs = sheet(tmp_path, shot(1, "a bowl", "- **Narration:** b1.wav") + shot(2, "a cup"))
    assert rs.shots[0].narration == str((tmp_path / "b1.wav").resolve())
    assert rs.shots[1].narration == ""


def test_narration_missing_file_is_rejected(tmp_path):
    with pytest.raises(SystemExit):
        sheet(tmp_path, shot(1, "a bowl", "- **Narration:** nope.wav"))


def test_narration_with_a_spoken_line_is_rejected(tmp_path):
    (tmp_path / "b1.wav").write_bytes(b"x")
    body = ("## Shot 1\n- **Duration:** 5s\n- **Text-To-Image Prompt:** Actor 1 sits.\n"
            '- **Image-To-Video Prompt:** Actor 1 says in a calm tone: "hi"\n- **Narration:** b1.wav\n')
    with pytest.raises(SystemExit):
        sheet(tmp_path, body)


def test_narration_on_a_save_master_shot_is_rejected(tmp_path):
    (tmp_path / "b1.wav").write_bytes(b"x")
    with pytest.raises(SystemExit):
        sheet(tmp_path, shot(1, "a bowl", "- **Narration:** b1.wav\n- **Save:** master"))


def test_start_image_resolves_file_relative_to_sheet_and_missing_file_rejected(tmp_path):
    Image.new("RGB", (1920, 1080)).save(tmp_path / "frame.jpg")
    rs = sheet(tmp_path, shot(1, "a hand", "- **Start:** image frame.jpg"))
    assert rs.shots[0].start == "image"
    assert rs.shots[0].start_image == str((tmp_path / "frame.jpg").resolve())
    with pytest.raises(SystemExit):
        sheet(tmp_path, shot(1, "a hand", "- **Start:** image nope.jpg"))


def test_start_image_must_be_16x9_or_9x16(tmp_path):
    """VE refuses other shapes only after the upload (2026-11-05, a portrait painting): the sheet stops first."""
    Image.new("RGB", (1080, 1920)).save(tmp_path / "tall.jpg")
    assert sheet(tmp_path, shot(1, "a hand", "- **Start:** image tall.jpg")).shots[0].start == "image"
    Image.new("RGB", (1280, 1620)).save(tmp_path / "painting.jpg")
    with pytest.raises(SystemExit, match="16:9 or 9:16"):
        sheet(tmp_path, shot(1, "a hand", "- **Start:** image painting.jpg"))
