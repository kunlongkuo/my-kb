"""Copies Prompt Studio into the website so GitHub Pages (which publishes only docs/) can serve it.

  python3 tools/site/sync_studio.py

tools/prompt-studio/prompt-studio.html is the source. docs/studio/app.html is a byte-for-byte copy, never edited by hand.
tools/site/tests/test_site_studio_copy.py fails when the two differ, so a change to the tool without this step is caught.
The tool's footer links to "index.html"; next to the copy that is docs/studio/index.html, a small page that forwards to
the site's Prompt Studio page (docs/studio.html).
"""
import pathlib, shutil

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "tools" / "prompt-studio" / "prompt-studio.html"
DST = ROOT / "docs" / "studio" / "app.html"

if __name__ == "__main__":
    DST.parent.mkdir(parents=True, exist_ok=True)
    same = DST.exists() and DST.read_bytes() == SRC.read_bytes()
    if not same:
        shutil.copyfile(SRC, DST)
    print(("unchanged: " if same else "copied: ") + str(DST.relative_to(ROOT)))
