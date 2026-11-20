"""Check every lecture.json palette against the rules for adding one (README "新增色票").

  python3 lecture_palette_check.py      prints five contrast ratios per palette, exit 1 if a key, a reason or a text contrast fails
"""
import json, os, sys
from pathlib import Path

THEMES = Path(__file__).resolve().parents[1] / "themes/lecture.json"
KEYS = ["bg", "panel", "fg", "muted", "accent", "accent2", "hi", "ring", "dim", "font_big", "font_ui"]
PALETTES = [k for k in json.loads(THEMES.read_text(encoding="utf-8")) if not k.startswith("_")]
TEXT_PAIRS = (("fg", "bg"), ("fg", "panel"), ("muted", "bg"))     # must be >= AA
SHOWN_PAIRS = (("accent", "bg"), ("accent2", "bg"))               # printed only: used for big numbers and shapes
AA = 4.5


def _lum(hexs):
    c = [int(hexs[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    """WCAG 2.1 contrast ratio of two #rrggbb colours."""
    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def find_source(src):
    """`<repo folder>:<path>` under PALETTE_SRC_ROOTS -> ("ok" | "no-file" | "no-repo", path or the roots searched).
    PALETTE_SRC_ROOTS has no default: unset, every source is "no-repo" (the test skips and says why)."""
    repo, rel = src.split(":", 1)
    roots = [r for r in os.environ.get("PALETTE_SRC_ROOTS", "").split(":") if r]
    if not roots:
        return "no-repo", "PALETTE_SRC_ROOTS not set"
    for root in roots:
        d = Path(root).expanduser() / repo
        if d.is_dir():
            return ("ok" if (d / rel).exists() else "no-file"), str(d / rel)
    return "no-repo", ":".join(roots)


def main():
    t = json.loads(THEMES.read_text(encoding="utf-8"))
    bad = []
    for mode in PALETTES:
        p = t[mode]
        bad += [f"{mode}: missing {k}" for k in KEYS if k not in p]
        if not (p.get("_why") or mode in t["_source"]):
            bad.append(f"{mode}: no _why and no _source entry")
        cells = []
        for a, b in TEXT_PAIRS + SHOWN_PAIRS:
            r = contrast(p[a], p[b])
            cells.append(f"{a}/{b} {r:.2f}")
            if (a, b) in TEXT_PAIRS and r < AA:
                bad.append(f"{mode}: {a}/{b} {r:.2f} < {AA}")
        print(f"{mode:8s} " + "  ".join(cells))
    print("\n".join(bad + [f"palettes {'ok' if not bad else 'fail'} {len(PALETTES)}"]))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
