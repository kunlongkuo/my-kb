"""Do doc_screen's logged times and boxes match the recording (lecture-screen T1, R1)?

  python3 screen_sync_check.py <doc_screen --out folder> [--shift-t S] [--shift-box PX]

For the selftest page (fixtures/screen_selftest.html: a pure-red button turns pure blue when clicked), every click step
must show red inside its box at t - BEFORE and blue at t + AFTER. A box that only checks one colour would pass with a
time off by seconds, so both sides are checked. Inside the box shrunk by EDGE px (anti-aliasing), the share of pixels
of that colour (its channel ahead of the other two by DOMINANT) must be at least SHARE. Prints `sync ok N/N`, else each miss and exit 1.
BEFORE is 0.15 s: with the origin at page creation the logged t lands 0.02-0.08 s after the frame where the button
turns blue (2026-10-28, 4 runs x 2 clicks; 25 fps, so under two frames); the context-creation origin was 0.15-0.18 s off.
AFTER is 0.1 s for the same reason (blue is already there at t). Mutation-tested: times 0.2 s late, 0.3 s early or 1 s
late and boxes 60 px off fail; 0.2 s early can still pass (the change sometimes lands 0.1 s before t). With AFTER 0.3,
0.3 s early passed too.
--shift-t / --shift-box move every logged time / box before checking: the mutation self-test (a check that still
passes with them is not checking anything).
"""
import argparse, json, subprocess, sys
from pathlib import Path

import numpy as np

BEFORE, AFTER, EDGE, SHARE = 0.15, 0.1, 4, 0.9
DOMINANT = 80   # a pixel is red / blue when that channel beats both others by this much: also true under screen_step's dim
W, H = 1920, 1080


def frame(video, t):
    """The frame at t, or None past either end of the video (counts as a miss)."""
    if t < 0:
        return None
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(H, W, 3).astype(np.int16) if raw else None


def share(img, box, colour):
    if img is None:
        return 0.0
    x, y, w, h = (round(v) for v in box)
    a = img[max(y + EDGE, 0):max(y + h - EDGE, 0), max(x + EDGE, 0):max(x + w - EDGE, 0)]
    if not a.size:
        return 0.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    hit = (r - np.maximum(g, b) >= DOMINANT) if colour == "red" else (b - np.maximum(r, g) >= DOMINANT)
    return float(hit.mean())


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("out", type=Path)
    ap.add_argument("--shift-t", type=float, default=0.0)
    ap.add_argument("--shift-box", type=float, default=0.0)
    a = ap.parse_args()
    clicks = [s for s in json.loads((a.out / "log.json").read_text(encoding="utf-8"))["steps"] if s["do"] == "click"]
    if not clicks:
        sys.exit("✗ no click steps in log.json")
    bad = []
    for s in clicks:
        t, box = s["t"] + a.shift_t, [s["box"][0] + a.shift_box, s["box"][1] + a.shift_box, *s["box"][2:]]
        pre, post = share(frame(a.out / "screen.webm", t - BEFORE), box, "red"), share(frame(a.out / "screen.webm", t + AFTER), box, "blue")
        if pre < SHARE or post < SHARE:
            bad.append(f"step {s['n']}: red {pre:.2f} at t-{BEFORE}, blue {post:.2f} at t+{AFTER} (need ≥ {SHARE})")
    print("\n".join(bad + [f"sync {'ok' if not bad else 'off'} {len(clicks) - len(bad)}/{len(clicks)}"]))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
