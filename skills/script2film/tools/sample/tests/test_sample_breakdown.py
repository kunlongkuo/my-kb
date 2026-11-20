"""breakdown.py 量測：假逐字稿驗說話量測的算術，ffmpeg 現場生小片驗換畫面與沒聲音、全靜音的情況。"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import breakdown as bd  # noqa: E402


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True)


def words(steps, text="字"):
    """第一個字在 0 秒，之後每個字的開始時間差依 steps。"""
    t, ws = 0.0, [{"word": text, "start": 0.0, "end": 0.1}]
    for d in steps:
        t += d
        ws.append({"word": text, "start": round(t, 3), "end": round(t + 0.1, 3)})
    return {"segments": [{"words": ws}]}


def colors(tmp, durs, name="c.mp4", audio=None):
    """依 durs 每段換一個顏色的片。audio：None 沒聲音流、"silent" 全靜音、"noise" 粉紅噪音。"""
    cols = ["red", "blue", "green", "white", "yellow", "purple"]
    ins = sum((["-f", "lavfi", "-i", f"color=c={cols[i % 6]}:s=320x240:r=30:d={d}"] for i, d in enumerate(durs)), [])
    n, total = len(durs), sum(durs)
    a = {"silent": "anullsrc=r=48000:cl=mono", "noise": "anoisesrc=c=pink:a=0.2"}.get(audio)
    extra = ["-f", "lavfi", "-i", a] if a else []
    out = tmp / name
    ff(*ins, *extra, "-filter_complex", "".join(f"[{i}:v]" for i in range(n)) + f"concat=n={n}:v=1:a=0,format=yuv420p[v]",
       "-map", "[v]", *(["-map", f"{n}:a", "-c:a", "aac"] if a else []), "-t", total, "-c:v", "libx264", out)
    return out


def test_speech_arithmetic():
    s = bd.speech(words([0.2] * 4 + [1.0] + [0.2] * 4), 10.0)
    assert s["chars"] == 10 and s["chars_per_min_film"] == 60.0
    for g in ("0.35", "0.5", "0.65"):
        assert s["by_gap"][g] == {"per_min": 375.0, "share": 0.16}


def test_speech_gap_threshold():
    s = bd.speech(words([0.2] * 4 + [0.4] + [0.2] * 4), 10.0)
    assert s["by_gap"]["0.35"]["share"] == 0.16
    assert s["by_gap"]["0.5"]["share"] == 0.2 and s["by_gap"]["0.65"]["share"] == 0.2


def test_speech_counts_han_only():
    w = {"segments": [{"words": [{"word": "AI", "start": 0, "end": 0.1}, {"word": "時代", "start": 0.2, "end": 0.4},
                                 {"word": "OK", "start": 0.4, "end": 0.5}, {"word": "好", "start": 0.6, "end": 0.7}]}]}
    assert bd.speech(w, 10.0)["chars"] == 3
    assert bd.speech({"segments": [{"words": [{"word": "hello", "start": 0, "end": 1}]}]}, 10.0) is None


def test_cuts_and_shots(tmp_path):
    m = bd.measure(colors(tmp_path, [6] + [3] * 10, audio="noise"))
    assert len(m["cuts"]) == 10 and all(abs(c - e) <= 0.1 for c, e in zip(m["cuts"], range(6, 36, 3)))
    assert m["shots"]["count"] == 11 and abs(m["shots"]["first30_gap"] - 6) <= 0.1
    assert m["lufs"] is not None and m["quiet_db"] is not None and m["speech"] is None


def test_fast_flicker_counts_as_one_change(tmp_path):
    m = bd.measure(colors(tmp_path, [5, 0.1, 0.1, 0.1, 5]))
    assert m["shots"]["raw_cuts"] >= 3 and m["shots"]["count"] == 2
    assert bd.merge([1.0, 1.1, 1.3, 1.65, 4.0]) == [1.0, 1.65, 4.0]


def test_short_film_has_no_first30(tmp_path):
    assert bd.measure(colors(tmp_path, [6, 3, 3]))["shots"]["first30_gap"] is None


def test_no_audio_stream(tmp_path):
    m = bd.measure(colors(tmp_path, [6, 3, 3]), words=words([0.2] * 5))
    assert m["lufs"] is None and m["quiet_db"] is None and m["speech"] is None and m["shots"]["count"] == 3


def test_silent_track(tmp_path):
    m = bd.measure(colors(tmp_path, [6, 3, 3], audio="silent"))
    assert m["lufs"] == -70.0 and m["quiet_db"] is None


def test_sheet_counts_and_width(tmp_path):
    from PIL import Image
    short = bd.sheet(colors(tmp_path, [20, 20], name="s.mp4"), words([0.2] * 5), tmp_path / "s")
    assert len(short) == 1 and Image.open(short[0]).width == 6 * 320
    long = bd.sheet(colors(tmp_path, [50, 50], name="l.mp4"), None, tmp_path / "l")
    assert [p.name for p in long] == ["l_01.jpg", "l_02.jpg"]
    assert Image.open(long[1]).height < Image.open(long[0]).height   # 第二張只有 4 格、一列


def test_sheet_tile_is_the_start_of_its_window(tmp_path):
    """每秒換一個顏色：第 k 格（every 3）要是第 3k 秒的顏色，不是格內後面的秒。"""
    from PIL import Image
    cols = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255), (255, 0, 255)] * 2
    ins = sum((["-f", "lavfi", "-i", f"color=c=0x{r:02x}{g:02x}{b:02x}:s=64x64:r=30:d=1"] for r, g, b in cols), [])
    out = tmp_path / "sec.mp4"
    ff(*ins, "-filter_complex", "".join(f"[{i}:v]" for i in range(12)) + "concat=n=12:v=1:a=0,format=yuv420p",
       "-c:v", "libx264", "-crf", "0", out)
    img = Image.open(bd.sheet(out, None, tmp_path / "sec")[0]).convert("RGB")
    for k in range(4):
        got = img.getpixel((k * 320 + 160, 100))
        assert min(range(6), key=lambda i: sum(abs(a - b) for a, b in zip(got, cols[i]))) == (3 * k) % 6, (k, got)


def test_missing_file_writes_nothing(tmp_path):
    film = colors(tmp_path, [3, 3])
    assert bd.main([str(film), "--vs", str(tmp_path / "nope.mp4"), "--out", str(tmp_path / "o")]) == 2
    assert not (tmp_path / "o" / "measure.json").exists()


def test_audio_only_file_is_refused(tmp_path):
    a = tmp_path / "a.m4a"
    ff("-f", "lavfi", "-i", "anoisesrc=c=pink:a=0.2:d=2", "-c:a", "aac", a)
    assert bd.main([str(a), "--out", str(tmp_path / "o")]) == 2


def test_run_writes_only_into_out(tmp_path, monkeypatch):
    src = tmp_path / "films"
    src.mkdir()
    loud = colors(src, [20, 20], name="loud.mp4", audio="noise")
    mute = colors(src, [20, 20], name="mute.mp4")
    seen = []

    def fake(paths):                                  # 沒聲音的片不會送進轉錄；有聲音的照樣拿到逐字稿
        seen.extend(paths)
        return {p: words([0.2] * 9) for p in paths}
    monkeypatch.setattr(bd, "transcribe", fake)
    before = sorted(x.name for x in src.iterdir())
    out = tmp_path / "out"
    assert bd.main([str(loud), "--vs", str(mute), "--out", str(out)]) == 0
    assert sorted(x.name for x in src.iterdir()) == before
    assert seen == [str(loud)]
    import json
    films = json.loads((out / "measure.json").read_text())["films"]
    assert [f["name"] for f in films] == ["loud", "mute"]
    assert films[0]["speech"]["chars"] == 10 and films[1]["speech"] is None
    md = (out / "measure.md").read_text()
    assert "| 項目 | loud | mute |" in md and (out / "words_loud.json").exists() and (out / "sheet_mute_01.jpg").exists()


def test_no_model_still_measures(tmp_path, monkeypatch):
    monkeypatch.setattr(bd, "transcribe", lambda paths: None)
    out = tmp_path / "out"
    assert bd.main([str(colors(tmp_path, [20, 20], audio="noise")), "--out", str(out)]) == 0
    assert (out / "measure.md").read_text().startswith("沒設 S2F_WHISPER_CPP_MODEL")


def test_duplicate_names():
    assert bd.names(["a/x.mp4", "b/x.mp4", "c/y.mp4"]) == ["x", "x-2", "y"]


def test_every_is_bounded(tmp_path):
    film = colors(tmp_path, [3, 3])
    for bad in ("0", "-3", "61"):
        assert bd.main([str(film), "--out", str(tmp_path / "o"), "--every", bad]) == 2
