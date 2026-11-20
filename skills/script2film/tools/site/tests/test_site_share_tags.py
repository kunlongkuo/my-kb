"""Share-preview tags on the eight site pages (fix: python3 tools/site/build_en.py)."""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import og_tags  # noqa: E402
from site_config import BASE_URL, OG_IMAGE_SIZE, PAGES  # noqa: E402

DOCS = Path(__file__).resolve().parents[3] / "docs"
CASES = [(p, lang) for lang in ("zh", "en") for p in PAGES]
PROPS = ["og:title", "og:description", "og:type", "og:url", "og:image", "og:image:width", "og:image:height",
         "og:image:alt", "og:site_name", "og:locale", "og:locale:alternate"]


def head(page, lang):
    return og_tags.file_of(page, lang).read_text(encoding="utf-8").split("</head>")[0]


def meta(text, prop):
    return re.findall(r'<meta (?:property|name)="%s" content="([^"]*)">' % re.escape(prop), text)


@pytest.mark.parametrize("page,lang", CASES)
def test_page_has_every_share_tag_once(page, lang):
    h = head(page, lang)
    for prop in PROPS + ["twitter:card"]:
        assert len(meta(h, prop)) == 1, f"{lang}/{page}: {prop}"
    assert meta(h, "og:type") == ["website"]
    assert meta(h, "twitter:card") == ["summary_large_image"]
    assert meta(h, "og:locale") == [{"zh": "zh_TW", "en": "en_US"}[lang]]
    assert meta(h, "og:locale:alternate") == [{"zh": "en_US", "en": "zh_TW"}[lang]]
    assert meta(h, "og:image:width") == [str(OG_IMAGE_SIZE[0])] and meta(h, "og:image:height") == [str(OG_IMAGE_SIZE[1])]
    assert re.findall(r'<link rel="canonical" href="([^"]*)">', h) == [og_tags.page_url(page, lang)]
    alts = dict(re.findall(r'<link rel="alternate" hreflang="([^"]*)" href="([^"]*)">', h))
    assert alts == {"zh-Hant": og_tags.page_url(page, "zh"), "en": og_tags.page_url(page, "en"),
                    "x-default": og_tags.page_url(page, "zh")}
    assert meta(h, "og:url") == [og_tags.page_url(page, lang)]


@pytest.mark.parametrize("page,lang", CASES)
def test_title_and_description_follow_the_page(page, lang):
    h = head(page, lang)
    title = re.search(r"<title>(.*?)</title>", h, re.S).group(1)
    desc = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', h).group(1)
    assert meta(h, "og:title") == [" ".join(title.split())]
    assert meta(h, "og:description") == [" ".join(desc.split())]


@pytest.mark.parametrize("page,lang", CASES)
def test_share_urls_start_with_base_url_and_image_exists(page, lang):
    h = head(page, lang)
    urls = meta(h, "og:url") + meta(h, "og:image") + re.findall(r'<link rel="(?:canonical|alternate)"[^>]*href="([^"]*)"', h)
    assert len(urls) == 6
    assert all(u.startswith(BASE_URL) for u in urls), urls
    img = meta(h, "og:image")[0][len(BASE_URL):]
    assert img.startswith("site/") and (DOCS / img).is_file(), img
    for u in urls:   # every share URL points at a page or file that exists in docs/
        rel = u[len(BASE_URL):]
        assert (DOCS / (rel + "index.html" if rel == "" or rel.endswith("/") else rel)).is_file(), u


@pytest.mark.parametrize("lang", ["zh", "en"])
def test_og_image_size(lang):
    from PIL import Image
    from site_config import OG_IMAGE
    f = DOCS / OG_IMAGE[lang]
    assert Image.open(f).size == OG_IMAGE_SIZE
    assert f.stat().st_size < 300 * 1024


@pytest.mark.parametrize("page,lang", CASES)
def test_each_language_shares_its_own_image(page, lang):
    from site_config import OG_IMAGE
    assert meta(head(page, lang), "og:image") == [BASE_URL + OG_IMAGE[lang]]


@pytest.mark.parametrize("page,lang", CASES)
def test_writer_is_idempotent_and_pages_are_up_to_date(page, lang):
    text = og_tags.file_of(page, lang).read_text(encoding="utf-8")
    once = og_tags.apply(text, page, lang)
    assert og_tags.apply(once, page, lang) == once
    assert once == text, f"{lang}/{page} is out of date: run python3 tools/site/build_en.py"
    assert og_tags.apply(og_tags.strip(text), page, lang) == text


def test_block_ignores_a_stale_block():
    t = '<head>\n  <title>T</title>\n  <meta name="description" content="D">\n</head>'
    a = og_tags.apply(t, "gallery", "zh")
    stale = a.replace('og:title" content="T"', 'og:title" content="old"')
    assert stale != a
    assert og_tags.apply(stale, "gallery", "zh") == a
    assert a.count(og_tags.BEGIN) == 1
