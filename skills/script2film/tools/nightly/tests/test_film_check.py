"""film_check.py 基本層：用 ffmpeg 現場生 3 秒 30fps 小片，逐項驗會擋、不會誤擋。"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import film_check as fc  # noqa: E402


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True)


def film(tmp, name="v.mp4", vdur=3.0, adur=3.0, black=None):
    """灰底會動的畫面＋-14 LUFS 左右的粉紅噪音。black=(開始, 長度)：那段換成全黑。"""
    out = tmp / name
    vf = "format=yuv420p"
    if black:
        s, d = black
        vf = f"drawbox=x=0:y=0:w=iw:h=ih:color=black:t=fill:enable='between(t,{s},{s + d - 0.001})',{vf}"
    ff("-f", "lavfi", "-i", f"testsrc=s=320x240:r=30:d={vdur}", "-f", "lavfi", "-i", f"anoisesrc=c=pink:a=0.25:d={adur + 1}",
       "-vf", vf, "-af", f"loudnorm=I=-14:TP=-2,aresample=48000,atrim=duration={adur}", "-ar", "48000", "-c:v", "libx264", "-c:a", "aac", str(out))
    return out


def codes(r, ok=None):
    return {x["code"] for x in r["items"] if ok is None or x["ok"] is ok}


def run(mp4):
    return fc.basic(str(mp4), skip=("loudness", "peak"))   # 3 秒噪音的整體響度不穩，響度另有一個案例


def test_normal_film_passes(tmp_path):
    r = run(film(tmp_path))
    assert r["ok"], r["items"]
    assert {"av_len", "last_frame", "black_mid"} <= codes(r, True)
    assert r["listed"] and r["listed"][0]["code"] == "stale"   # 沒有指紋檔：列「無紀錄」
    assert r["sha256"] == fc.sha256(tmp_path / "v.mp4")


def test_video_cut_short_fails_av_len(tmp_path):
    r = run(film(tmp_path, vdur=2.0, adur=3.0))
    assert "av_len" in codes(r, False)


def test_two_frames_of_extra_audio_passes(tmp_path):
    r = run(film(tmp_path, vdur=3.0, adur=3.0 + 2 / 30))
    assert "av_len" in codes(r, True)


def test_black_frame_mid_film_fails(tmp_path):
    r = run(film(tmp_path, black=(1.5, 1 / 30)))
    assert "black_mid" in codes(r, False)


def test_black_frame_in_last_second_not_at_end_still_fails(tmp_path):
    r = run(film(tmp_path, black=(2.5, 1 / 30)))
    assert "black_mid" in codes(r, False)
    assert not [x for x in r["listed"] if x["code"] == "black_tail"]


def test_black_tail_is_listed_not_blocking(tmp_path):
    r = run(film(tmp_path, black=(2.5, 0.6)))
    assert "black_mid" in codes(r, True)
    assert [x for x in r["listed"] if x["code"] == "black_tail"]


def test_stale_input_fails_and_rerun_does_not_touch_fingerprint(tmp_path):
    mp4 = film(tmp_path)
    src = tmp_path / "beats.json"
    src.write_text("{}")
    inputs = fc.record_paths(mp4)[1]
    inputs.write_text(json.dumps({"base": str(tmp_path), "files": {"beats.json": fc.sha256(src)}}))
    assert "stale" in codes(run(mp4), True)
    src.write_text("{ }")
    before = inputs.read_bytes()
    assert "stale" in codes(run(mp4), False)
    assert fc.main([str(mp4)]) == 1
    assert inputs.read_bytes() == before
    assert "stale" in codes(run(mp4), False)


def test_loudness_and_peak(tmp_path):
    """1 kHz 正弦（ffmpeg sine 預設振幅 1/8，再乘 0.1）：實測 -41.1 LUFS、峰值 -37.6 dBTP，每次都一樣，不靠隨機噪音。"""
    mp4 = tmp_path / "tone.mp4"
    ff("-f", "lavfi", "-i", "testsrc=s=320x240:r=30:d=6", "-f", "lavfi", "-i", "sine=f=1000:d=6,volume=0.1",
       "-ar", "48000", "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k", str(mp4))
    std = {**fc.DEFAULT, "lufs": -41.0, "lufs_tol": 1.0}
    r = fc.basic(str(mp4), standard=std)
    assert {"loudness", "peak"} <= codes(r, True), r["items"]
    assert "loudness" in codes(fc.basic(str(mp4)), False)                                   # 預設 -14
    assert "peak" in codes(fc.basic(str(mp4), standard={**std, "max_tp": -40.0}), False)


def test_series_standard(tmp_path):
    ep = tmp_path / "series" / "ep1"
    ep.mkdir(parents=True)
    assert fc.load_standard(ep) == fc.DEFAULT
    (tmp_path / "series/film_check.json").write_text(json.dumps({"lufs": -16}))
    assert fc.load_standard(ep)["lufs"] == -16 and fc.load_standard(ep)["max_tp"] == -1.0
    (tmp_path / "series/film_check.json").write_text(json.dumps({"skip": [{"item": "bogus", "why": "x"}]}))
    with pytest.raises(fc.ConfigError):
        fc.load_standard(ep)
    (tmp_path / "series/film_check.json").write_text(json.dumps({"skip": [{"item": "black_mid", "why": " "}]}))
    with pytest.raises(fc.ConfigError):
        fc.load_standard(ep)


def test_cli_bad_series_config_exits_2(tmp_path):
    ep = tmp_path / "series" / "ep1"
    ep.mkdir(parents=True)
    mp4 = film(ep)
    (tmp_path / "series/film_check.json").write_text(json.dumps({"skip": [{"item": "bogus", "why": "x"}]}))
    assert fc.main([str(mp4)]) == 2


def test_series_skip_drops_item(tmp_path):
    r = fc.basic(str(film(tmp_path, black=(1.5, 1 / 30))),
                 standard={**fc.DEFAULT, "skip": [{"item": "black_mid", "why": "測試"}]})
    assert "black_mid" not in codes(r) and "black_mid" in r["skipped"]



def test_sfx_present_missing_and_shifted(tmp_path):
    """音效床＝隨機位置的短促噪音；成片＝固定旁白（正弦）＋音效床。拿掉音效床或錯開 0.2 秒都要不過。"""
    bed = tmp_path / "sfx_bed.wav"
    ff("-f", "lavfi", "-i", "anoisesrc=c=white:a=0.5:d=8:seed=3", "-af",
       "volume='if(lt(mod(t,1.3),0.15),1,0)':eval=frame", "-ar", "48000", str(bed))

    def mix(name, bed_filter):
        out = tmp_path / name
        ff("-f", "lavfi", "-i", "testsrc=s=320x240:r=30:d=8", "-f", "lavfi", "-i", "sine=f=220:d=8", "-i", bed,
           "-filter_complex", f"[2]{bed_filter}[b];[1][b]amix=inputs=2:normalize=0[a]", "-map", "0:v", "-map", "[a]",
           "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k", str(out))
        return out
    ok = fc.basic(str(mix("ok.mp4", "volume=0.3")), sfx_bed=bed, skip=("loudness", "peak"))
    assert "sfx" in codes(ok, True), ok["items"]
    gone = fc.basic(str(mix("gone.mp4", "volume=0")), sfx_bed=bed, skip=("loudness", "peak"))
    assert "sfx" in codes(gone, False)
    late = fc.basic(str(mix("late.mp4", "adelay=200,volume=0.3")), sfx_bed=bed, skip=("loudness", "peak"))
    assert "sfx" in codes(late, False)
    none = fc.basic(str(mix("x.mp4", "volume=0.3")), skip=("loudness", "peak"))   # 沒給音效床：不量
    assert "sfx" not in codes(none)


def test_missing_input_is_noted_not_blocking(tmp_path):
    mp4 = film(tmp_path)
    src = tmp_path / "layers.json"
    src.write_text("{}")
    fc.record_paths(mp4)[1].write_text(json.dumps({"base": str(tmp_path), "files": {"layers.json": fc.sha256(src)}}))
    src.unlink()
    r = run(mp4)
    st = [x for x in r["items"] if x["code"] == "stale"][0]
    assert st["ok"] and "missing" in st["value"] and st["notes"]


def test_tail_black_up_to_two_seconds_is_listed(tmp_path):
    r = run(film(tmp_path, vdur=4.0, adur=4.0, black=(2.5, 1.5)))
    assert "black_mid" in codes(r, True) and [x for x in r["listed"] if x["code"] == "black_tail"]
    r = run(film(tmp_path, name="w.mp4", vdur=5.0, adur=5.0, black=(2.5, 2.5)))   # 超過 2 秒：算片中黑
    assert "black_mid" in codes(r, False)


def test_quiet_is_listed_and_flags_sound_with_no_pauses(tmp_path):
    """噪音一路沒停：最安靜 5% 也很大聲，列出提醒；中間有一半靜音的片不提醒。都不擋。"""
    loud = fc.basic(str(film(tmp_path)), skip=("loudness", "peak"))
    q = [x for x in loud["listed"] if x["code"] == "quiet"][0]
    assert loud["ok"] and "music may be covering" in q["value"]
    gaps = tmp_path / "gaps.mp4"
    ff("-i", film(tmp_path, name="src.mp4"), "-af", "volume=enable='between(mod(t,1),0.5,1)':volume=0", "-c:v", "copy", gaps)
    q = [x for x in fc.basic(str(gaps), skip=("loudness", "peak"))["listed"] if x["code"] == "quiet"][0]
    assert "music may be covering" not in q["value"]


def test_series_quiet_max(tmp_path):
    ep = tmp_path / "s" / "001"
    ep.mkdir(parents=True)
    (ep.parent / "film_check.json").write_text(json.dumps({"quiet_max": 0}))
    q = [x for x in fc.basic(str(film(tmp_path)), standard=fc.load_standard(ep), skip=("loudness", "peak"))["listed"]
         if x["code"] == "quiet"][0]
    assert "music may be covering" not in q["value"]


def test_first30_leaves_out_the_cover(tmp_path):
    """前 12 秒同一個畫面、之後每 3 秒換色：直接量 12 秒；12 秒那段是封面拍就只剩 3 秒。"""
    cols = ["red"] + ["blue", "green", "white", "yellow", "purple", "orange"]
    durs = [12] + [3] * 6
    out = tmp_path / "c.mp4"
    ins = sum((["-f", "lavfi", "-i", f"color=c={c}:s=320x240:r=30:d={d}"] for c, d in zip(cols, durs)), [])
    ff(*ins, "-filter_complex", "".join(f"[{i}:v]" for i in range(len(cols))) + f"concat=n={len(cols)}:v=1:a=0,format=yuv420p",
       "-c:v", "libx264", out)
    assert abs(fc.first30(out) - 12) < 0.2
    ep = tmp_path / "ep"
    ep.mkdir()
    (ep / "doc.json").write_text(json.dumps({"beats": [{"id": "B1", "scene": "cover"}, {"id": "B2", "scene": "photo"}]}))
    (ep / "beats.json").write_text(json.dumps({"beats": [{"id": "B1", "start": 0.0, "end": 12.0}, {"id": "B2", "start": 12.0, "end": 30.0}]}))
    assert fc.cover_spans(ep) == [(0.0, 12.0)]
    assert abs(fc.first30(out, fc.cover_spans(ep)) - 3) < 0.2
    assert fc.cover_spans(tmp_path) == []   # 沒有 doc.json：不扣


def test_first30_is_listed_not_blocking(tmp_path):
    r = run(film(tmp_path))
    assert r["ok"] and [x for x in r["listed"] if x["code"] == "first30"]


def test_silent_track_does_not_crash(tmp_path):
    """有音軌但全是靜音：ebur128 的峰值印 -inf（響度印下限 -70），峰值當作量不到，不拋例外；響度不過。"""
    out = tmp_path / "s.mp4"
    ff("-f", "lavfi", "-i", "testsrc=s=320x240:r=30:d=3", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", "3",
       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", out)
    _, lufs, tp = fc.black_and_loudness(str(out))
    assert lufs == -70.0 and tp is None
    assert {"loudness", "peak"} <= codes(fc.basic(str(out)), False)
