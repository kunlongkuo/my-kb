"""Render a local, silent 16:9 text-board read-through preview from shots.json."""
import json
import math
import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SPEC = HERE / "shots.json"
W, H = 1280, 720
FONT = "C:/Windows/Fonts/msjh.ttc"
FONT_BOLD = "C:/Windows/Fonts/msjhbd.ttc"


def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def wrap(draw, text, face, max_width):
    lines, current = [], ""
    for char in text:
        candidate = current + char
        if current and draw.textbbox((0, 0), candidate, font=face)[2] > max_width:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def render_card(shot, size=(W, H), compact=False):
    w, h = size
    im = Image.new("RGB", size, (17, 25, 34))
    d = ImageDraw.Draw(im)
    pad = max(12, w // 36)
    d.rounded_rectangle((pad, pad, w - pad, h - pad), radius=max(10, pad // 2),
                        fill=(24, 36, 47), outline=(225, 172, 85), width=max(2, w // 500))
    scale = w / W
    sid_size = max(15, int(30 * scale))
    body_size = max(14, int((27 if compact else 34) * scale))
    cap_size = max(14, int((22 if compact else 30) * scale))
    x = pad * 2
    y = pad * 2
    d.text((x, y), f"{shot['id']}   {shot['sec']} 秒", font=font(sid_size, True), fill=(255, 207, 119))
    visual = shot.get("visual_zh", shot.get("panel", ""))
    visual_face = font(body_size)
    max_width = w - 4 * pad
    visual_lines = wrap(d, visual, visual_face, max_width)
    available = int(h * (0.44 if compact else 0.43))
    line_height = int(body_size * 1.45)
    visual_lines = visual_lines[:max(1, available // line_height)]
    visual_y = int(h * 0.29)
    for line in visual_lines:
        d.text((x, visual_y), line, font=visual_face, fill=(238, 241, 238))
        visual_y += line_height
    captions = [line.get("caption", "") for line in shot.get("lines", []) if line.get("caption")]
    cap_text = "　".join(captions) if captions else "（無台詞）"
    cap_face = font(cap_size, True)
    cap_lines = wrap(d, cap_text, cap_face, max_width)
    cap_line_height = int(cap_size * 1.5)
    cap_y = h - pad * 3 - cap_line_height * min(2, len(cap_lines))
    for line in cap_lines[:2]:
        d.text((x, cap_y), line, font=cap_face, fill=(255, 231, 184))
        cap_y += cap_line_height
    return im


def main():
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    shots = spec["shots"]
    thumb_w, thumb_h = 480, 270
    sheet = Image.new("RGB", (thumb_w * 4, thumb_h * 4), (9, 14, 20))
    for index, shot in enumerate(shots):
        sheet.paste(render_card(shot, (thumb_w, thumb_h), compact=True),
                    ((index % 4) * thumb_w, (index // 4) * thumb_h))
    sheet_path = HERE / "分鏡文字稿.png"
    sheet.save(sheet_path)

    total, timeline = 0.0, []
    with tempfile.TemporaryDirectory(prefix="memory_soda_preview_") as temp_dir:
        temp = Path(temp_dir)
        concat = []
        for index, shot in enumerate(shots):
            text_chars = sum(len(re.findall(r"[一-鿿A-Za-z0-9]", line.get("text", "")))
                             for line in shot.get("lines", []))
            read_dur = 0.25 + text_chars / 4.0 + (0.3 if text_chars else 0)
            duration = max(float(shot.get("sec", 2)), read_dur)
            h3_sec = max(3.0, float(shot.get("sec", 0)), text_chars / 3.0 + 2.0) if text_chars else float(shot.get("sec", 2))
            h3_sec = math.ceil(h3_sec * 2) / 2
            timeline.append({"shot": shot["id"], "start": round(total, 2), "dur": round(duration, 2),
                             "table_sec": shot.get("sec"), "chars": text_chars, "h3_sec": h3_sec})
            frame = temp / f"{index:03}.png"
            render_card(shot).save(frame)
            concat.extend([f"file '{frame.as_posix()}'", f"duration {duration:.3f}"])
            total += duration
        concat.append(f"file '{(temp / f'{len(shots) - 1:03}.png').as_posix()}'")
        concat_file = temp / "list.txt"
        concat_file.write_text("\n".join(concat), encoding="utf-8")
        output = HERE / "讀本試映.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-vf", "fps=24,format=yuv420p",
            "-t", f"{total:.3f}", "-c:v", "libx264", "-crf", "23", "-c:a", "aac", "-b:a", "128k",
            "-shortest", "-movflags", "+faststart", str(output)
        ], check=True)
    (HERE / "讀本_timeline.json").write_text(
        json.dumps({"total": round(total, 2), "shots": timeline}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"讀本試映：{output}")
    print(f"文字分鏡：{sheet_path}")
    print(f"總長：{total:.1f} 秒（{total / 60:.1f} 分鐘）")
    print("超過 12 秒的鏡頭：", [x["shot"] for x in timeline if x["dur"] > 12 or x["h3_sec"] > 12])


if __name__ == "__main__":
    main()
