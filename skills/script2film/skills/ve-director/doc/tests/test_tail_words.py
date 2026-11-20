"""doc_align.tail_report：逐字時間的尾巴落在檔尾靜音之後才印一行；沒有就不印；量不到靜音另外說。"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_align  # noqa: E402


def audio(tmp_path, pad):
    f = tmp_path / "a.wav"
    af = ["-af", f"apad=pad_dur={pad}"] if pad else []
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=f=440:d=5", *af, str(f)], check=True)
    return f


def timing(tmp_path, words):
    f = tmp_path / "w.json"
    f.write_text(json.dumps({"segments": [{"words": [{"word": w, "start": a, "end": b} for w, a, b in words]}]}), encoding="utf-8")
    return f


def test_tail_word_is_reported(tmp_path):
    note = doc_align.tail_report(timing(tmp_path, [(" real", 1.0, 1.5), (" thanks", 6.0, 6.5), (" watching", 6.5, 7.0)]), audio(tmp_path, 3))
    assert "after the closing silence" in note and "2 words" in note and "thanks watching" in note


def test_nothing_printed_without_a_tail_word(tmp_path):
    assert doc_align.tail_report(timing(tmp_path, [(" real", 1.0, 1.5), (" end", 4.2, 4.8)]), audio(tmp_path, 3)) is None


def test_says_so_when_no_silence_is_found(tmp_path):
    assert "no silence found" in doc_align.tail_report(timing(tmp_path, [(" real", 1.0, 1.5)]), audio(tmp_path, 0))
