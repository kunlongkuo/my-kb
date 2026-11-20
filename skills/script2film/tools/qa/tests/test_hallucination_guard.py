"""幻覺守衛：靜音段解析與分類的純邏輯，加上合成檔跑一次獨立工具。"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hallucination_guard import classify, main, parse_silencedetect, parse_srt, render_srt, tail_words  # noqa: E402

LOG = """[silencedetect @ 0x1] silence_start: 3.2
[silencedetect @ 0x1] silence_end: 5.0 | silence_duration: 1.8
[silencedetect @ 0x1] silence_start: 9.5
"""


def seg(idx, start, end, text="x"):
    return {"idx": idx, "start": start, "end": end, "text": text, "time": "t"}


def test_parse_open_tail_runs_to_duration():
    assert parse_silencedetect(LOG, 12.0) == [(3.2, 5.0), (9.5, 12.0)]


def test_negative_start_clamped():
    assert parse_silencedetect("silence_start: -0.01\nsilence_end: 0.8 |", 5.0) == [(0.0, 0.8)]


def test_classify_tail_and_suspect():
    sil = parse_silencedetect(LOG, 12.0)
    segs = [seg(1, 0.0, 3.1, "真話"), seg(2, 3.5, 4.6, "靜音裡"), seg(3, 5.0, 9.4, "真話"), seg(4, 10.0, 11.5, "謝謝觀看")]
    suspect, trailing = classify(segs, sil, 12.0)
    assert [s["idx"] for s in suspect] == [2]
    assert [s["idx"] for s in trailing] == [4]


def test_speech_overlapping_silence_edge_not_flagged():
    suspect, trailing = classify([seg(1, 2.8, 4.0)], [(3.2, 5.0)], 10.0)
    assert suspect == [] and trailing == []


def test_no_tail_silence_means_no_trailing():
    suspect, trailing = classify([seg(1, 9.0, 9.9)], [(3.2, 5.0)], 10.0)
    assert trailing == []


def test_srt_roundtrip_renumbers():
    text = "1\n00:00:00,000 --> 00:00:01,000\n甲\n\n2\n00:00:01,000 --> 00:00:02,000\n乙\n"
    segs = parse_srt(text)
    out = render_srt(segs[1:])
    assert out.startswith("1\n00:00:01,000 --> 00:00:02,000\n乙")


def word(start, end, text="x"):
    return {"start": start, "end": end, "text": text}


def test_tail_words_only_after_the_silence_that_runs_to_the_end():
    got = tail_words([word(9.5, 9.9, "真"), word(10.2, 10.6, "謝謝")], [(10.0, 13.0)], 13.0)
    assert [w["text"] for w in got] == ["謝謝"]
    assert tail_words([word(10.2, 10.6)], [(10.0, 12.0)], 13.0) == []      # the silence stops before the end
    assert tail_words([word(3.5, 4.0)], [(3.2, 5.0), (10.0, 13.0)], 13.0) == []   # inside a mid-film silence: not this rule


def tone_then_silence(tmp_path):
    """5 s of tone, then 3 s of silence; two subtitles, the second one on the silence."""
    audio = tmp_path / "a.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=f=440:d=5", "-af", "apad=pad_dur=3", str(audio)], check=True)
    srt = tmp_path / "a.srt"
    srt.write_text("1\n00:00:01,000 --> 00:00:04,000\n真話\n\n2\n00:00:06,000 --> 00:00:07,500\n謝謝觀看\n", encoding="utf-8")
    return audio, srt


def test_tool_lists_then_removes_the_tail_subtitle(tmp_path, capsys):
    audio, srt = tone_then_silence(tmp_path)
    before = srt.read_text(encoding="utf-8")
    assert main(["--audio", str(audio), "--srt", str(srt)]) == 0
    assert "謝謝觀看" in capsys.readouterr().out and srt.read_text(encoding="utf-8") == before   # listed, file untouched
    out = tmp_path / "b.srt"
    assert main(["--audio", str(audio), "--srt", str(srt), "--apply", "--out", str(out)]) == 0
    assert "真話" in out.read_text(encoding="utf-8") and "謝謝觀看" not in out.read_text(encoding="utf-8")
    assert srt.read_text(encoding="utf-8") == before
