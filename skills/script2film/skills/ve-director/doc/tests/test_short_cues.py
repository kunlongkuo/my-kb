"""short_cues：字幕停不到讀得完的時間（0.5 秒以下、0.5–0.8 秒）；parse_srt 是 doc_cut.srt 的反向。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_cut  # noqa: E402
from doc_common import MIN_SUB_FAIL_S, MIN_SUB_WARN_S, parse_srt, short_cues  # noqa: E402


def cue(start, dur, text="字"):
    return {"start": start, "end": round(start + dur, 3), "text": text}


def test_boundaries():
    fail, warn = short_cues([cue(1, 0.499, "a"), cue(2, 0.5, "b"), cue(3, 0.799, "c"), cue(4, 0.8, "d"), cue(5, 3.0, "e")])
    assert [c["text"] for c in fail] == ["a"] and [c["text"] for c in warn] == ["b", "c"]
    assert fail[0] == {"start": 1, "dur": 0.499, "text": "a"}
    assert (MIN_SUB_FAIL_S, MIN_SUB_WARN_S) == (0.5, 0.8)


def test_parse_srt_reads_back_what_srt_writes():
    cues = [cue(0.0, 1.25, "第一行"), cue(61.5, 0.4, "兩行\n字幕"), cue(3600.0, 2.0, "一小時後")]
    assert parse_srt(doc_cut.srt(cues)) == cues
    assert parse_srt("") == [] and parse_srt("1\nnot a time line\ntext\n") == []
