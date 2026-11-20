import subprocess

from PIL import Image

from ve_clipcheck import check, strips


def clip(path, *colors):
    """一秒一色的小片段：兩色以上就有硬切點。"""
    src = sum((["-f", "lavfi", "-i", f"color={c}:s=160x90:d=1:r=10"] for c in colors), [])
    cat = "".join(f"[{i}:v]" for i in range(len(colors))) + f"concat=n={len(colors)}:v=1[v]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *src, "-filter_complex", cat, "-map", "[v]", "-pix_fmt", "yuv420p", str(path)],
                   check=True)


def test_single_shot_passes(tmp_path):
    clip(tmp_path / "shot1.mp4", "gray", "gray")
    assert check(tmp_path) == 0


def test_cut_flagged_and_early_cut_named(tmp_path):
    clip(tmp_path / "shot1.mp4", "white", "black", "black", "black")   # 1 s 白之後換黑：開頭先放參考圖
    clip(tmp_path / "shot2.mp4", "black", "black", "black", "white")   # 3 s 換：片中換鏡
    assert check(tmp_path) == 2
    text = (tmp_path / "clipcheck.json").read_text(encoding="utf-8")
    assert "reference image shown first" in text and "cut inside the clip" in text


def test_first_frame_like_previous_shot(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    Image.new("RGB", (160, 90), "white").save(run / "shot1_cand1.jpg")
    Image.new("RGB", (160, 90), "black").save(run / "shot2_cand1.jpg")
    clip(tmp_path / "shot2.mp4", "white", "white")                       # 拿了上一鏡（白）的圖
    assert check(tmp_path, run) == 1
    clip(tmp_path / "shot2.mp4", "black", "black")
    assert check(tmp_path, run) == 0


def test_strips_sheet_is_in_time_order(tmp_path):
    """--strips: one row per clip, frames left to right in time order (red first half, blue second half)."""
    for name in ("a.mp4", "b.mp4"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=red:s=320x180:d=2:r=30", "-f", "lavfi", "-i",
                        "color=c=blue:s=320x180:d=2:r=30", "-filter_complex", "[0][1]concat=n=2:v=1:a=0,format=yuv420p",
                        str(tmp_path / name)], check=True)
    out = strips(tmp_path)
    img = Image.open(out)
    assert img.size == (5 * 384, 2 * (216 + 24))
    for row in (0, 1):
        y = row * 240 + 24 + 100
        left, right = img.getpixel((100, y)), img.getpixel((4 * 384 + 100, y))
        assert left[0] > 150 and left[2] < 100 and right[2] > 150 and right[0] < 100
    assert strips(tmp_path / "nothing-here") is None
