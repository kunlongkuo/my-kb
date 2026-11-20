"""tp_multi 的純邏輯：工作字串解析、跨集隊伍順序（瀏覽器操作沿用 tp_host，不在這裡測）。"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tp_multi import build_queue, parse_job  # noqa: E402


def test_parse_job_with_look_keeps_spaces_and_capitalizes_prefix(tmp_path):
    P, prefix, look = parse_job(f"{tmp_path}:e01:Host shirt")
    assert P == tmp_path.resolve() and prefix == "E01" and look == "Host shirt"


def test_parse_job_without_look_means_original_character(tmp_path):
    assert parse_job(f"{tmp_path}:R01")[2] is None
    assert parse_job(f"{tmp_path}:R01:")[2] is None


@pytest.mark.parametrize("spec", ["只有資料夾", "/tmp/x:", ""])
def test_parse_job_rejects_missing_prefix(spec):
    with pytest.raises(ValueError):
        parse_job(spec)


def test_queue_runs_episodes_in_given_order_then_part_number(tmp_path):
    jobs = []
    for name, ks, prefix, look in [("002", [1, 2], "B", "Host bible"), ("001", [1, 2, 3], "A", None)]:
        P = tmp_path / name
        (P / "host").mkdir(parents=True)
        (P / "host/parts.json").write_text(json.dumps([{"k": k} for k in ks]))
        jobs.append((P, prefix, look))
    q = build_queue(jobs)
    assert [it[2] for it in q] == ["B part1", "B part2", "A part1", "A part2", "A part3"]
    assert q[0][5] == "Host bible" and q[2][5] is None
    assert q[2][3] == tmp_path / "001/host/parts/part1.mp3" and q[2][4].name == "part1.mp4"
