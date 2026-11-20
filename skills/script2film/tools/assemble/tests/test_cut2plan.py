"""cut2plan.py（s2f-1b D1、D2）：素材都用 ffmpeg 在 tmp_path 現場產生，不依賴任何專案資料夾。"""
import json
import os
import re
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "cut2plan.py"

SRT = """1
00:00:00,100 --> 00:00:00,950
第一句

2
00:00:01,100 --> 00:00:01,950
第二句

3
00:00:02,100 --> 00:00:02,950
第三句上行
第三句下行
"""


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def clip(path: Path, rate="30", frames=30):
    ff("-f", "lavfi", "-i", f"color=c=blue:s=320x180:r={rate}", "-frames:v", str(frames), "-bf", "0",
       "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path))


def fmt_dur(path: Path) -> str:
    return subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                          capture_output=True, text=True, check=True).stdout.strip()


def make_project(tmp_path, *, bgm_s=2.0, sub_bg=True, speakers=("阿明", "阿明", "阿明"), sequence=False,
                 clips=None):
    """base/：cut_t.json、tts/lines.json、voice.cleaned/final.srt、bgm/bgm.wav；
    base/cut_t/：.segments/shot1-3.mp4、voice.cleaned/{narr.wav, final.srt}。"""
    base = tmp_path / "ep"
    out = base / "cut_t"
    (out / ".segments").mkdir(parents=True)
    (out / "voice.cleaned").mkdir()
    (base / "voice.cleaned").mkdir()
    (base / "tts").mkdir()
    (base / "bgm").mkdir()
    for i, spec in enumerate(clips or [("30", 30)] * 3, 1):
        clip(out / ".segments" / f"shot{i}.mp4", *spec)
    ff("-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000", "-t", "3", "-ac", "1", "-c:a", "pcm_s16le",
       str(out / "voice.cleaned" / "narr.wav"))
    ff("-f", "lavfi", "-i", "sine=frequency=220:sample_rate=48000", "-t", str(bgm_s), "-ac", "2", "-c:a", "pcm_s16le",
       str(base / "bgm" / "bgm.wav"))
    for d in (out, base):
        (d / "voice.cleaned" / "final.srt").write_text(SRT, encoding="utf-8")
    lines = [{"n": i + 1, "speaker": s, "text": f"第{i + 1}句", "start": i + 0.1, "end": i + 0.9}
             for i, s in enumerate(speakers)]
    (base / "tts" / "lines.json").write_text(json.dumps(lines, ensure_ascii=False), encoding="utf-8")
    cc = {"name": "t", "lines": "tts/lines.json", "audio": "voice.cleaned/narr.wav", "lead_s": 0.0,
          "width": 1920, "height": 1080, "fps": 30,
          "extra_audios": [{"path": "../bgm/bgm.wav", "start_s": 0, "track": "BGM"}]}
    if sub_bg:
        cc["sub_bg"] = {"color": "#000000", "alpha": 0.7}
    cfg = {"clips": "picks", "srt": "voice.cleaned/final.srt", "out": "cut_t", "stepped_fps": 0, "timeline": cc}
    if sequence:
        cfg["sequence"] = [{"voice": [1, 3], "shots": {"shot1": 1}}]
    else:
        cfg["shots"] = {"shot1": 1, "shot2": 2, "shot3": 3}
    path = base / "cut_t.json"
    path.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
    return path, out


