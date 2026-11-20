"""preflight 事實清單：doc.json 有 "facts" 時，facts.md 少一列就列出問題（夜跑第 0 步不開跑）。"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[2] / "checklist"
sys.path.insert(0, str(HERE))
from items import facts_problems  # noqa: E402

DOC = {"facts": "facts.md", "beats": [{"id": "B1", "source": "code", "scene": "quote_card",
                                       "params": {"text": "示範引文", "by": "某書 1:1"}}]}
HEAD = "| 畫面 | 等級 | 出處 | 原文摘錄 | 備註 |\n|---|---|---|---|---|\n"


def test_complete_list_passes(tmp_path):
    (tmp_path / "facts.md").write_text(HEAD + "| 示範引文 | 原始 | 某書 1:1 | 示範引文，後面還有半句 | B1 |\n")
    assert facts_problems(DOC, tmp_path) == []


def test_missing_row_is_listed(tmp_path):
    (tmp_path / "facts.md").write_text(HEAD)
    out = facts_problems(DOC, tmp_path)
    assert out and all("B1" in m for m in out)
