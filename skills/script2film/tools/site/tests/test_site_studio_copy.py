"""The website's copy of Prompt Studio must match the tool byte for byte (fix: python3 tools/site/sync_studio.py)."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]


def test_site_copy_matches_the_tool():
    src = ROOT / "tools" / "prompt-studio" / "prompt-studio.html"
    dst = ROOT / "docs" / "studio" / "app.html"
    assert dst.exists(), "docs/studio/app.html is missing: run python3 tools/site/sync_studio.py"
    assert dst.read_bytes() == src.read_bytes(), \
        "docs/studio/app.html differs from tools/prompt-studio/prompt-studio.html: run python3 tools/site/sync_studio.py"


def test_tool_footer_link_has_a_target_next_to_the_copy():
    # the tool links to "index.html" beside itself; on the site that is docs/studio/index.html
    assert (ROOT / "docs" / "studio" / "index.html").exists()
