import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from doc_credits import credit_groups, outlet, outlets  # noqa: E402
from doc_cutout import fg_auto, fg_path  # noqa: E402

CREDITS = """# 素材授權

| 檔案 | 原檔 | 授權 | 作者 | 署名 | 用在 |
|---|---|---|---|---|---|
| a.jpg | https://commons.wikimedia.org/wiki/File:A.jpg | CC BY 4.0 | Ann（en.wikipedia） | 照片：Ann | B3p |
| b.jpg | https://commons.wikimedia.org/wiki/File:B.jpg | CC BY-SA 4.0 | Bob | 照片：Bob | 未使用 |
"""
FACTS = """# 事實清單

| 畫面 | 等級 | 出處 | 原文摘錄 | 備註 |
|---|---|---|---|---|
| B2 | 權威二手 | USA Today（Yahoo Sports 轉載，2026-08-18）https://x | x | |
| B3 | 原始 | MLB.com 2026-10-28 https://x | x | |
| B5 | 權威二手 | Baseball-Reference Bullpen https://x | x | |
| B5b | 權威二手 | Baseball-Reference 1982 WS Game 7 https://x | x | |
| B6 | 權威二手 | 同 B2 | x | |
| B11 | 權威二手 | Fox Sports https://x ；CBS Sports https://y | x | |
| B14c | 原始 | 中央銀行 銀行間收盤匯率 2026-10-28 https://x | x | |
"""


def test_outlet_keeps_only_the_name():
    assert outlet("USA Today（Yahoo Sports 轉載，2026-08-18）https://x") == "USA Today"
    assert outlet("MLB.com 勞資協議 https://x") == "MLB.com"
    assert outlet("TVBS 2025-03-21 https://x") == "TVBS"
    assert outlet("中央銀行 銀行間收盤匯率 https://x") == "中央銀行"
    assert outlet("Jang 轉載 2026-10 https://x") == "Jang"


def test_outlets_skip_pointers_split_pairs_and_merge_prefixes(tmp_path):
    (tmp_path / "facts.md").write_text(FACTS, encoding="utf-8")
    from doc_credits import md_table
    assert outlets(md_table(tmp_path / "facts.md")) == ["USA Today", "MLB.com", "Baseball-Reference", "Fox Sports", "CBS Sports", "中央銀行"]


def test_credit_groups_list_only_used_photos_and_say_what_is_ai(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets/CREDITS.md").write_text(CREDITS, encoding="utf-8")
    (tmp_path / "facts.md").write_text(FACTS, encoding="utf-8")
    doc = {"facts": "facts.md", "pip": {"beats": ["B1"]}, "bgm": {"credit": "本頻道自製（程式作曲）"},
           "beats": [{"id": "B3p", "source": "code", "params": {"photos": [{"src": "assets/a.jpg", "fg": "auto", "cap": "Jackson Chourio（2025）"}]}},
                     {"id": "B6", "source": "ve"}]}
    g = credit_groups(tmp_path, doc)
    assert g[0] == {"head": "照片（Wikimedia Commons）", "lines": ["Jackson Chourio：Ann（CC BY 4.0）", "部分照片經去背，沿用原授權"]}
    assert g[1]["head"] == "資料來源" and g[1]["lines"][0] == "USA Today・MLB.com・Baseball-Reference・Fox Sports"
    assert g[2]["lines"] == ["部分畫面為 AI 生成", "主持人畫面為 AI 生成", "配樂：本頻道自製（程式作曲）"]
    # a show about the tools names them
    assert credit_groups(tmp_path, {**doc, "name_tools": True})[2]["lines"][:2] == ["部分畫面為 AI 生成（VideoExpress）", "主持人畫面為 AI 生成（TalkingPhoto）"]


def test_fg_auto_points_at_an_existing_cut_out_without_redoing_it(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets/a_fg.png").write_bytes(b"x")
    p = {"photos": [{"src": "assets/a.jpg", "fg": "auto"}, {"src": "assets/c.jpg"}]}
    assert fg_path("assets/a.jpg") == "assets/a_fg.png"
    assert fg_auto(tmp_path, p)["photos"] == [{"src": "assets/a.jpg", "fg": "assets/a_fg.png"}, {"src": "assets/c.jpg"}]
    assert fg_auto(tmp_path, {"value": 3}) == {"value": 3}
