"""Is the right side of a stage-left frame empty (lecture-style T3)? The host frame goes there (doc_cut "side").

  python3 stage_left_check.py <frame.png> [...]      prints `clear` per frame, else the share of content pixels; exit 1 if any

A pixel in x >= 1240 counts as content when it differs from its row's median there by more than 24 levels (about 9 %;
the background is a vertical gradient plus a soft vignette, so a clean row stays close to its median). A frame is clear
when under 3 % of that region is content.
"""
import sys

import numpy as np
from PIL import Image

X0, LEVEL, SHARE = 1240, 24, 0.03


def content_share(path):
    a = np.asarray(Image.open(path).convert("L"), dtype=np.int16)[:, X0:]
    return float((np.abs(a - np.median(a, axis=1, keepdims=True)) > LEVEL).mean())


def main():
    bad = 0
    for p in sys.argv[1:]:
        s = content_share(p)
        print(f"{p}: {'clear' if s < SHARE else 'content'} ({s:.2%})")
        bad += s >= SHARE
    sys.exit(1 if bad or len(sys.argv) < 2 else 0)


if __name__ == "__main__":
    main()
