"""Settings shared by the website scripts in tools/site/.

BASE_URL is the published address of docs/ (GitHub Pages). It is the only place the site's full address is written:
og_tags.py builds every share-preview URL (og:url, og:image, canonical, hreflang) from it.
"""
BASE_URL = "https://notoriouslab.github.io/script2film/"
SITE_NAME = "Script2Film"
OG_IMAGE = {"zh": "site/og-zh.jpg", "en": "site/og.jpg"}   # relative to docs/; made by tools/site/make_og.py
OG_IMAGE_SIZE = (1200, 630)
PAGES = ("index", "gallery", "tools", "studio")   # docs/<page>.html and docs/en/<page>.html
