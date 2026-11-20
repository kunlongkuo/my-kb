import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dramalib as dl  # noqa: E402

CUT = {"name": "t", "shots": [
    {"id": "D0", "card": "片頭", "dur": 3.0, "sfx": [{"name": "rooster", "at": 0.6, "db": -10}]},
    {"id": "A", "src": "a.mp4", "in": 0.5, "dur": 4.0, "sfx": [{"name": "feet", "at": 0.3, "db": -8}]},
    {"id": "B", "src": "b.mp4", "in": 0, "dur": 4.0, "speaker": "小美", "sub": {"text": "阿明，下來。", "from": 0.2, "to": 1.6}},
    {"id": "C", "src": "c.mp4", "in": 0, "dur": 5.0, "sfx": [{"name": "water", "at": 0.2, "db": -12}]},
]}


def seg(mid, start, dur, src=0.0):
    return {"material_id": mid, "target_timerange": {"start": int(start * 1e6), "duration": int(dur * 1e6)},
            "source_timerange": {"start": int(src * 1e6), "duration": int(dur * 1e6)}}


def test_offsets_and_subtitles_clamp_to_real_length():
    assert dl.offsets(CUT["shots"]) == [0.0, 3.0, 7.0, 11.0]
    subs = dl.subtitles(CUT["shots"], [3.0, 4.0, 1.5, 5.0])  # B 實際只有 1.5 秒：字幕截在 1.48
    assert subs == [(7.2, 7.0 + 1.48, "阿明，下來。")]


def test_lanes_never_overlap():
    assert dl.lanes([(0, 4), (1, 2), (3.5, 1), (4, 1)]) == [0, 1, 1, 0]


def test_sfx_cues_numbering_follows_shot_order():
    cues = dl.sfx_cues(CUT["shots"])
    assert [(c["k"], c["name"], c["at"], c["rel"]) for c in cues] == [(0, "rooster", 0.6, 0.6), (1, "feet", 3.3, 0.3),
                                                                      (2, "water", 11.2, 0.2)]


def test_line_status():
    words = [{"word": "阿明", "start": 0.0, "end": 0.46}, {"word": "下來", "start": 0.46, "end": 1.14}]
    ok = dl.line_status("阿明，下來。", words, 4.0)
    assert ok["ok"] and ok["tail"] == 2.86
    cut_off = dl.line_status("醒了就洗臉，飯在桌上放著。", [{"word": "醒了就洗臉飯在桌上放", "start": 1.5, "end": 4.0}], 4.04)
    assert cut_off["truncated"] and not cut_off["ok"]
    late_but_whole = dl.line_status("我再想一想。", [{"word": "我再想一想", "start": 1.56, "end": 2.68}], 4.04)
    assert late_but_whole["ok"] and late_but_whole["lead"] == 1.56  # 晚開口但句子完整：剪接修空白就好
    assert not dl.line_status("謝謝。", [], 4.0)["ok"]


def test_text_of_both_formats():
    assert dl.text_of('{"text": "謝謝。", "styles": []}') == "謝謝。"
    assert dl.text_of('<font id="" path="x.ttf"><color=(1,1,1,1)><size=5.0>[阿明，下來。]</size></color></font>') == "阿明，下來。"


def test_pull_reads_user_edits():
    """使用者在剪輯軟體裡：拿掉 A、B 移到 C 後面、C 修短並入點後移、音效 water 移到 B、feet 刪掉、對白聲音晚 0.27 秒。"""
    names = {"v0": "00_D0.mp4", "v2": "02_B.mp4", "v3": "03_C.mp4",
             "s0": "sfx_00_rooster.wav", "s2": "sfx_02_water.wav", "l2": "02_B_小美.wav", "t1": "阿明，下來。"}
    draft = {"tracks": [
        {"type": "video", "segments": [seg("v0", 0, 3.0), seg("v3", 3.0, 2.5, src=1.0), seg("v2", 5.5, 4.0)]},
        {"type": "audio", "segments": [seg("s0", 0.6, 4.0), seg("s2", 5.9, 3.0)]},
        {"type": "audio", "segments": [seg("l2", 5.77, 4.0)]},
        {"type": "text", "segments": [seg("t1", 5.8, 1.3)]},
    ]}
    new, report = dl.pull(CUT, draft, names)
    assert [s["id"] for s in new["shots"]] == ["D0", "C", "B"]
    c = new["shots"][1]
    assert c["in"] == 1.0 and c["dur"] == 2.5 and c["sfx"] == []
    b = new["shots"][2]
    assert b["sfx"] == [{"name": "water", "at": 0.4, "db": -12}]  # 音量照原設定
    assert b["sub"] == {"text": "阿明，下來。", "from": 0.3, "to": 1.6}
    text = "\n".join(report)
    assert "removed: A" in text and "reordered: D0 → C → B" in text and "trimmed C" in text
    assert "removed sound effect: feet" in text and "sound effect water: moved to B" in text and "dialogue B: on the timeline the sound is 0.27s behind the picture" in text
    assert "rooster" not in text  # 沒動的不報


