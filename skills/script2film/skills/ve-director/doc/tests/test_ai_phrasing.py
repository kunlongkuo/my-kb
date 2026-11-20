"""pytest for doc_lint.ai_phrasing (FORMAT §4「AI 味」): a report, never a lint failure."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from doc_lint import ai_phrasing  # noqa: E402


def doc(*lines, lang="zh"):
    return {"lang": lang, "lines": [{"text": t} for t in lines], "beats": []}


def test_flags_each_category_with_line_number():
    out = ai_phrasing(doc("大家好。", "我們來算這筆帳。", "說穿了，這是信心。", "記住這一點。"))
    assert [o.split()[2] for o in out] == ["2", "3", "4"]
    assert "這筆帳" in out[0] and "說穿了" in out[1] and "記住" in out[2]


def test_clean_line_and_bible_words_pass():
    # 拆毀 is scripture vocabulary, not the analytic 拆
    assert ai_phrasing(doc("耶戶拆毀巴力的廟。", "大衛在希伯崙作王。")) == []


def test_one_contrast_is_allowed_two_are_listed():
    one = doc("我們讚美的，從來不是殿，是神。", "大衛哭了。")
    assert ai_phrasing(one) == []
    two = doc("雲彩充滿帳幕，不是故事的結局，是開始。", "我們讚美的，從來不是殿，是神。")
    out = ai_phrasing(two)
    assert len(out) == 2 and all("不是…是…" in o and "2 lines in this episode" in o for o in out)


def test_english_doc_is_skipped():
    assert ai_phrasing(doc("Let's do the math on this.", lang="en")) == []


def test_check_prints_but_does_not_fail(capsys, monkeypatch):
    import doc_lint
    monkeypatch.setattr(doc_lint, "lint", lambda *a, **k: [])
    monkeypatch.setattr(doc_lint, "report_prev", lambda *a, **k: None)
    doc_lint.check(doc("問題來了，誰是王？"), {"facts": False})
    assert "⚠ ai_phrasing: line 1" in capsys.readouterr().out
