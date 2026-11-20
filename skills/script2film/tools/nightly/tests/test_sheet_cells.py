"""截圖表的格子（tools/nightly/check.py sheet_cells）。不抽圖、不用字型。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check  # noqa: E402


def beat(i, source, start, duration, **more):
    return {"id": i, "source": source, "start": start, "duration": duration, "text": "x", **more}


def test_code_beats_get_a_tail_frame_and_others_do_not():
    beats = [beat("B1", "code", 0.0, 5.0), beat("B2", "ve", 5.0, 4.0), beat("B3", "code", 9.0, 0.4)]
    cells = [(b["id"], round(t, 2), kind) for b, t, kind in check.sheet_cells(beats)]
    assert cells == [("B1", 0.15, "head"), ("B1", 4.6, "tail"), ("B2", 5.15, "head"), ("B3", 9.15, "head")]   # B3：尾不比首晚，不加


def test_head_frame_follows_the_first_word():
    cells = check.sheet_cells([beat("B1", "code", 2.0, 6.0, first_word=3.5), beat("B2", "clip", 8.0, 3.0, first_word=7.0)])
    assert [(round(t, 2), kind) for _, t, kind in cells] == [(3.65, "head"), (7.6, "tail"), (8.15, "head")]


def test_a_film_without_code_beats_keeps_one_cell_per_beat():
    beats = [beat(f"B{k}", s, k * 4.0, 4.0) for k, s in enumerate(["ve", "clip", "photo", "ve", "ve"])]
    assert len(check.sheet_cells(beats)) == len(beats)


def test_canvas_has_room_for_every_cell():
    assert check.sheet_size(4) == (check.COLS * check.W, check.H + 60)
    assert check.sheet_size(8) == (check.COLS * check.W, 2 * (check.H + 60))      # 範例：四拍各兩格
    assert check.sheet_size(9) == (check.COLS * check.W, 3 * (check.H + 60))