def test_pull_unknown_segment_is_reported_not_fatal():
    new, report = dl.pull(CUT, {"tracks": [{"type": "video", "segments": [seg("x", 0, 2)]}]}, {"x": "mystery.mp4"})
    assert new["shots"] == [] and "unrecognized" in report[0]


def test_pull_volume_and_gap():
    names = {"v0": "00_D0.mp4", "v1": "01_A.mp4", "s1": "sfx_01_feet.wav"}
    s_feet = seg("s1", 6.3, 1.0)
    s_feet["volume"] = 0.5
    draft = {"tracks": [{"type": "video", "segments": [seg("v0", 0, 3.0), seg("v1", 6.0, 4.0)]},
                        {"type": "audio", "segments": [s_feet]}]}
    new, report = dl.pull(CUT, draft, names, full={"v1": 4.0})
    text = "\n".join(report)
    assert "gap of 3.00s between D0 and A" in text
    assert new["shots"][1]["sfx"] == [{"name": "feet", "at": 0.3, "db": -14.0}] and "volume -8 → -14.0 dB" in text
    assert "trimmed A" not in text  # 整段照用（素材全長 4.0）不算修剪


def test_concat_as_draft():
    tl = {"media": [{"id": "m1", "duration": 4.0}],
          "timeline": {"clips": [{"id": "c1", "kind": "video", "name": "01_A.mp4", "media": "m1", "start": 3.0, "duration": 4.0,
                                  "sourceStart": 0.0, "track": "T3"},
                                 {"id": "c2", "kind": "text", "text": "謝謝。", "start": 3.2, "duration": 1.0, "track": "T4"},
                                 {"id": "c3", "kind": "audio", "name": "sfx_01_feet.wav", "start": 3.3, "duration": 1.0,
                                  "sourceStart": 0.0, "volume": 0.5, "track": "t1"}]}}
    draft, names, full = dl.concat_as_draft(tl)
    assert names == {"c1": "01_A.mp4", "c2": "謝謝。", "c3": "sfx_01_feet.wav"} and full == {"c1": 4.0}
    kinds = sorted(t["type"] for t in draft["tracks"])
    assert kinds == ["audio", "text", "video"]
    audio = next(t for t in draft["tracks"] if t["type"] == "audio")["segments"][0]
    assert audio["volume"] == 0.5 and audio["target_timerange"]["start"] == 3_300_000


# ---- shot_filter：限時 punch／delogo ----
import subprocess  # noqa: E402

import pytest  # noqa: E402


def render(tmp_path, shot):
    """2 秒灰底、右上一塊白（假燒字），套 shot_filter 後回傳 0.2 秒與 1.7 秒兩格的 PIL 灰階圖。"""
    from PIL import Image
    src, out = tmp_path / "src.mp4", tmp_path / "out.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=gray:s=1920x1080:r=30:d=2",
                    "-vf", "drawbox=x=1500:y=100:w=300:h=120:color=white:t=fill", "-pix_fmt", "yuv420p", str(src)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-filter_complex", dl.shot_filter(shot), "-map", "[v]",
                    "-pix_fmt", "yuv420p", str(out)], check=True)
    frames = []
    for t in (0.2, 1.7):
        f = tmp_path / f"f{t}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(out), "-frames:v", "1", str(f)], check=True)
        frames.append(Image.open(f).convert("L"))
    return frames


def white_in_box(img):
    return img.crop((1550, 130, 1750, 190)).getextrema()[1] > 200


def test_shot_filter_plain_shot_keeps_old_chain():
    f = dl.shot_filter({"id": "A", "dur": 4, "zoom": 1.2})
    assert f == "[0:v]setpts=PTS/1.0,scale=2304:1296,crop=1920:1080,fps=30,setsar=1[b0];[b0]null[v]"


def test_delogo_only_inside_its_window(tmp_path):
    early, late = render(tmp_path, {"id": "A", "dur": 2, "delogo": [{"box": [1480, 80, 340, 160], "from": 1, "to": 2}]})
    assert white_in_box(early) and not white_in_box(late)


