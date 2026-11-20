"""Compare two renders frame by frame (lecture-style T0: shared-script changes must not move the collage output).

  python3 framemd5_diff.py <base>/framemd5 <new>/framemd5 [--noise N]

Each folder holds `<name>.txt` files written by `ffmpeg -i <mp4> -f framemd5 <name>.txt`. Prints `same`, or the frames
that differ per file and the total; with --noise N a total ≤ N prints `diff T ≤ noise N` and still passes.
Exit 0 = same or within noise, 1 = more than that or a file missing on one side.
"""
import argparse, sys
from pathlib import Path


def frames(p):
    """(stream, pts) → hash, from ffmpeg's framemd5 lines `stream, dts, pts, duration, size, hash`."""
    out = {}
    for line in p.read_text().splitlines():
        if line.startswith("#") or not line.strip():
            continue
        f = [x.strip() for x in line.split(",")]
        out[(f[0], f[2])] = f[5]
    return out


def compare(a_dir, b_dir):
    """{file name: frames that differ (a missing frame counts)}; a file missing on one side counts as None."""
    names = sorted({p.name for p in a_dir.glob("*.txt")} | {p.name for p in b_dir.glob("*.txt")})
    out = {}
    for n in names:
        a, b = a_dir / n, b_dir / n
        if not (a.exists() and b.exists()):
            out[n] = None
            continue
        fa, fb = frames(a), frames(b)
        out[n] = sum(fa.get(k) != fb.get(k) for k in fa.keys() | fb.keys())
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("base", type=Path)
    ap.add_argument("new", type=Path)
    ap.add_argument("--noise", type=int, default=0)
    a = ap.parse_args()
    res = compare(a.base, a.new)
    if not res:
        sys.exit("✗ no framemd5 files in either folder")
    missing = [n for n, d in res.items() if d is None]
    total = sum(d for d in res.values() if d)
    for n, d in res.items():
        if d is None or d:
            print(f"{n}: {'missing on one side' if d is None else f'{d} frames differ'}")
    if missing:
        print(f"✗ {len(missing)} file(s) missing")
        sys.exit(1)
    if total == 0:
        print(f"same ({len(res)} files)")
    elif total <= a.noise:
        print(f"diff {total} ≤ noise {a.noise}")
    else:
        print(f"✗ diff {total} > noise {a.noise}")
        sys.exit(1)


if __name__ == "__main__":
    main()
