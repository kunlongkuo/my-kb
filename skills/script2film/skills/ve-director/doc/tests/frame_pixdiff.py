"""Pixel-level comparison of two renders of the same clip (lecture-style T0, second layer after framemd5_diff.py).

  python3 frame_pixdiff.py <a.mp4> <b.mp4> [--every 15]

framemd5 is exact, but the HyperFrames renderer is not bit-stable: two renders of episode 10 from the same scripts
differ in 4 of 18 files (2026-10-28: B1 cover, B30 burst_title and the two joined tracks), by at most 21-27 grey levels
on at most 1 pixel per frame. So a file that framemd5 flags in the baseline too is compared here instead: every Nth frame,
the share of pixels that differ by more than 24 grey levels. Over 0.1 % (about 2,000 pixels; one moved caption is
tens of thousands) on any sampled frame, or a frame count mismatch, fails.
"""
import argparse, subprocess, sys

import numpy as np

W, H, LEVEL, SHARE = 1920, 1080, 24, 0.001


def frames(path, every):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"select=not(mod(n\\,{every})),scale={W}:{H}",
                          "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, H, W)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--every", type=int, default=15)
    x = ap.parse_args()
    a, b = frames(x.a, x.every), frames(x.b, x.every)
    if len(a) != len(b):
        print(f"✗ sampled frames {len(a)} vs {len(b)}")
        sys.exit(1)
    shares = (np.abs(a.astype(np.int16) - b.astype(np.int16)) > LEVEL).mean(axis=(1, 2))
    worst = int(shares.argmax())
    msg = f"{len(a)} frames, worst {shares[worst]:.4%} at sampled frame {worst} (frame {worst * x.every})"
    if shares[worst] > SHARE:
        print(f"✗ {msg}")
        sys.exit(1)
    print(f"close: {msg}")


if __name__ == "__main__":
    main()