def test_punch_pushes_corner_text_out_only_inside_window(tmp_path):
    early, late = render(tmp_path, {"id": "A", "dur": 2, "punch": [{"zoom": 1.5, "cx": 0.4, "cy": 0.6, "from": 1}]})
    assert white_in_box(early) and late.getextrema()[1] < 200     # 放大後整格都沒有白塊


@pytest.mark.parametrize("patch,where", [
    ({"delogo": [{"box": [0, 10, 100, 100]}]}, "delogo 0"),            # 貼邊，ffmpeg 會拒
    ({"delogo": [{"box": [10, 10, 100, 100], "from": 3, "to": 5}]}, "delogo 0"),
    ({"punch": [{"zoom": 1.0}]}, "punch 0"),
    ({"punch": [{"zoom": 1.5, "from": 2, "to": 1}]}, "punch 0"),
])
def test_shot_filter_rejects_bad_fields(patch, where):
    with pytest.raises(ValueError, match=where):
        dl.shot_filter({"id": "A", "dur": 4, **patch})


# ---- 新欄位：subs／pics／scene／title／fps／lang ----
def base_cfg(**kw):
    cfg = {"name": "t", "shots": [
        {"id": "A", "src": "a.mp4", "dur": 4.0, "scene": "s1", "speaker": "阿明"},
        {"id": "B", "src": "b.mp4", "dur": 3.0, "scene": "s1"},
        {"id": "C", "src": "c.mp4", "dur": 2.0, "scene": "s2"},
    ], "scenes": {"s1": {"bed": "auto", "db": -33}, "s2": {"bed": "bed.wav"}}}
    cfg.update(kw)
    return cfg


def shot_patch(patch, i=0):
    c = base_cfg()
    c["shots"][i].update(patch)
    return c


def test_units_counts_cjk_chars_or_english_words():
    assert dl.units("阿明，下來。") == 4
    assert dl.units("Can you wait? Three more minutes.") == 6
    assert dl.units("You're $400, ok") == 3
    assert dl.units("OK 好") == 1   # 有中日韓字就只數那些字


def test_line_status_english_counts_words():
    words = [{"word": " Call", "start": 0.1, "end": 0.4}, {"word": " me,", "start": 0.4, "end": 0.6}]
    st = dl.line_status("Call me, we'll talk.", words, 0.65)
    assert st["want"] == 4 and st["got"] == 2 and st["truncated"]


def test_subs_of_both_forms():
    assert dl.subs_of({"sub": {"text": "x", "from": 0, "to": 1}}) == [{"text": "x", "from": 0, "to": 1}]
    two = [{"text": "a", "from": 0, "to": 1}, {"text": "b", "from": 1.5, "to": 2}]
    assert dl.subs_of({"subs": two}) == two
    assert dl.subs_of({}) == []


def test_subtitles_with_multiple_subs():
    shots = [{"id": "A", "dur": 2.0}, {"id": "B", "dur": 3.0, "subs": [{"text": "a", "from": 0.1, "to": 1.0},
                                                                      {"text": "b", "from": 1.5, "to": 3.5}]}]
    assert dl.subtitles(shots) == [(2.1, 3.0, "a"), (3.5, 2.0 + 2.98, "b")]


def test_pics_of_fills_defaults():
    s = {"pics": [{"src": "x.mp4", "dur": 1.5}, {"src": "y.mp4", "in": 2, "dur": 0.5, "hflip": True, "crop": [960, 540, 0, 0]}]}
    assert dl.pics_of(s) == [{"src": "x.mp4", "in": 0.0, "dur": 1.5, "zoom": 1.0},
                             {"src": "y.mp4", "in": 2.0, "dur": 0.5, "zoom": 1.0, "hflip": True, "crop": [960, 540, 0, 0]}]
    assert dl.pics_of({"src": "a.mp4"}) == []


def test_frame_counts_do_not_accumulate_rounding():
    counts = dl.frame_counts([7.3, 7.3, 7.3, 7.3], 24)   # 一支 175.2 格：各自取整會每支多算或少算
    assert sum(counts) == round(29.2 * 24)
    assert dl.frame_counts([3.1, 2.6, 1.0], 24, start=13.3) == [75, 62, 24]   # 319→394→456→480
    assert sum(dl.frame_counts([3.1, 2.6, 1.0], 24, start=13.3)) == round(20.0 * 24) - round(13.3 * 24)


