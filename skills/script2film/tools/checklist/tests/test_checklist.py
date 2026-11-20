"""清單本體：找集資料夾、分段分層、系列宣告不適用、單集、gate 的四條路。項目換成假的，不碰真的環境。"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import checklist  # noqa: E402
import items  # noqa: E402


def fake(id, layer, stage, ok=True, format=None, na_ok=False):
    return {"id": id, "layer": layer, "format": format, "stage": stage, "na_ok": na_ok, "label": id,
            "fn": lambda c: [(id, ok, "")]}


@pytest.fixture
def fakes(monkeypatch):
    def use(*xs):
        monkeypatch.setattr(items, "ITEMS", list(xs))
    return use


def episode(tmp_path, kind="doc.json", series=None):
    ep = tmp_path / "系列" / "EP01"
    ep.mkdir(parents=True)
    (ep / kind).write_text("{}", encoding="utf-8")
    if series is not None:
        (ep.parent / "series.json").write_text(json.dumps(series, ensure_ascii=False), encoding="utf-8")
    return ep


def ids(out, state=None):
    return [r["id"] for r in out["items"] if r["id"] != "answers" and (state is None or r["state"] == state)]


def test_find_episode_from_file_in_episode(tmp_path):
    ep = episode(tmp_path)
    (ep / "ve").mkdir()
    sheet = ep / "ve" / "runsheet.md"
    sheet.write_text("", encoding="utf-8")
    assert checklist.find_episode(sheet) == (ep.resolve(), "doc")


def test_find_episode_day_folder(tmp_path):
    ep = episode(tmp_path, "day.json")
    assert checklist.find_episode(ep / "runsheet-sky.md") == (ep.resolve(), "book")


def test_find_episode_skips_nested_stub_doc(tmp_path):
    """送 VE 的 run sheet 在 <集>/extra_live/，那裡也有一份 doc.json：要找到的是整集。"""
    ep = episode(tmp_path)
    (ep / "extra_live").mkdir()
    (ep / "extra_live/doc.json").write_text("{}", encoding="utf-8")
    sheet = ep / "extra_live/storyboard_live.md"
    sheet.write_text("", encoding="utf-8")
    assert checklist.find_episode(sheet) == (ep.resolve(), "doc")
    with pytest.raises(checklist.ConfigError, match="is a subfolder of"):
        checklist.run(ep / "extra_live", "start")


def test_find_episode_none(tmp_path):
    (tmp_path / "story").mkdir()
    assert checklist.find_episode(tmp_path / "story" / "board.md") is None


def test_upper_array_doc_is_not_an_episode(tmp_path, capsys):
    """上層剛好有一份內容是陣列的 doc.json（別的工具的輸出）：那不是集，--skip-checklist 也不必用就放行。"""
    (tmp_path / "x/sub").mkdir(parents=True)
    (tmp_path / "x/doc.json").write_text("[]", encoding="utf-8")
    prompts = tmp_path / "x/sub/prompts.json"
    prompts.write_text("[]", encoding="utf-8")
    ignored = []
    assert checklist.find_episode(prompts, ignored) is None and (tmp_path / "x/doc.json").resolve() in ignored
    checklist.gate(prompts, "start", None, "ve")
    out = capsys.readouterr().out
    assert "does not hold a readable JSON object" in out and "checklist does not apply" in out
    ep = episode(tmp_path / "y")                                           # 集底下的子資料夾放了一份陣列 doc.json：照樣找到整集
    (ep / "extra").mkdir()
    (ep / "extra/doc.json").write_text("[]", encoding="utf-8")
    assert checklist.find_episode(ep / "extra/board.md") == (ep.resolve(), "doc")


def test_upper_broken_doc_is_not_an_episode(tmp_path, capsys):
    (tmp_path / "x/sub").mkdir(parents=True)
    (tmp_path / "x/doc.json").write_text("{broken", encoding="utf-8")
    video = tmp_path / "x/sub/film.mp4"
    video.write_text("", encoding="utf-8")
    assert checklist.find_episode(video) is None
    with pytest.raises(SystemExit) as e:                                   # 上傳：集外的片照舊要寫原因
        checklist.gate(video, "release", None, "upload", outside_ok=False)
    assert e.value.code == 1
    checklist.gate(video, "release", "測試", "upload", outside_ok=False)   # 寫了原因就放行（以前連原因都帶不過）
    assert json.loads((tmp_path / "x/sub/checklist_skips.jsonl").read_text(encoding="utf-8"))["failed"] == ["outside-episode"]


def test_named_bad_episode_file_still_fails(tmp_path, capsys):
    """明確指定的集（直接傳那份 doc.json，或 checklist.py run 那個資料夾）壞了要報錯，不能安靜當成不是集。"""
    z = tmp_path / "z"
    z.mkdir()
    (z / "doc.json").write_text("[]", encoding="utf-8")
    with pytest.raises(checklist.ConfigError, match="must hold an object"):
        checklist.find_episode(z / "doc.json")
    with pytest.raises(SystemExit) as e:
        checklist.gate(z / "doc.json", "start", "測試", "ve")
    assert e.value.code == 2 and "must hold an object" in capsys.readouterr().out
    with pytest.raises(checklist.ConfigError, match="must hold an object"):
        checklist.run(z, "start")
    with pytest.raises(SystemExit) as e:                                   # tp_host.py 傳的是集資料夾本身
        checklist.gate(z, "start", "測試", "tp")
    assert e.value.code == 2
    (z / "doc.json").write_text("{broken", encoding="utf-8")
    assert checklist.main(["run", str(z), "--stage", "start"]) == 2 and "cannot read" in capsys.readouterr().out


def test_release_includes_start(tmp_path, fakes):
    fakes(fake("a", "base", "start"), fake("b", "base", "release"))
    ep = episode(tmp_path)
    assert ids(checklist.run(ep, "start")) == ["series", "a"]
    assert ids(checklist.run(ep, "release")) == ["series", "a", "b"]


def test_book_format_skips_doc_items(tmp_path, fakes):
    fakes(fake("a", "base", "start"), fake("d", "format", "start", format="doc"))
    assert ids(checklist.run(episode(tmp_path, "day.json"), "start")) == ["series", "a"]
    assert ids(checklist.run(episode(tmp_path / "x"), "start")) == ["series", "a", "d"]


def test_single_episode_skips_series_layer(tmp_path, fakes):
    fakes(fake("a", "base", "start"), fake("s", "series", "start", ok=False))
    out = checklist.run(episode(tmp_path), "start")
    assert out["ok"] and ids(out) == ["series", "a"]
    assert out["items"][0]["state"] == "na" and "single episode" in out["items"][0]["detail"]


def test_series_layer_runs_with_series_json(tmp_path, fakes):
    fakes(fake("s", "series", "start", ok=False))
    out = checklist.run(episode(tmp_path, series={"name": "系列"}), "start")
    assert not out["ok"] and ids(out, "fail") == ["s"]


def test_na_with_reason(tmp_path, fakes):
    fakes(fake("a", "base", "start"), fake("u", "series", "start", ok=False, na_ok=True))
    out = checklist.run(episode(tmp_path, series={"name": "系列", "checklist": {"na": {"u": "手寫說明欄"}}}), "start")
    assert out["ok"] and ids(out, "na") == ["u"] and "手寫說明欄" in out["items"][-2]["detail"]


def test_na_on_item_that_cannot_be_waived(tmp_path, fakes):
    fakes(fake("a", "base", "start", ok=False))
    with pytest.raises(checklist.ConfigError, match="cannot be declared not applicable"):
        checklist.run(episode(tmp_path, series={"name": "系列", "checklist": {"na": {"a": "不想跑"}}}), "start")


def test_na_empty_reason(tmp_path, fakes):
    fakes(fake("u", "series", "start", na_ok=True))
    with pytest.raises(checklist.ConfigError, match="is empty"):
        checklist.run(episode(tmp_path, series={"name": "系列", "checklist": {"na": {"u": " "}}}), "start")


def test_real_items_base_layer_cannot_be_waived():
    assert not [x["id"] for x in items.ITEMS if x["layer"] == "base" and x["na_ok"]]
    assert [x["id"] for x in items.ITEMS if x["na_ok"]] == ["upload-fields"]


def test_main_exit_codes(tmp_path, fakes, capsys):
    fakes(fake("a", "base", "start"))
    ep = episode(tmp_path)
    assert checklist.main(["run", str(ep), "--stage", "start"]) == 0
    assert json.loads((ep / "nightly/checklist_start.json").read_text(encoding="utf-8"))["ok"] is True
    fakes(fake("a", "base", "start", ok=False))
    assert checklist.main(["run", str(ep), "--stage", "start"]) == 1
    assert checklist.main(["run", str(tmp_path), "--stage", "start"]) == 2
    assert "has neither doc.json nor day.json" in capsys.readouterr().out


def test_gate_outside_episode_passes(tmp_path, capsys):
    checklist.gate(tmp_path / "board.md", "start", None, "ve")
    assert "checklist does not apply" in capsys.readouterr().out


def test_gate_pass(tmp_path, fakes):
    fakes(fake("a", "base", "start"))
    checklist.gate(episode(tmp_path), "start", None, "tp")


def test_gate_fail_exits_1(tmp_path, fakes, capsys):
    fakes(fake("a", "base", "start", ok=False))
    with pytest.raises(SystemExit) as e:
        checklist.gate(episode(tmp_path), "start", None, "tp")
    assert e.value.code == 1 and "✗ a" in capsys.readouterr().out


def test_gate_skip_writes_one_line(tmp_path, fakes):
    fakes(fake("a", "base", "start", ok=False))
    ep = episode(tmp_path)
    checklist.gate(ep, "start", "測試", "tp")
    rows = [json.loads(x) for x in (ep / "nightly/checklist_skips.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1 and rows[0]["step"] == "tp" and rows[0]["reason"] == "測試" and rows[0]["failed"] == ["a"]


def test_gate_blank_reason_exits_2(tmp_path, fakes):
    fakes(fake("a", "base", "start", ok=False))
    ep = episode(tmp_path)
    with pytest.raises(SystemExit) as e:
        checklist.gate(ep, "start", "  ", "tp")
    assert e.value.code == 2 and not (ep / "nightly/checklist_skips.jsonl").exists()


def test_gate_bad_config_cannot_be_skipped(tmp_path, fakes):
    fakes(fake("a", "base", "start"))
    ep = episode(tmp_path, series={"name": "系列", "checklist": {"na": {"a": "x"}}})
    with pytest.raises(SystemExit) as e:
        checklist.gate(ep, "start", "測試", "tp")
    assert e.value.code == 2


def test_release_check(tmp_path):
    ep = episode(tmp_path)
    assert items.release_check(ep)[0] is False                       # 沒有 check.json
    (ep / "nightly").mkdir()
    mp4 = ep / "film.mp4"
    mp4.write_bytes(b"x")
    chk = ep / "nightly/check.json"
    chk.write_text(json.dumps({"ok": True, "video": "elsewhere/film.mp4"}), encoding="utf-8")
    assert items.release_check(ep) == (True, "film.mp4")             # 相對路徑找不到時用檔名到集資料夾找
    import os
    os.utime(mp4, (chk.stat().st_mtime + 10,) * 2)                   # 成片比檢查新
    assert items.release_check(ep)[0] is False
    chk.write_text(json.dumps({"ok": False, "video": "film.mp4"}), encoding="utf-8")
    assert items.release_check(ep)[0] is False


# ---- 逐條作答 ----

def doc_episode(tmp_path, lines=("第一句", "第二句"), series=None):
    ep = episode(tmp_path, series=series)
    (ep / "doc.json").write_text(json.dumps({"lines": [{"text": t} for t in lines]}, ensure_ascii=False), encoding="utf-8")
    return ep


def answers_row(out):
    return next(r for r in out["items"] if r["id"] == "answers")


@pytest.mark.real_rules
def test_shipped_rules_by_format_and_stage():
    q = lambda fmt, stage: [r["id"] for r in checklist.questions(None, fmt, [stage])]
    assert q("doc", "start") == ["named-place", "inventory-read"]
    assert q("doc", "release") == ["named-place", "listen-names"]
    assert q("book", "start") == [] and q("book", "release") == ["listen-names"]


@pytest.mark.real_rules
def test_h3_question_only_for_episodes_that_use_h3(tmp_path, fakes):
    """h3-territory has when_file h3/manifest.json: asked (and answerable) only once tools/h3 planned this episode."""
    fakes(fake("a", "base", "start"))
    ep = doc_episode(tmp_path)
    ids = lambda: [r["id"] for r in checklist.questions(None, "doc", ["start"], ep)]
    assert "h3-territory" not in ids()
    assert checklist.main(["answer", str(ep), "h3-territory", "台灣"]) == 2
    (ep / "h3").mkdir()
    (ep / "h3/manifest.json").write_text("{}", encoding="utf-8")
    assert ids()[-1] == "h3-territory"
    assert "h3-territory: not answered" in answers_row(checklist.run(ep, "start"))["detail"]
    assert checklist.main(["answer", str(ep), "h3-territory", "台灣，片子在台灣用"]) == 0
    assert "h3-territory" not in answers_row(checklist.run(ep, "start"))["detail"]


@pytest.mark.real_rules
def test_unanswered_then_answered_then_narration_changed(tmp_path, fakes):
    fakes(fake("a", "base", "start"))
    ep = doc_episode(tmp_path)
    row = answers_row(checklist.run(ep, "start"))
    assert not row["ok"] and "named-place: not answered" in row["detail"] and "inventory-read: not answered" in row["detail"]
    assert checklist.main(["answer", str(ep), "named-place", "B3 用生成畫面，沒有標地名"]) == 0
    assert checklist.main(["answer", str(ep), "inventory-read", "連續純字卡 20 秒"]) == 0
    assert checklist.run(ep, "start")["ok"]
    doc_episode(tmp_path / "x")                                           # 另一集不受影響
    (ep / "doc.json").write_text(json.dumps({"lines": [{"text": "第一句"}, {"text": "改過的第二句"}]}, ensure_ascii=False), encoding="utf-8")
    row = answers_row(checklist.run(ep, "start"))
    assert not row["ok"] and "named-place: narration changed, confirm again" in row["detail"]


@pytest.mark.real_rules
def test_answer_exit_codes(tmp_path):
    ep = doc_episode(tmp_path)
    assert checklist.main(["answer", str(ep), "no-such-rule", "x"]) == 2
    assert checklist.main(["answer", str(ep), "named-place", "  "]) == 2
    assert not (ep / "checklist_answers.json").exists()


@pytest.mark.real_rules
def test_book_format_is_only_asked_listen_names(tmp_path, fakes):
    fakes(fake("a", "base", "start"))
    ep = episode(tmp_path, "day.json")
    (ep / "day.json").write_text(json.dumps({"narration": [{"text": "一段"}]}, ensure_ascii=False), encoding="utf-8")
    assert checklist.run(ep, "start")["ok"]
    row = answers_row(checklist.run(ep, "release"))
    assert not row["ok"] and row["detail"].startswith("listen-names: not answered")


def test_series_questions_are_added(tmp_path, fakes):
    fakes(fake("a", "base", "start"))
    series = {"name": "系列", "checklist": {"rules": [{"id": "gov-photo", "stage": "start", "ask": "照片出處？", "source": "SERIES.md:36"}]}}
    ep = doc_episode(tmp_path, series=series)
    assert "gov-photo: not answered" in answers_row(checklist.run(ep, "start"))["detail"]
    assert checklist.main(["answer", str(ep), "gov-photo", "都是總統府公布的"]) == 0
    assert checklist.run(ep, "start")["ok"]


def test_unlisted_assets(tmp_path):
    ep = episode(tmp_path)
    assert items.unlisted_assets(ep) == []                                   # 沒有 assets/
    (ep / "assets/src").mkdir(parents=True)
    for name in ("a.jpg", "b.mp4", "note.txt", "src/raw.jpg"):
        (ep / "assets" / name).write_bytes(b"x")
    assert items.unlisted_assets(ep) == ["a.jpg", "b.mp4"]                   # 沒有 CREDITS.md：兩個都沒登記；txt 與 src/ 不算
    (ep / "assets/CREDITS.md").write_text("| a.jpg | 某人 | CC BY 4.0 |", encoding="utf-8")
    assert items.unlisted_assets(ep) == ["b.mp4"]
    (ep / "assets/CREDITS.md").write_text("| a.jpg | … |\n| b.mp4 | … |", encoding="utf-8")
    assert items.unlisted_assets(ep) == []
    (ep / "assets/a_fg.png").write_bytes(b"x")                               # 工具去背的圖跟著原圖算
    (ep / "assets/z_fg.png").write_bytes(b"x")                               # 原圖沒登記的不算
    assert items.unlisted_assets(ep) == ["z_fg.png"]


@pytest.mark.parametrize("kind,body", [
    ("doc.json", {}),
    ("doc.json", {"lang": "zh", "lines": [{"text": "第一句"}], "beats": [{"id": "B1", "lines": [1], "source": "code", "scene": "quote_card"}]}),
    ("day.json", {}),
])
def test_real_items_run_on_a_bare_episode_without_writing(tmp_path, monkeypatch, kind, body):
    """真的項目對一個幾乎空的集資料夾跑兩段：每一項都回得出結果（不丟例外），write=False 時集資料夾裡不多出任何檔。
    查 YouTube 權杖那一項會連線，這裡拿掉。"""
    monkeypatch.setattr(items, "ITEMS", [i for i in items.ITEMS if i["id"] != "yt-token"])
    ep = episode(tmp_path, kind, series={"name": "系列"})
    (ep / kind).write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
    before = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*"))
    for stage in ("start", "release"):
        out = checklist.run(ep, stage, environ={}, write=False)
        assert out["items"] and all({"id", "item", "ok", "detail", "state"} <= set(r) for r in out["items"])
    assert sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*")) == before


def test_power_item_without_pmset(monkeypatch):
    monkeypatch.setattr(items.shutil, "which", lambda name: None)
    assert items._power({}) == [("on AC power (reminder only)", True, "no pmset on this machine: not checked")]


def test_power_item_on_battery_only_reminds(monkeypatch):
    class R:
        stdout = "Now drawing from 'Battery Power'\n -InternalBattery-0 80%\n"
    monkeypatch.setattr(items.shutil, "which", lambda name: "/usr/bin/pmset")
    monkeypatch.setattr(items.subprocess, "run", lambda *a, **k: R())
    (name, ok, detail), = items._power({})
    assert ok is True and detail.startswith("not on AC power")


def test_gate_outside_episode_stops_when_not_allowed(tmp_path, capsys):
    film = tmp_path / "film.mp4"
    film.write_bytes(b"")
    with pytest.raises(SystemExit) as e:
        checklist.gate(film, "release", None, "upload", outside_ok=False)
    assert e.value.code == 1 and "not in an episode folder" in capsys.readouterr().out
    with pytest.raises(SystemExit) as e:
        checklist.gate(film, "release", " ", "upload", outside_ok=False)
    assert e.value.code == 2
    checklist.gate(film, "release", "母帶備份重傳", "upload", outside_ok=False)
    row = json.loads((tmp_path / "checklist_skips.jsonl").read_text(encoding="utf-8"))
    assert row["step"] == "upload" and row["reason"] == "母帶備份重傳" and row["failed"] == ["outside-episode"]


@pytest.mark.real_rules
def test_release_also_asks_the_start_questions(tmp_path, fakes):
    """出片段包含開工段：開工段的題目沒答（或旁白改過）一樣不過。"""
    fakes()
    ep = episode(tmp_path)
    (ep / "doc.json").write_text(json.dumps({"lines": [{"text": "一"}]}), encoding="utf-8")
    for q in ("named-place", "listen-names"):
        assert checklist.main(["answer", str(ep), q, "答"]) == 0
    row = [r for r in checklist.run(ep, "release", write=False)["items"] if r["id"] == "answers"][0]
    assert not row["ok"] and "inventory-read: not answered" in row["detail"]
    assert checklist.main(["answer", str(ep), "inventory-read", "答"]) == 0
    assert [r for r in checklist.run(ep, "release", write=False)["items"] if r["id"] == "answers"][0]["ok"]


def lead_doc(at, **beat):
    return {"lang": "zh", "lines": [{"text": "路加福音第五章寫到湖邊有兩隻船，其中一隻是西門彼得的"}],
            "beats": [{"id": "B8", "lines": [1], "source": "code", "scene": "quote_card", "params": {"text": "引言", "at": at}, **beat}]}


def test_lead_estimate_stops_a_late_card_before_any_voice(tmp_path):
    ep = episode(tmp_path)
    ctx = lambda doc: {"ep": ep, "doc": doc}
    (name, ok, detail), = items._lead_estimate(ctx(lead_doc("其中一隻")))   # 第 16 個字，估 3.2 秒
    assert not ok and "B8" in detail and "estimate" in detail
    assert items._lead_estimate(ctx(lead_doc("路加福音")))[0][1] is True
    assert items._lead_estimate(ctx(lead_doc(0.3)))[0][1] is True
    assert items._lead_estimate(ctx(lead_doc("其中一隻", bg_video={"src": "a.mp4"})))[0][1] is True
    assert items._lead_estimate(ctx({**lead_doc("其中一隻"), "lang": "en"}))[0][1] is True   # 英文稿不估


def test_blank_lead_stops_on_measured_late_card(tmp_path):
    ep = episode(tmp_path)
    doc = lead_doc("其中一隻")
    toks = [[c, round(i * 0.2, 2)] for i, c in enumerate("路加福音第五章寫到湖邊有兩隻船其中一隻是西門彼得的")]
    (ep / "beats.json").write_text(json.dumps({"beats": [{"id": "B8", "lines": [1], "tokens": toks}]}, ensure_ascii=False), encoding="utf-8")
    (name, ok, detail), = items._blank_lead({"ep": ep, "doc": doc})
    assert not ok and "B8" in detail
    assert items._lead_estimate({"ep": ep, "doc": doc})[0][0] == "blank card lead"   # 對時過就用實測


def test_packs_are_asked_only_when_the_series_picks_them(tmp_path):
    q = lambda series, want: [r["id"] for r in checklist.questions(series, "doc", want)]
    assert q({"name": "s"}, ["start"]) == []
    got = q({"name": "s", "checklist": {"packs": ["scripture", "publishing"]}}, ["start", "release"])
    assert "scripture-checked" in got and "channel-checked" in got and "neutral-wording" not in got
    assert "host-look" not in got and "host-look" in q({"name": "s", "checklist": {"packs": ["host"]}}, ["start"])
    with pytest.raises(checklist.ConfigError):
        q({"name": "s", "checklist": {"packs": ["no-such-pack"]}}, ["start"])
    with pytest.raises(checklist.ConfigError):
        q({"name": "s", "checklist": {"packs": ["../rules"]}}, ["start"])
    with pytest.raises(checklist.ConfigError):   # 系列自己的題目不能和包裡的撞代號
        q({"name": "s", "checklist": {"packs": ["scripture"], "rules": [{"id": "scripture-checked", "stage": "start", "ask": "?"}]}}, ["start"])


@pytest.mark.real_rules
def test_shipped_packs_are_well_formed():
    ids = [r["id"] for r in json.loads(checklist.RULES.read_text(encoding="utf-8"))["rules"]]
    for p in sorted(checklist.PACKS.glob("*.json")):
        for r in json.loads(p.read_text(encoding="utf-8"))["rules"]:
            assert r["id"] and r["ask"] and r["source"] and set(r["stage"]) <= set(checklist.STAGES), (p.name, r)
            ids.append(r["id"])
    assert len(ids) == len(set(ids))


def subs_episode(tmp_path, doc=None, series=None, files=("subtitles_zh.srt",)):
    ep = episode(tmp_path, series=series)
    (ep / "doc.json").write_text(json.dumps(doc or {"lang": "zh"}, ensure_ascii=False), encoding="utf-8")
    (ep / "beats.json").write_text("{}", encoding="utf-8")
    (ep / "cut_x.json").write_text("{}", encoding="utf-8")            # 同名開頭的檔，不是資料夾
    (ep / "cut_x").mkdir()
    for f in files:
        (ep / "cut_x" / f).write_text("1\n00:00:00,000 --> 00:00:01,000\n字\n", encoding="utf-8")
    return ep


def subs_row(ep, series=None):
    return items._subs_files({"ep": ep, "doc": json.loads((ep / "doc.json").read_text(encoding="utf-8")), "series": series})[0]


def test_subs_files_only_when_burn_is_set(tmp_path):
    burn = {"name": "s", "subs": {"burn": "zh"}}
    ep = subs_episode(tmp_path)
    assert subs_row(ep, None)[1:] == (True, "subs.burn not set: not checked")            # 單集，沒設
    assert subs_row(ep, {"name": "s"})[1:] == (True, "subs.burn not set: not checked")   # 系列也沒設
    ok = subs_row(ep, burn)
    assert ok[1] is True and "cut_x/subtitles_zh.srt" in ok[2]
    (ep / "cut_x/subtitles_zh.srt").unlink()
    miss = subs_row(ep, burn)
    assert miss[1] is False and "--captions-only" in miss[2]


def test_subs_files_stale_and_translation(tmp_path):
    import os
    ep = subs_episode(tmp_path, doc={"lang": "en", "zh": ["一"], "subs": {"burn": "zh"}})
    need = subs_row(ep)
    assert need[1] is False and "subtitles_en.srt" in need[2]                  # 旁白那一份不在
    (ep / "cut_x/subtitles_en.srt").write_text("x", encoding="utf-8")
    assert subs_row(ep)[1] is True
    old = (ep / "beats.json").stat().st_mtime - 100
    os.utime(ep / "cut_x/subtitles_zh.srt", (old, old))
    stale = subs_row(ep)
    assert stale[1] is False and "is older than beats.json" in stale[2]


def test_caption_hint(tmp_path):
    ep = subs_episode(tmp_path)
    text = items.caption_hint(ep)
    assert "YouTube Studio" in text and str(ep / "cut_x/subtitles_zh.srt") in text and "  zh  " in text
    (ep / "cut_x/subtitles_zh.srt").unlink()
    assert items.caption_hint(ep) == ""


def test_series_lookup_matches_the_doc_scripts(tmp_path):
    sys.path.insert(0, str(items.DOC_SCRIPTS))
    import doc_common
    ep = episode(tmp_path)
    assert doc_common.series_of(ep) is None and items.series_cfg(ep)[0] is None
    (ep.parent / "series.json").write_text(json.dumps({"name": "s", "subs": {"burn": "zh"}}), encoding="utf-8")
    assert doc_common.series_of(ep) == items.series_cfg(ep)[0]


def test_caption_files_follow_the_cut_whose_captions_are_newest(tmp_path):
    import os
    ep = subs_episode(tmp_path)                                        # cut_x with a caption file
    (ep / "cut_y").mkdir()
    t = (ep / "cut_y").stat().st_mtime
    os.utime(ep / "cut_x", (t - 500, t - 500))                         # cut_x the older folder …
    os.utime(ep / "cut_x/subtitles_zh.srt", (t + 500, t + 500))        # … but its caption file was just written (--captions-only)
    assert items.caption_files(ep)[0][1].parent.name == "cut_x"
    assert subs_row(ep, {"name": "s", "subs": "zh"})[1:] == (True, "subs.burn not set: not checked")   # 寫壞的 subs 不當掉
