"""兩人同鏡的對嘴片：用 Voice Changer 各換過一次聲音的版本，依講話先後拼成一支（畫面用原片）。

用法：python3 tools/drama/splice_voices.py <原片.mp4> <第1段講話的換聲版.mp4> <第2段的換聲版.mp4> ... -o <輸出.mp4>
Voice Changer 不動畫面與長度、講話時間點也不變（實測差 0.01 秒內），所以照原片的講話區間切：
第 k 段講話用第 k 個換聲版的聲音，切點在兩段講話之間空白的中點。講話段數要剛好等於換聲版的數量，否則停下。
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools/assemble"))   # velib
from velib import duration, silences, speech_spans, splice_cuts  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=(
        "Lip-synced shot with two people: splice the versions each voiced once by Voice Changer into one, in speaking order "
        "(the picture is the original's).\n\n"
        "Voice Changer keeps the picture, the length and the speech timing (measured within 0.01 s), so the cut follows the "
        "original's speech spans:\nspan k takes its sound from voiced version k, and each cut sits at the middle of the "
        "silence between two spans.\nThe number of speech spans must equal the number of voiced versions, otherwise it stops."),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("original")
    ap.add_argument("voiced", nargs="+")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--cut", type=float, nargs="+",
                    help="seconds where the speaker changes (give them by hand when a line has pauses and there are more speech spans than voiced versions; count = voiced versions − 1)")
    a = ap.parse_args(argv)
    src, out = Path(a.original), Path(a.out)
    if out.exists():
        sys.exit(f"✗ output exists: {out} (not overwritten)")
    dur = duration(src)
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(src), "-af", "silencedetect=noise=-35dB:d=0.25",
                          "-vn", "-f", "null", "-"], capture_output=True, text=True).stderr
    spans = speech_spans(silences(log, dur), dur)
    if a.cut:
        if len(a.cut) != len(a.voiced) - 1:
            sys.exit(f"✗ --cut needs {len(a.voiced) - 1} values")
        spans = [(x, y) for x, y in zip([0.0] + a.cut, a.cut + [dur])]
    elif len(spans) != len(a.voiced):
        sys.exit(f"✗ the original has {len(spans)} speech spans {spans}, but {len(a.voiced)} voiced versions were given; use --cut to give the seconds where the speaker changes")
    for v in a.voiced:
        if abs(duration(Path(v)) - dur) > 0.05:
            sys.exit(f"✗ {v} is not the same length as the original, so it is not a revoiced copy of it")
    cuts = [(x, y) for x, y in spans] if a.cut else splice_cuts(spans, dur)
    inputs, parts = ["-i", str(src)], []
    for k, (v, (x, y)) in enumerate(zip(a.voiced, cuts), 1):
        inputs += ["-i", v]
        parts.append(f"[{k}:a]atrim=start={x}:end={y},asetpts=PTS-STARTPTS[p{k}]")
    graph = ";".join(parts) + ";" + "".join(f"[p{k}]" for k in range(1, len(cuts) + 1)) + f"concat=n={len(cuts)}:v=0:a=1[a]"
    subprocess.run(["ffmpeg", "-v", "error", *inputs, "-filter_complex", graph, "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", str(out)], check=True)
    for (s0, s1), (x, y), v in zip(spans, cuts, a.voiced):
        print(f"speech {s0:.2f}-{s1:.2f}s ← {Path(v).parent.name}/{Path(v).name} ({x:.2f}-{y:.2f}s)")
    print(f"→ {out} ({duration(out):.3f}s)")


if __name__ == "__main__":
    main()
