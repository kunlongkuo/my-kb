"""doc_align.chunks: a closing quote after 「…？」 stays with its sentence (2026-11-05 面對 AI 的迎合: a screen of only 「」」 had
no words and doc_align divided by zero)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_align  # noqa: E402
from doc_common import tokens  # noqa: E402


def check(text):
    out = doc_align.chunks(text, "zh")
    assert "".join(out) == text
    assert all(tokens(c, "zh") for c in out), out
    return out


def test_quote_after_question_mark_stays_with_it():
    out = check("有人問耶穌：「誰是我的鄰舍呢？」祂沒有直接給一個定義，而是講了故事。")
    assert "「誰是我的鄰舍呢？」" in out


def test_quote_at_end_of_line():
    out = check("彼得說：「各人要照所得的恩賜彼此服事，作神百般恩賜的好管家。」")
    assert out[-1].endswith("好管家。」")


def test_quote_then_comma():
    out = check("像是「做好事不信耶穌，會下地獄嗎？」，AI 拼出來的答案很雜。")
    assert any(c.endswith("嗎？」，") for c in out)
