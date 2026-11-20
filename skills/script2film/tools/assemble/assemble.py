"""VE 片段 → 依字幕句界切窗 →（可選）抽格 → 串成一條畫面軌 → 換進殼（字幕頁、旁白、音效）。

用法：python3 tools/assemble/assemble.py <ve-project.json>
doc 模式由 doc_cut.py 呼叫；之後 doc_cut.py --render 用 doc_common.hyperframes() 把 <out> 渲成 <out>/output.mp4。
設定檔格式見 velib.py。設定檔有 "sequence" 時走段落模式（旁白段＋對白段依序排，見 velib.py 的說明）。
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from velib import (block_bounds, duration, load_config, parse_srt, segment_frames, shift_cues,  # noqa: E402
                   line_boundaries, retime_cues, shot_windows, silences, speech_bounds, speech_span, speech_spans,
                   stretch_factor, timeline_cfg)

USAGE = """VE clips -> windows cut at subtitle line boundaries -> (optional) stepped frames -> one video track -> swapped into
the shell (subtitle page, narration, sound effects).

usage: python3 tools/assemble/assemble.py <ve-project.json>
In doc mode doc_cut.py calls it; doc_cut.py --render then renders <out> to <out>/output.mp4 with doc_common.hyperframes().
Config format: see velib.py. A config with "sequence" uses block mode (narration and dialogue blocks in order; see velib.py).
"""
FPS = 24          # 畫面軌的格率（抽格後回到 24）
SR = 48000        # 混音的取樣率；SR / FPS = 每格 2000 個取樣，段落邊界對齊格


def run(cmd):
    subprocess.run(cmd, check=True)


def has_audio(path: Path) -> bool:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_type",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return "audio" in r.stdout


def render_segment(src: Path, frames: int, need: float, dst: Path, stepped: int, always_pad: bool = False,
                   max_stretch: float = 1.0) -> tuple[float, float]:
    """一段畫面：片段比需要的短就先放慢（最多 max_stretch 倍），還不夠再凍結最後一格補足；抽格；以格數切到 frames 格。
    回傳（放慢倍數, 補凍結的秒數）。always_pad：保留給呼叫端相容（現在一律墊 0.25s）。"""
    have = duration(src)
    k = stretch_factor(have, need, max_stretch)
    pad = max(0.0, need - have * k)  # 多補 0.25s，最後由 trim 切掉
    vf = f"setpts={k}*(PTS-STARTPTS)," if k > 1 else ""
    # 一律墊 0.25s 再以格數切：片長剛好等於需要時，抽格會把尾端往下湊整而少一格（一支短劇的實測）
    vf += f"tpad=stop_mode=clone:stop_duration={pad + 0.25:.3f},"
    vf += "setpts=PTS-STARTPTS,"
    if stepped:
        vf += f"fps={stepped},"
    vf += (f"fps={FPS},trim=end_frame={frames},setpts=PTS-STARTPTS,"
           "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", vf, "-an", "-c:v", "libx264",
         "-crf", "18", "-pix_fmt", "yuv420p", str(dst)])
    return k, pad


def audio_piece(src: Path | None, start_sample: int, samples: int, dst: Path, gain: float = 1.0):
    """src 從 start_sample 起取 samples 個取樣（48k 單聲道 PCM），不足補靜音；src=None 產生靜音。"""
    if src is None or not has_audio(src):
        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=mono", "-af",
             f"atrim=end_sample={samples}", "-c:a", "pcm_s16le", str(dst)])
        return
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af",
         f"aresample={SR},pan=mono|c0=c0,atrim=start_sample={start_sample},asetpts=PTS-STARTPTS,"
         f"apad=whole_len={samples},atrim=end_sample={samples},volume={gain}",
         "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", str(dst)])


def mix(a: Path, b: Path, dst: Path):
    run(["ffmpeg", "-v", "error", "-y", "-i", str(a), "-i", str(b), "-filter_complex",
         "amix=inputs=2:duration=first:normalize=0", "-c:a", "pcm_s16le", str(dst)])


def concat(files: list[Path], listfile: Path, dst: Path, codec: list[str]):
    listfile.write_text("".join(f"file '{f.name}'\n" for f in files))
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile), *codec, str(dst)])


def copy_shell(shell: dict, base: Path, out: Path):
    shell_dir = base / shell["dir"]
    for x in shell["copy"]:
        (shutil.copytree if (shell_dir / x).is_dir() else shutil.copy)(shell_dir / x, out / x)


def swap_video(index: Path, shell: dict) -> str:
    s, old = index.read_text(encoding="utf-8"), f'src="{shell["video_src"]}"'
    if s.count(old) != 1:
        sys.exit(f"✗ {old} appears {s.count(old)} times in index.html, expected 1")
    return s.replace(old, 'src="ve_visual.mp4"')


def legacy(cfg: dict, base: Path, out: Path):
    clips, shell = base / cfg["clips"], cfg["shell"]
    windows = shot_windows(parse_srt((base / cfg["srt"]).read_text(encoding="utf-8")), cfg["shots"])
    missing = [n for n, _, _ in windows if not (clips / f"{n}.mp4").exists()]
    if missing:
        sys.exit(f"✗ {clips} is missing clips: {', '.join(missing)}")
    out.mkdir(parents=True)
    copy_shell(shell, base, out)
    seg = out / ".segments"
    seg.mkdir()
    stepped = int(cfg.get("stepped_fps", 8))
    report = []
    for name, a, b in windows:
        src = clips / f"{name}.mp4"
        need, have = round(b - a, 3), duration(src)
        k, pad = render_segment(src, segment_frames(a, b), need, seg / f"{name}.mp4", stepped,
                                max_stretch=float(cfg.get("max_stretch", 1.0)))
        report.append(f"{name} {a:6.2f}-{b:6.2f} window {need:5.2f}s clip {have:5.2f}s" + (f" slowed {k:.2f}x" if k > 1 else "")
                      + (f" freeze-padded {pad:.2f}s" if pad else ""))
    concat([seg / f"{n}.mp4" for n, _, _ in windows], seg / "list.txt", out / "ve_visual.mp4", ["-c", "copy"])
    (out / "index.html").write_text(swap_video(out / "index.html", shell), encoding="utf-8")
    print("\n".join(report))
    print(f"video track {duration(out / 've_visual.mp4'):.2f}s (last subtitle line ends at {windows[-1][2]:.2f}s) → {out}")


def patch_shell(s: str, cues: list[tuple[float, float, str]], total: float, last_line_end: float) -> str:
    """殼裡寫死的時間：字幕時間表 CUES、整片與音軌長度、配音檔位置、字幕淡出點。每一項都要剛好命中一處，否則停下。"""
    m = re.search(r'<video[^>]*src="ve_visual\.mp4"[^>]*data-duration="([0-9.]+)"', s)
    if not m:
        sys.exit("✗ no data-duration for ve_visual.mp4 in the shell")
    old_total = m.group(1)
    hits = s.count(f'data-duration="{old_total}"')
    if hits < 2:
        sys.exit(f"✗ data-duration=\"{old_total}\" appears only {hits} time(s) in the shell (expected the film container + the video track)")
    s = s.replace(f'data-duration="{old_total}"', f'data-duration="{total:.3f}"')
    s, n = re.subn(r'(<audio id="voice"[^>]*?)src="[^"]*"(\s+data-start="0"\s+data-duration=")[0-9.]+"',
                   rf'\1src="mix.m4a"\g<2>{total:.3f}"', s)
    if n != 1:
        sys.exit("✗ no narration track <audio id=\"voice\"> in the shell")
    m = re.search(r"const CUES = \[\s*\[[0-9.]+,\s*\"(.*?)\"\]", s, re.S)
    if not m or ">" not in m.group(1):
        sys.exit("✗ no subtitle timetable CUES in the shell")
    first = m.group(1)
    prefix, suffix = first[:first.index(">") + 1], first[first.rindex("<"):]
    rows, prev_end = [], None
    for a, b, text in cues:
        if prev_end is not None and a - prev_end > 0.05:
            rows.append(f'    [{prev_end:g}, ""]')
        rows.append(f'    [{a:g}, "{prefix}{json.dumps(text, ensure_ascii=False)[1:-1]}{suffix}"]')
        prev_end = b
    rows.append(f'    [{last_line_end:g}, ""]')
    s, n = re.subn(r"const CUES = \[.*?\n  \];", "const CUES = [\n" + ",\n".join(rows) + "\n  ];", s, count=1, flags=re.S)
    if n != 1:
        sys.exit("✗ could not replace the subtitle timetable CUES")
    s, n = re.subn(r'(main\.to\("\.subtitles-panel",[^)]*\},\s*)[0-9.]+(\);)', rf"\g<1>{last_line_end - 0.1:.2f}\2", s)
    if n != 1:
        sys.exit("✗ no subtitle fade-out point main.to(\".subtitles-panel\" …) in the shell")
    return s


def sequence(cfg: dict, base: Path, out: Path):
    """旁白段：Qwen 配音截一段，段內各鏡照字幕句切窗（同舊模式）；對白段：整支片，畫面和聲音都用它自己的。"""
    clips, shell = base / cfg["clips"], cfg["shell"]
    cues = parse_srt((base / cfg["srt"]).read_text(encoding="utf-8"))
    stepped = int(cfg.get("stepped_fps", 8))
    gain = float(cfg.get("ambience_gain", 1.0))
    max_stretch = float(cfg.get("max_stretch", 1.0))
    for i, blk in enumerate(cfg["sequence"]):
        if ("voice" in blk) == ("clip" in blk):
            sys.exit(f"✗ sequence block {i + 1} needs exactly one of voice or clip")
        if "clip" in blk and not (base / blk["clip"]).exists():
            sys.exit(f"✗ sequence block {i + 1}: clip does not exist: {blk['clip']}")
        if "voice" in blk:
            missing = [n for n in blk["shots"] if not (clips / f"{n}.mp4").exists()]
            if missing:
                sys.exit(f"✗ {clips} is missing clips: {', '.join(missing)}")
    out.mkdir(parents=True)
    copy_shell(shell, base, out)
    voice_src = out / cfg.get("voice", "voice.cleaned/audio.m4a")
    voice_len = duration(voice_src)
    # 字幕時間是語音辨識對出來的，句首可能晚近一秒（一支短劇實測 0.3-0.9 秒）。先把字幕對齊配音表（TTS 的 lines.json）
    # 每句實際出聲的區間，旁白段的切點再取對齊後句首之前的句界，才不會截到被對白段取代的那句、或切掉下一句的開頭
    cc = timeline_cfg(cfg)
    lines = json.loads((base / cfg.get("lines", cc.get("lines"))).read_text(encoding="utf-8"))
    lead = float(cfg.get("lead_s", cc.get("lead_s", 0)))
    cuts = line_boundaries(lines, lead)
    # 段內各鏡的換鏡點仍照原字幕
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(voice_src), "-af", "silencedetect=noise=-35dB:d=0.25",
                          "-vn", "-f", "null", "-"], capture_output=True, text=True).stderr
    sub_cues = retime_cues(cues, lines, lead, speech_bounds(lines, lead, silences(log, voice_len), voice_len))
    seg, aud = out / ".segments", out / ".audio"
    seg.mkdir()
    aud.mkdir()
    videos, pieces, subs, blocks, report, expect = [], [], [], [], [], []
    t_frames = 0
    for i, blk in enumerate(cfg["sequence"], 1):
        offset = t_frames / FPS
        if "voice" in blk:
            first, last = blk["voice"]
            bs, be = block_bounds(sub_cues, first, last, cuts, cues[-1][2])
            fa, fb = round(bs * FPS), round(be * FPS)
            samples = (fb - fa) * (SR // FPS)
            narr = aud / f"b{i:02d}_voice.wav"
            audio_piece(voice_src, fa * (SR // FPS), samples, narr)
            amb_parts = []
            for name, a, b in shot_windows(cues, blk["shots"], start=bs, end=be):
                src, dst = clips / f"{name}.mp4", seg / f"{i:02d}_{name}.mp4"
                frames = segment_frames(a, b)
                k, pad = render_segment(src, frames, round(b - a, 3), dst, stepped, max_stretch=max_stretch)
                videos.append(dst)
                expect.append(frames)
                part = aud / f"b{i:02d}_{name}_amb.wav"
                audio_piece(src, 0, frames * (SR // FPS), part, gain)  # 這鏡自帶的環境音（沒有就是靜音；放慢的鏡頭不跟著放慢）
                amb_parts.append(part)
                report.append(f"[{i:02d} narration] {name} {a:6.2f}-{b:6.2f} → film {(t_frames + round(a * FPS) - fa) / FPS:6.2f}s"
                              + (f" slowed {k:.2f}x" if k > 1 else "") + (f" freeze-padded {pad:.2f}s" if pad else ""))
            amb = aud / f"b{i:02d}_amb.wav"
            concat(amb_parts, aud / f"b{i:02d}_amb.txt", amb, ["-c", "copy"])
            piece = aud / f"b{i:02d}.wav"
            mix(narr, amb, piece)
            subs += shift_cues(sub_cues, bs, min(be, voice_len), offset)
            blocks.append({"kind": "voice", "first": first, "last": last, "src_start": bs, "src_end": be,
                           "offset": offset, "frames": fb - fa})
            t_frames += fb - fa
        else:
            src = base / blk["clip"]
            have = duration(src)
            frames = round(have * FPS)
            dst = seg / f"{i:02d}_clip.mp4"
            render_segment(src, frames, have, dst, int(blk.get("stepped_fps", stepped)), always_pad=True)
            videos.append(dst)
            expect.append(frames)
            piece = aud / f"b{i:02d}.wav"
            audio_piece(src, 0, frames * (SR // FPS), piece)
            log = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(src), "-af", "silencedetect=noise=-35dB:d=0.25",
                                  "-vn", "-f", "null", "-"], capture_output=True, text=True).stderr
            texts = blk["text"] if isinstance(blk["text"], list) else [blk["text"]]
            if len(texts) == 1:
                spans = [speech_span(log, have)]
            elif blk.get("cut"):  # 兩人同鏡、句中有停頓：照指定的換人秒數切字幕
                s0, s1 = speech_span(log, have)
                cut = blk["cut"] if isinstance(blk["cut"], list) else [blk["cut"]]
                spans = list(zip([s0] + cut, cut + [s1]))
            else:  # 兩人同鏡：每段講話一句字幕
                spans = speech_spans(silences(log, have), have)
                if len(spans) != len(texts):
                    sys.exit(f"✗ sequence block {i}: detected {len(spans)} speech span(s) {spans}, but text has {len(texts)} line(s)")
            subs += [(round(offset + s0, 3), round(offset + s1, 3), t) for (s0, s1), t in zip(spans, texts)]
            blocks.append({"kind": "clip", "clip": str(src), "speaker": blk.get("speaker", "對白"), "text": "".join(texts),
                           "offset": offset, "frames": frames, "audio": str(piece)})
            report.append(f"[{i:02d} dialogue] {src.name} {have:5.2f}s → film {offset:6.2f}s, speech "
                          + ", ".join(f"{s0:.2f}-{s1:.2f}s" for s0, s1 in spans))
            t_frames += frames
        pieces.append(piece)
    total = t_frames / FPS
    got = [round(duration(v) * FPS) for v in videos]
    want = sum(b["frames"] for b in blocks)
    if sum(got) != want:
        off = [f"{v.name} has {g} frames, should be {e}" for v, g, e in zip(videos, got, expect) if g != e]
        sys.exit(f"✗ video segments total {sum(got)} frames, should be {want}: " + "; ".join(off))
    concat(videos, seg / "list.txt", out / "ve_visual.mp4", ["-c", "copy"])
    concat(pieces, aud / "list.txt", aud / "mix.wav", ["-c", "copy"])
    run(["ffmpeg", "-v", "error", "-y", "-i", str(aud / "mix.wav"), "-c:a", "aac", "-b:a", "192k", str(out / "mix.m4a")])
    srt = "".join(f"{k}\n{ts(a)} --> {ts(b)}\n{text}\n\n" for k, (a, b, text) in enumerate(subs, 1))
    (out / "subtitles.srt").write_text(srt, encoding="utf-8")
    (out / "sequence.json").write_text(json.dumps({"total": total, "blocks": blocks}, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
    index = out / "index.html"
    index.write_text(patch_shell(swap_video(index, shell), subs, round(total, 3), subs[-1][1]), encoding="utf-8")
    print("\n".join(report))
    print(f"film {total:.3f}s ({t_frames} frames), {len(subs)} subtitle lines → {out}")


def ts(sec: float) -> str:
    ms = round(sec * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main(cfg_path: str):
    cfg, base = load_config(cfg_path)
    out = base / cfg["out"]
    if out.exists():
        sys.exit(f"✗ output folder already exists: {out} (not overwritten; pick another out or delete it yourself)")
    (sequence if "sequence" in cfg else legacy)(cfg, base, out)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(USAGE)
    main(sys.argv[1])
