"""Re-pick every lecture.json colour from its screenshot (lecture-style T1): `_source` says file, x, y.

  python3 lecture_tokens_check.py [--samples ~/Downloads/sample]      prints `tokens ok N/N`, else each mismatch and exit 1
"""
import argparse, json, sys
from pathlib import Path

from PIL import Image

THEMES = Path(__file__).resolve().parents[1] / "themes/lecture.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=Path, default=Path("~/Downloads/sample").expanduser())
    a = ap.parse_args()
    t = json.loads(THEMES.read_text(encoding="utf-8"))
    rows = [(mode, key, *src) for mode, keys in t["_source"].items() for key, src in keys.items()]
    bad = []
    for mode, key, name, x, y in rows:
        got = "#%02x%02x%02x" % Image.open(a.samples / name).convert("RGB").getpixel((x, y))
        if got != t[mode][key]:
            bad.append(f"{mode}.{key}: json {t[mode][key]}, {name} ({x}, {y}) is {got}")
    print("\n".join(bad + [f"tokens {'ok' if not bad else 'mismatch'} {len(rows) - len(bad)}/{len(rows)}"]))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