def run(cfg):
    dst = cfg.parent / "plan_out.json"
    r = subprocess.run([sys.executable, str(SCRIPT), str(cfg), str(dst)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    return json.loads(dst.read_text(encoding="utf-8"))


def ms(x):
    return round(x * 1000)


@pytest.fixture(scope="module")
def basic(tmp_path_factory):
    cfg, out = make_project(tmp_path_factory.mktemp("basic"))
    return run(cfg), out


def test_01_top_level_keys(basic):
    plan, _ = basic
    assert list(plan) == ["total", "width", "height", "fps", "media", "tracks"]
    assert (plan["width"], plan["height"], plan["fps"]) == (1920, 1080, 30)


def test_02_track_type_order(basic):
    plan, _ = basic
    assert [t["type"] for t in plan["tracks"]] == ["video", "text", "audio", "audio"]


def test_03_video_starts_are_cumulative_durs(basic):
    segs = basic[0]["tracks"][0]["segs"]
    assert [s["name"] for s in segs] == ["shot1.mp4", "shot2.mp4", "shot3.mp4"]
    acc = 0
    for s in segs:
        assert ms(s["start"]) == acc
        acc += ms(s["dur"])
    assert acc == 3000


def test_04_voice_segments(basic):
    segs = basic[0]["tracks"][2]["segs"]
    assert len(segs) == 3
    assert all(re.match(r"^\d+_", s["name"]) for s in segs)
    for a, b in zip(segs, segs[1:]):
        assert ms(a["start"]) + ms(a["dur"]) <= ms(b["start"])


def test_05_volumes(basic):
    plan, _ = basic
    assert {s["vol"] for s in plan["tracks"][2]["segs"]} == {1.4142}
    assert plan["tracks"][3]["segs"][0]["vol"] == 1.0
    assert plan["tracks"][3]["segs"][0]["name"] == "bgm.wav"


def test_06_subtitle_background(basic, tmp_path):
    for s in basic[0]["tracks"][1]["segs"]:
        assert (s["bg"], s["bga"], s["y"]) == ("#000000", 0.7, -0.8)
    cfg, _ = make_project(tmp_path, sub_bg=False)
    for s in run(cfg)["tracks"][1]["segs"]:
        assert (s["bg"], s["bga"], s["y"]) == (None, 1.0, -0.8)


def test_07_text_equals_srt(basic):
    segs = basic[0]["tracks"][1]["segs"]
    assert [s["text"] for s in segs] == ["第一句", "第二句", "第三句上行\n第三句下行"]
    assert [(s["start"], s["end"]) for s in segs] == [(0.1, 0.95), (1.1, 1.95), (2.1, 2.95)]


def test_08_paths_absolute_existing_normalized(basic):
    plan, out = basic
    seg_paths = {s["path"] for t in plan["tracks"] if t["type"] != "text" for s in t["segs"]}
    for p in seg_paths:
        assert os.path.isabs(p) and os.path.exists(p) and ".." not in Path(p).parts, p
    assert {m["path"] for m in plan["media"]} == seg_paths
    bgm = plan["tracks"][3]["segs"][0]["path"]
    assert bgm == os.path.normpath(str(out.parent / "bgm" / "bgm.wav"))


def test_09_sequence_mode_refused(tmp_path):
    cfg, _ = make_project(tmp_path, sequence=True)
    r = subprocess.run([sys.executable, str(SCRIPT), str(cfg), str(tmp_path / "p.json")], capture_output=True, text=True)
    assert r.returncode != 0
    assert "assemble.py" in r.stdout + r.stderr
    assert "Traceback" not in r.stderr


def test_10_rounding_is_ceiling_to_ms(tmp_path):
    cfg, out = make_project(tmp_path, clips=[("30000/1001", 31), ("30", 483), ("30", 30)])
    raw = fmt_dur(out / ".segments" / "shot1.mp4")
    x = Decimal(raw) * 1000
    frac = x - int(x)
    assert frac != 0 and frac < Decimal("0.5"), f"ffprobe format.duration is {raw}, which breaks the test's premise (expected 1.034367)"
    segs = run(cfg)["tracks"][0]["segs"]
    assert segs[0]["dur"] == 1.035, f"ffprobe value {raw}"
    assert segs[1]["start"] == 1.035
    assert fmt_dur(out / ".segments" / "shot2.mp4") == "16.100000"
    assert segs[1]["dur"] == 16.1


def test_11_total_is_max_of_video_and_audio(basic, tmp_path):
    plan, _ = basic  # 配樂 2 秒、畫面 3 秒
    assert plan["total"] == 3.0
    cfg, _ = make_project(tmp_path, bgm_s=4.0)
    plan = run(cfg)
    bgm = plan["tracks"][3]["segs"][0]
    assert plan["total"] == bgm["start"] + bgm["dur"] == 4.0


def test_12_two_speakers_two_tracks_in_first_appearance_order(tmp_path):
    cfg, _ = make_project(tmp_path, speakers=("乙", "甲", "乙"))
    plan = run(cfg)
    assert [t["type"] for t in plan["tracks"]] == ["video", "text", "audio", "audio", "audio"]
    assert [s["name"] for s in plan["tracks"][2]["segs"]] == ["01_乙.wav", "03_乙.wav"]
    assert [s["name"] for s in plan["tracks"][3]["segs"]] == ["02_甲.wav"]
    assert plan["tracks"][4]["segs"][0]["name"] == "bgm.wav"


def test_13_two_line_cue_keeps_newline(basic):
    assert "\n" in basic[0]["tracks"][1]["segs"][2]["text"]


def test_14_audio_rounds_to_nearest_ms_ties_to_even(tmp_path):
    """聲音取最接近的毫秒、一半取偶數；影片向上取整。三支 24 kHz 的 wav：6.853083、3.049917、4.6185 秒。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("cut2plan_under_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for samples, raw, want in [(164474, "6.853083", 6853), (73198, "3.049917", 3050), (110844, "4.618500", 4618)]:
        wav = tmp_path / f"v{samples}.wav"
        ff("-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-af", f"atrim=end_sample={samples}", str(wav))
        got = fmt_dur(wav)
        assert got == raw, f"ffprobe format.duration is {got}, which breaks the test's premise (expected {raw})"
        assert mod.dur_ms(str(wav), up=False) == want
    assert mod.dur_ms(str(tmp_path / "v164474.wav")) == 6854


def test_15_old_key_capcut_gives_same_plan(tmp_path):
    """設定檔只有舊鍵 capcut 時，產出的 plan 與用 timeline 的逐鍵相同（D2 相容讀法）。"""
    cfg, _ = make_project(tmp_path)
    new = run(cfg)
    d = json.loads(cfg.read_text(encoding="utf-8"))
    d["capcut"] = d.pop("timeline")
    cfg.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    old = run(cfg)
    assert list(old) == list(new)
    for k in new:
        assert old[k] == new[k], k


def test_16_no_timeline_block_stops(tmp_path):
    cfg, _ = make_project(tmp_path)
    d = json.loads(cfg.read_text(encoding="utf-8"))
    del d["timeline"]
    cfg.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), str(cfg), str(tmp_path / "p.json")], capture_output=True, text=True)
    assert r.returncode != 0
    assert "timeline" in r.stdout + r.stderr
    assert "Traceback" not in r.stderr
