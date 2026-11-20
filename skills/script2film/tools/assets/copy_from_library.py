"""Copy the fonts and your own sounds from an existing sound and font library (a folder with fonts/ and
sfx/manifest.json) into the asset layers. Copies only: nothing in the old library is moved, changed or deleted.

  python3 tools/assets/copy_from_library.py <old library folder> [--local <user layer folder>]

Since 2026-11-17 the sound effects ship with the repository (assets/sfx, in git), so this script no longer writes the
bundled sfx/ folder. What it still does:
  fonts/  the NotoSansTC* and NotoSerifTC* files go into the bundled layer ($S2F_ASSETS, default <repo>/assets), plus a
          manifest.json (OFL 1.1; the library's other fonts are not copied). Downloading them is the usual way
          (assets/README.md); this is for a machine that already has them in a library.
  --local the library's sounds whose id is not already in the bundled manifest go into the user layer (the folder
          S2F_ASSETS_LOCAL points to): sfx/ with the files and a manifest.json, merged by id with what is there.
          Without --local those sounds are listed and skipped. Music is never copied.
A sound keeps its manifest "file" path (e.g. ve-gen/x.mp3) inside the user layer's sfx/ folder.
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
import argparse, json, os, shutil, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FONTS = ("NotoSansTC", "NotoSerifTC")


def read_manifest(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def own_sounds(library, bundled):
    """The library's entries that do not ship with the repository (their id is not in the bundled manifest)."""
    shipped = {m["id"] for m in bundled}
    return [m for m in library if m["id"] not in shipped]


def merge(existing, entries):
    """existing manifest entries with entries added; an entry replaces the existing one of the same id."""
    ids = {m["id"] for m in entries}
    return [m for m in existing if m["id"] not in ids] + entries


def copy_sounds(entries, src, dst):
    (dst / "sfx").mkdir(parents=True, exist_ok=True)
    for m in entries:
        f = src / m["file"]
        if not f.exists():
            sys.exit(f"✗ {m['id']}: {f} is in the manifest but not on disk")
        (dst / "sfx" / m["file"]).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst / "sfx" / m["file"])
    man = merge(read_manifest(dst / "sfx/manifest.json"), entries)
    (dst / "sfx/manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("library", help="the old library folder (has fonts/ and sfx/manifest.json)")
    ap.add_argument("--local", help="the user layer folder (S2F_ASSETS_LOCAL) for the library's own sounds")
    a = ap.parse_args()
    lib = Path(a.library).expanduser().resolve()
    out = Path(os.environ.get("S2F_ASSETS") or REPO / "assets").expanduser().resolve()
    if not (lib / "sfx/manifest.json").exists() or not (lib / "fonts").is_dir():
        sys.exit(f"✗ {lib} has no fonts/ or sfx/manifest.json")
    if out == lib or (a.local and Path(a.local).expanduser().resolve() == lib):
        sys.exit("✗ the destination is the library itself")

    fonts = sorted(f for f in (lib / "fonts").iterdir() if f.is_file() and f.name.startswith(FONTS))
    if not fonts:
        sys.exit(f"✗ no {' / '.join(FONTS)} font in {lib / 'fonts'}")
    (out / "fonts").mkdir(parents=True, exist_ok=True)
    for f in fonts:
        shutil.copy2(f, out / "fonts" / f.name)
    (out / "fonts/manifest.json").write_text(json.dumps(
        [{"id": f.stem, "file": f.name, "license": "OFL 1.1", "source": "google/fonts (Noto)"} for f in fonts],
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"✓ {len(fonts)} fonts → {out / 'fonts'}: {', '.join(f.name for f in fonts)}")

    rest = own_sounds(read_manifest(lib / "sfx/manifest.json"), read_manifest(out / "sfx/manifest.json"))
    if a.local:
        loc = Path(a.local).expanduser().resolve()
        copy_sounds(rest, lib / "sfx", loc)
        print(f"✓ {len(rest)} sounds that do not ship with the repository → {loc / 'sfx'} (set S2F_ASSETS_LOCAL={loc})")
    else:
        print(f"  {len(rest)} sounds that do not ship with the repository skipped (give --local <folder> to copy them "
              f"to your own layer)")
    print(f"  the bundled sounds ({out / 'sfx'}) are in git and were not touched")


if __name__ == "__main__":
    main()