def test_scene_spans_and_non_contiguous_scene():
    shots = base_cfg()["shots"]
    assert dl.scene_spans(shots) == {"s1": (0.0, 7.0), "s2": (7.0, 9.0)}
    assert dl.scene_spans(shots, [4.1, 3.0, 2.0])["s2"] == (7.1, 9.1)
    shots.append({"id": "D", "src": "d.mp4", "dur": 1.0, "scene": "s1"})
    with pytest.raises(ValueError, match='D: the shots of scene "s1" are not consecutive'):
        dl.scene_spans(shots)


def test_check_cfg_accepts_valid_config():
    dl.check_cfg(base_cfg(fps=24, lang="en", dialogue={"stem": "vocals", "db": -18}, music={"file": "m.wav", "stop_at": "C"}))
    dl.check_cfg(shot_patch({"pics": [{"src": "x.mp4", "dur": 1.5}, {"src": "a.mp4", "in": 1.5, "dur": 2.5}],
                             "title": {"lines": [{"text": "T", "size": 60, "y": 100}], "from": 0.8, "to": 3.2},
                             "subs": [{"text": "a", "from": 0.1, "to": 9}]}))   # to 超過鏡長會被截，不算錯
    dl.check_cfg(shot_patch({"scene": "s2"}, 1))   # A＝s1、B＝s2、C＝s2：各自連續


@pytest.mark.parametrize("cfg,msg", [
    (base_cfg(fps=0), "fps"),
    (base_cfg(lang="jp"), "lang"),
    (base_cfg(dialogue={"stem": "drums"}), "stem"),
    (base_cfg(music={"file": "m.wav", "stop_at": "Z"}), "stop_at"),
    (shot_patch({"pics": [{"src": "x.mp4", "dur": 1.0}, {"src": "y.mp4", "dur": 2.0}]}), "A: the pics' dur adds up to"),
    (shot_patch({"speed": 1.5, "pics": [{"src": "x.mp4", "dur": 4.0}]}), "A: a shot with pics cannot set speed"),
    (shot_patch({"speed": 3}), "A: speed"),
    (shot_patch({"title": {"lines": [{"text": "T", "size": 60, "y": 100}], "from": 1, "to": 5}}), "A title"),
    (shot_patch({"title": {"lines": [], "from": 0, "to": 1}}), "A title"),
    (shot_patch({"card": {"lines": [{"text": "x", "size": 60, "y": 10}]}}), "A: needs exactly one of card and src"),
    (shot_patch({"scene": "nope"}, 2), 'C: scene "nope"'),
    (shot_patch({"scene": "s2"}, 0), 'C: the shots of scene "s2" are not consecutive'),   # A＝s2、B＝s1、C＝s2
    (shot_patch({"subs": [{"text": "a", "from": 2, "to": 1}]}), "A subtitle 0"),
    (shot_patch({"crop": [0, 10, 0, 0]}), "A: crop"),
])
def test_check_cfg_rejects(cfg, msg):
    with pytest.raises(ValueError, match=msg):
        dl.check_cfg(cfg)


def test_shot_filter_hflip_crop_and_custom_labels():
    f = dl.shot_filter({"id": "A", "dur": 2, "hflip": True, "crop": [1280, 720, 520, 40]}, fps=24, inp="1:v", out="s1", tag="q1")
    assert f == ("[1:v]hflip,crop=1280:720:520:40,setpts=PTS/1.0,scale=1920:1080,crop=1920:1080,fps=24,setsar=1[q1b0];"
                 "[q1b0]null[s1]")


def test_pull_keeps_subs_form():
    cut = {"name": "t", "shots": [{"id": "A", "src": "a.mp4", "in": 0, "dur": 4.0, "speaker": "阿明",
                                   "subs": [{"text": "一", "from": 0.2, "to": 1.0}, {"text": "二", "from": 2.0, "to": 3.0}]},
                                  {"id": "B", "src": "b.mp4", "in": 0, "dur": 2.0, "sub": {"text": "三", "from": 0.1, "to": 1.0}}]}
    names = {"v0": "00_A.mp4", "v1": "01_B.mp4", "t1": "一", "t2": "二", "t3": "三"}
    draft = {"tracks": [{"type": "video", "segments": [seg("v0", 0, 4.0), seg("v1", 4.0, 2.0)]},
                        {"type": "text", "segments": [seg("t1", 0.3, 0.8), seg("t2", 2.5, 1.0), seg("t3", 4.2, 0.5)]}]}
    new, report = dl.pull(cut, draft, names)
    a, b = new["shots"]
    assert a["subs"] == [{"text": "一", "from": 0.3, "to": 1.1}, {"text": "二", "from": 2.5, "to": 3.5}] and "sub" not in a
    assert b["sub"] == {"text": "三", "from": 0.2, "to": 0.7} and "subs" not in b
