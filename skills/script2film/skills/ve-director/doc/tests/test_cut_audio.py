"""doc_cut 保底成片的聲音（s2f-1b D5）：殼頁面的 <audio> 與響度校正。

synthetic_shell_input() 產生 doc_cut.shell() 的最小合成輸入（不取自任何專案資料夾）；
tests/fixtures/shell_no_bgm.html 是 1b 改 doc_cut.py 之前，用這份輸入產生的頁面（沒有配樂、沒有 sfx_on）。
"""
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "shell_no_bgm.html"

SRT_TWO_LINES = """1
00:00:00,000 --> 00:00:01,500
第一句

2
00:00:01,600 --> 00:00:03,200
第二句
"""


def synthetic_shell_input(P):
    """Write the smallest project shell() reads into folder P and return its arguments (P, doc, beats, total, theme, hits):
    a two-line voice.cleaned/final.srt, a doc with two lines and two code beats (no burst_title, so hits=[]),
    no "bgm" and no "sfx_on": the page the fixture holds."""
    P = Path(P)
    (P / "voice.cleaned").mkdir(parents=True, exist_ok=True)
    (P / "voice.cleaned" / "final.srt").write_text(SRT_TWO_LINES, encoding="utf-8")
    doc = {"title": "合成測試", "lang": "zh-Hant",
           "lines": [{"text": "第一句"}, {"text": "第二句"}],
           "beats": [{"id": "B1", "lines": [1], "scene": "title"}, {"id": "B2", "lines": [2], "scene": "title"}]}
    beats = [{"id": "B1", "start": 0.0, "duration": 1.6, "source": "code", "tokens": []},
             {"id": "B2", "start": 1.6, "duration": 2.4, "source": "code", "tokens": []}]
    return P, doc, beats, 4.0, "collage", []


def _page(tmp_path, hits=(), **extra):
    import doc_cut
    P, doc, beats, total, theme, _ = synthetic_shell_input(tmp_path)
    doc.update(extra)
    plan = doc_cut.subtitle_plan(doc, None)
    return (doc_cut.shell(P, doc, beats, total, theme, list(hits), plan) / "index.html").read_text(encoding="utf-8")


def _audio(page):
    return re.findall(r"<audio [^>]*>", page)


def _attr(tag, name):
    return re.search(rf'{name}="([^"]*)"', tag).group(1)


def test_no_bgm_no_sfx_page_is_unchanged(tmp_path):
    """①沒有配樂、沒有 sfx_on：<audio> 只有旁白與風聲（hits=[] 沒有重擊），頁面與改 doc_cut.py 之前的夾具逐字相同。"""
    page = _page(tmp_path)
    assert [_attr(t, "id") for t in _audio(page)] == ["voice", "wind"]
    assert page == FIXTURE.read_text(encoding="utf-8")


def test_no_bgm_keeps_wind_and_impacts(tmp_path):
    """①之二：沒有配樂但有重擊時，<audio> 是旁白、風聲與每個重擊。"""
    ids = [_attr(t, "id") for t in _audio(_page(tmp_path, hits=[1.0, 2.5]))]
    assert ids == ["voice", "wind", "impact0", "impact1"]


def test_bgm_replaces_wind(tmp_path):
    """②有配樂：有 id="bgm"、沒有 id="wind"。"""
    page = _page(tmp_path, hits=[1.0], bgm={"src": "music/x.wav"})
    assert 'id="bgm"' in page and 'id="wind"' not in page
    assert 'id="sfxbed"' not in page


def test_sfx_on_adds_bed(tmp_path):
    """③sfx_on：有 id="sfxbed"；沒有配樂時風聲照舊。"""
    page = _page(tmp_path, hits=[1.0], sfx_on=True)
    assert 'id="sfxbed"' in page and 'id="wind"' in page


def test_bed_sources_and_tracks(tmp_path):
    """④src 是輸出資料夾內的相對路徑（不含 ..），配樂 track 11、音效底 track 12 加重擊個數。"""
    hits = [1.0, 2.0, 3.0]
    tags = {_attr(t, "id"): t for t in _audio(_page(tmp_path, hits=hits, bgm={"src": "music/x.wav"}, sfx_on=True))}
    assert _attr(tags["bgm"], "src") == "bgm/bgm.wav"
    assert _attr(tags["sfxbed"], "src") == "sfx/sfx_bed.wav"
    assert ".." not in _attr(tags["bgm"], "src") + _attr(tags["sfxbed"], "src")
    assert _attr(tags["bgm"], "data-track-index") == "11"
    assert _attr(tags["sfxbed"], "data-track-index") == str(12 + len(hits)) == "15"
    assert [_attr(tags[f"impact{k}"], "data-track-index") for k in range(3)] == ["12", "13", "14"]
    assert _attr(tags["bgm"], "data-duration") == _attr(tags["sfxbed"], "data-duration") == "4.0"


def _render(tmp_path, monkeypatch, returncode, calls):
    """把渲染與響度校正換成假函式後呼叫 doc_cut.render()；loudnorm 收到的參數記進 calls。"""
    import doc_cut
    monkeypatch.setattr(doc_cut, "hyperframes", lambda *a, **kw: SimpleNamespace(returncode=returncode))
    monkeypatch.setattr(doc_cut, "loudnorm", lambda *a, **kw: calls.append((a, kw)))
    doc_cut.render(tmp_path)


def test_render_success_calls_loudnorm_with_str(tmp_path, monkeypatch):
    """⑤渲染成功：loudnorm 呼叫一次，參數是 output.mp4 的字串路徑。"""
    calls = []
    _render(tmp_path, monkeypatch, 0, calls)
    assert len(calls) == 1
    (arg,), kw = calls[0]
    assert type(arg) is str and arg == str(tmp_path / "output.mp4") and kw == {}


def test_render_failure_skips_loudnorm(tmp_path, monkeypatch):
    """⑤渲染失敗：停下，沒呼叫 loudnorm。"""
    calls = []
    with pytest.raises(SystemExit):
        _render(tmp_path, monkeypatch, 1, calls)
    assert calls == []


def test_capcut_flag_stops_with_render_hint(tmp_path, monkeypatch):
    """--capcut 已移除（s2f-naming D1）：load() 之後立刻停下，專案裡沒有 beats.json 也是同一個訊息。"""
    import json
    import doc_cut
    (tmp_path / "doc.json").write_text(json.dumps({"title": "t", "lang": "zh"}), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["doc_cut.py", str(tmp_path / "doc.json"), "--capcut"])
    with pytest.raises(SystemExit) as e:
        doc_cut.main()
    assert e.value.code != 0 and "--render" in str(e.value) and "plan2concat_mcp.py" in str(e.value)
