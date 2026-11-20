"""yt_snippet：上傳用的 snippet（不匯入 yt_upload，它要 Google 的套件）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from yt_snippet import upload_snippet  # noqa: E402


def test_upload_snippet_fields_and_empty_tags_dropped():
    assert upload_snippet("t", "d", "a,,b", "27", "zh-Hant") == {
        "title": "t", "description": "d", "tags": ["a", "b"], "categoryId": "27", "defaultLanguage": "zh-Hant"}


def test_upload_snippet_language_and_no_tags():
    s = upload_snippet("t", "d", "", "25", "en")
    assert s["defaultLanguage"] == "en" and s["tags"] == []
