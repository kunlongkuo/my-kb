"""Writes the share-preview tags (Open Graph, Twitter card, canonical, hreflang) into the <head> of the eight site pages.

  python3 tools/site/og_tags.py

build_en.py calls this too, so after editing a Chinese page one command updates everything:

  python3 tools/site/build_en.py        # English pages + share tags on all eight pages
  python3 tools/site/make_og.py         # only when the preview image itself should change (see that file)

Each page gets one block between the two marker comments below, placed after <meta name="description">. The block is
rebuilt from the page's own <title> and description and from BASE_URL in site_config.py, and replaces any block
already there, so running this twice changes nothing. Do not edit the block by hand.
"""
import html, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from site_config import BASE_URL, SITE_NAME, OG_IMAGE, OG_IMAGE_SIZE, PAGES  # noqa: E402

D = pathlib.Path(__file__).resolve().parents[2] / "docs"
BEGIN = "<!-- share preview: written by tools/site/og_tags.py -->"
END = "<!-- /share preview -->"
LOCALE = {"zh": "zh_TW", "en": "en_US"}
HREFLANG = {"zh": "zh-Hant", "en": "en"}
IMAGE_ALT = {"zh": "Script2Film 字樣與「給 AI agent 用的影片與解說片工具組」，旁邊是兩格每日得力一分鐘的成片畫面",
             "en": "The Script2Film name beside two frames from films: a dinosaur chasing explorers, and a host with English subtitles"}
BLOCK_RX = re.compile(r"\n[ \t]*" + re.escape(BEGIN) + r".*?" + re.escape(END), re.S)


def page_path(page, lang):
    """Path of a page relative to docs/ as it is published; the index is the folder itself."""
    prefix = "en/" if lang == "en" else ""
    return prefix if page == "index" else f"{prefix}{page}.html"


def page_url(page, lang):
    return BASE_URL + page_path(page, lang)


def strip(text):
    return BLOCK_RX.sub("", text)


def _attr(s):
    return html.escape(html.unescape(" ".join(s.split())), quote=True)


def block(text, page, lang, indent="  "):
    title = re.search(r"<title>(.*?)</title>", text, re.S)
    desc = re.search(r'<meta\s+name="description"\s+content="([^"]*)"\s*>', text, re.S)
    assert title and desc, f"{lang}/{page}: <title> or <meta name=\"description\"> missing"
    other = "en" if lang == "zh" else "zh"
    w, h = OG_IMAGE_SIZE
    tags = [
        BEGIN,
        f'<link rel="canonical" href="{page_url(page, lang)}">',
        f'<link rel="alternate" hreflang="{HREFLANG["zh"]}" href="{page_url(page, "zh")}">',
        f'<link rel="alternate" hreflang="{HREFLANG["en"]}" href="{page_url(page, "en")}">',
        f'<link rel="alternate" hreflang="x-default" href="{page_url(page, "zh")}">',
        f'<meta property="og:type" content="website">',
        f'<meta property="og:site_name" content="{SITE_NAME}">',
        f'<meta property="og:title" content="{_attr(title.group(1))}">',
        f'<meta property="og:description" content="{_attr(desc.group(1))}">',
        f'<meta property="og:url" content="{page_url(page, lang)}">',
        f'<meta property="og:locale" content="{LOCALE[lang]}">',
        f'<meta property="og:locale:alternate" content="{LOCALE[other]}">',
        f'<meta property="og:image" content="{BASE_URL + OG_IMAGE[lang]}">',
        f'<meta property="og:image:width" content="{w}">',
        f'<meta property="og:image:height" content="{h}">',
        f'<meta property="og:image:alt" content="{_attr(IMAGE_ALT[lang])}">',
        '<meta name="twitter:card" content="summary_large_image">',
        END,
    ]
    return "\n" + "\n".join(indent + t for t in tags)


def apply(text, page, lang):
    """Returns the page text with a fresh share block after the description; apply(apply(t)) == apply(t)."""
    text = strip(text)
    m = re.search(r'[ \t]*<meta\s+name="description"\s+content="[^"]*"\s*>', text, re.S)
    assert m, f"{lang}/{page}: <meta name=\"description\"> missing"
    indent = re.match(r"[ \t]*", m.group(0)).group(0)
    return text[:m.end()] + block(text, page, lang, indent) + text[m.end():]


def file_of(page, lang):
    return D / ("en" if lang == "en" else "") / f"{page}.html"


def write(page, lang):
    f = file_of(page, lang)
    old = f.read_text(encoding="utf-8")
    new = apply(old, page, lang)
    if new != old:
        f.write_text(new, encoding="utf-8")
    return new != old


if __name__ == "__main__":
    for lang in ("zh", "en"):
        for p in PAGES:
            print(("updated: " if write(p, lang) else "unchanged: ") + str(file_of(p, lang).relative_to(D.parent)))
