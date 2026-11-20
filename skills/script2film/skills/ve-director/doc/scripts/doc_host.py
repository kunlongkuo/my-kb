"""TalkingPhoto host take for a narration longer than one TP render (High Quality takes at most 1 minute, at least 10 s).

  python3 doc_host.py split <project>/doc.json [--max 58] [--min 10]
      tts/voice.wav → host/parts/part1.mp3 … cut in the pause between two lines, each part ≤ --max s and ≥ --min s
      (TP takes at least 10 s; MiniMax H3 takes at most 15 s: --max 15 --min 4);
      host/parts.json keeps where each part sits in voice.wav. Render every part in TP on the same character.
  python3 doc_host.py join <project>/doc.json [--out host/tp_host.mp4]
      host/parts/partK.mp4 (the downloaded TP takes) → one take on the subtitle timeline (voice.cleaned/audio.m4a), so
      doc.json "clip_sync" / "pip" can use it like a single full-narration render: each take is trimmed or held to its
      part's exact length and the narration's lead silence (doc_align LEAD) is held on the first frame.
2026-10-21 (約伯記 1-13, 176 s): four parts cut by hand at beat starts on the wrong timeline (audio.m4a, which starts
with the lead silence) landed 0.45 s late, inside a word; cutting in the pauses of tts/lines.json avoids that.
"""
import json, sys

from doc_align import END_HOLD, LEAD
from doc_common import duration, load, read_json, sh

MIN_PART = 10.0


def cut_points(lines, total, cap, least=MIN_PART):
    """Cuts at the middle of the pauses between lines: as late as the cap allows, the last part kept ≥ least."""
    pauses = [(a["end"] + b["start"]) / 2 for a, b in zip(lines, lines[1:])]
    cuts, start = [], 0.0
    while total - start > cap:
        ok = [p for p in pauses if least <= p - start <= cap and total - p >= least]
        if not ok:
            sys.exit(f"✗ no pause between {start + least:.1f}s and {start + cap:.1f}s to cut at")
        cuts.append(max(ok))
        start = cuts[-1]
    return cuts


def split(doc, P, cap, least=MIN_PART):
    lines, voice = read_json(P / "tts/lines.json", "run doc_voice.py first"), P / "tts/voice.wav"
    total, end = duration(voice), max(0.6, float(doc.get("end_hold", END_HOLD)))
    edges = [0.0, *cut_points(lines, total + end, cap, least), total]   # the last part's closing silence counts toward --max
    out = P / "host/parts"
    out.mkdir(parents=True, exist_ok=True)
    parts = []
    last = len(edges) - 1
    for k, (a, b) in enumerate(zip(edges, edges[1:]), 1):
        # the last part ends in silence as long as the film runs on after the voice (doc_align end_hold), so the host's
        # face can settle instead of freezing on the frame of the last word (2026-11-18). TalkingPhotos trims that silence
        # (a 20.04 s part came back 18.05 s; join then holds the last frame), so for TP it does not help yet
        tail = end if k == last else 0.0
        sh("ffmpeg", "-v", "error", "-y", "-i", voice, "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-af", f"apad=pad_dur={tail:.2f}",
           "-b:a", "192k", out / f"part{k}.mp3")
        parts.append({"k": k, "start": round(a, 3), "end": round(b, 3), "tail": tail})
        print(f"part{k}.mp3 {a:7.2f}-{b:7.2f} ({b - a + tail:.1f}s)")
    (P / "host/parts.json").write_text(json.dumps(parts, indent=1), encoding="utf-8")


def join(doc, P, out):
    parts = read_json(P / "host/parts.json", "run doc_host.py split first")
    tmp = P / "host/parts"
    segs = []
    for p in parts:
        src, seg, d = tmp / f"part{p['k']}.mp4", tmp / f"_seg{p['k']}.mp4", p["end"] - p["start"] + p.get("tail", 0.0)
        if not src.exists():
            sys.exit(f"✗ missing TP take {src}")
        hold = LEAD if p["k"] == 1 else 0.0    # the subtitle timeline starts with LEAD s of silence before the voice
        vf = (f"fps=30,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,"
              f"tpad=start_mode=clone:start_duration={hold}:stop_mode=clone:stop_duration=5")
        sh("ffmpeg", "-v", "error", "-y", "-i", src, "-an", "-vf", vf, "-t", f"{d + hold:.3f}",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", seg)
        print(f"part{p['k']}: take {duration(src):.2f}s → {d + hold:.2f}s")
        segs.append(seg)
    lst = tmp / "_concat.txt"
    lst.write_text("".join(f"file '{s.name}'\n" for s in segs))
    sh("ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", P / out)
    for s in [*segs, lst]:
        s.unlink()
    print(f"{out}: {duration(P / out):.2f}s (narration {duration(P / 'voice.cleaned/audio.m4a'):.2f}s)")


def main():
    cmd, doc_path, args = sys.argv[1], sys.argv[2], sys.argv[3:]
    doc, P = load(doc_path)
    if cmd == "split":
        least = float(args[args.index("--min") + 1]) if "--min" in args else MIN_PART
        if not 1.0 <= least <= MIN_PART:
            sys.exit(f"✗ --min must be between 1 and {MIN_PART:g} s")
        cap = float(args[args.index("--max") + 1]) if "--max" in args else 58.0
        split(doc, P, max(2 * least, min(cap, 60.0)), least)
    elif cmd == "join":
        join(doc, P, args[args.index("--out") + 1] if "--out" in args else "host/tp_host.mp4")
    else:
        sys.exit("usage: doc_host.py split|join <doc.json>")


if __name__ == "__main__":
    main()
