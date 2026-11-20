"""Doc-mode themes: the look of code shots (CODE_THEMES) and the style block of VE prompts (VE_THEMES).

collage = the official VOX template (tan / ink black / halftone grey, one hot red accent, restrained mustard; hand-cut paper,
halftone photo cutouts, tape). live = documentary realism (VE photoreal shots, dark infographic code shots).
Code-shot filters are userSpaceOnUse and extend into negative coordinates: with the default region a purely horizontal or
vertical line has a zero-size box and vanishes, and dots drawn around their own origin get clipped.
lecture-<mode> = knowledge-teaching look (flat panels, no paper): light, dark, story, finance, food, colours from ../themes/lecture.json.
dark-gold, newsroom, vintage-poster, editorial-serif, cinematic-dark = styled themes from ../themes/styles.json: palette, shape and
ground each change, and each names the VE look its VE shots use.
"light": the frame is light, so subtitles without sub_bg are dark ink and paper wipes are paper-coloured.
"pill": (fill, text) of doc_cut's keyword pills.
"""
import json
from pathlib import Path

U = 'filterUnits="userSpaceOnUse" x="-1920" y="-1080" width="5760" height="3240"'

CODE_THEMES = {
    "collage": dict(
        vars="--bg:#e6d9bd; --fg:#1f1b16; --red:#d0372a; --must:#d6a227; --hi:#f4ecd8; --strip:#f5efe0; --font-big:'Noto Serif TC'; --font-ui:'Noto Sans TC';",
        paper="""background: var(--bg);""",
        texture="""<filter id="fib"><feTurbulence type="fractalNoise" baseFrequency="0.7" numOctaves="3" seed="2"/>
      <feColorMatrix values="0 0 0 0 .30  0 0 0 0 .22  0 0 0 0 .12  0 0 0 .14 0"/></filter>
    <filter id="blot"><feTurbulence type="fractalNoise" baseFrequency="0.006" numOctaves="3" seed="8"/>
      <feColorMatrix values="0 0 0 0 .40  0 0 0 0 .30  0 0 0 0 .16  0 0 0 .20 -.05"/></filter>
    <rect width="1920" height="1080" filter="url(#blot)"/><rect width="1920" height="1080" filter="url(#fib)"/>
    <pattern id="ht" width="7" height="7" patternUnits="userSpaceOnUse"><circle cx="3.5" cy="3.5" r="1.1" fill="#3a2f22" opacity=".10"/></pattern>
    <rect width="1920" height="1080" fill="url(#ht)"/>""",
        # 剪紙：邊緣微抖＋落地投影；wash＝柔影；brush＝馬克筆（不暈）
        filters=f"""<filter id="bleed" {U}><feTurbulence type="fractalNoise" baseFrequency="0.09" numOctaves="2" seed="3" result="n"/>
        <feDisplacementMap in="SourceGraphic" in2="n" scale="5" xChannelSelector="R" yChannelSelector="G" result="d"/>
        <feDropShadow in="d" dx="4" dy="6" stdDeviation="2.5" flood-color="#2a1f12" flood-opacity=".38"/></filter>
      <filter id="wash" {U}><feGaussianBlur stdDeviation="14"/></filter>
      <filter id="brush" {U}><feTurbulence type="fractalNoise" baseFrequency="0.6" numOctaves="2" seed="9" result="n"/>
        <feDisplacementMap in="SourceGraphic" in2="n" scale="3" xChannelSelector="R" yChannelSelector="G"/></filter>""",
        vignette="rgba(0,0,0,0) 60%, rgba(70,45,15,.22) 100%", dim="#14100b", flash="#fff8e8",
        css="""
  .ph .inner { filter: grayscale(1) contrast(1.35) brightness(1.06) sepia(.12); }
  .ph .tone { position:absolute; inset:0; background: radial-gradient(rgba(20,14,8,.55) 1.1px, transparent 1.6px) 0 0/6px 6px; mix-blend-mode: multiply; opacity:.45; }
  .ph .tape { position:absolute; width:150px; height:38px; background: rgba(214,162,39,.62); top:-18px; left:calc(50% - 75px); transform: rotate(-4deg); box-shadow: 0 1px 2px rgba(0,0,0,.15); }
  .cap, .quote { position:absolute; background: var(--strip); color: var(--fg); font-family: var(--font-ui); font-weight: 700; padding: 10px 18px; box-shadow: 3px 4px 0 rgba(40,28,14,.25); white-space: nowrap; }
  .cap { font-size: 30px; letter-spacing: 2px; transform: rotate(-1.2deg); }
  .cap .bar { display:none; }
  .quote { font-family: var(--font-big); font-size: 40px; font-weight: 800; transform: rotate(.8deg); }
  #big { color: var(--fg); } #term .main, #label .main { background: var(--strip); padding: 6px 16px; box-shadow: 3px 4px 0 rgba(40,28,14,.25); display:inline-block; }
""",
        torn=True, photo_ease="steps(5)", light=True, pill=("#1f1b16", "#f5efe0"), ring="#f4ecd8"),
    "live": dict(
        vars="--bg:#111315; --bg-solid:#111315; --fg:#ebe8e1; --red:#e2463b; --must:#e0b44a; --hi:#ffffff; --strip:rgba(0,0,0,0); --font-big:'Noto Sans TC'; --font-ui:'Noto Sans TC';",
        paper="""background: radial-gradient(ellipse at 50% 45%, #1d2125 0%, #111315 60%, #0b0c0d 100%);""",
        texture="""<filter id="fib"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="2"/>
      <feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .05 0"/></filter>
    <rect width="1920" height="1080" filter="url(#fib)"/>""",
        filters=f"""<filter id="bleed" {U}><feGaussianBlur stdDeviation="3" result="g"/><feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      <filter id="wash" {U}><feGaussianBlur stdDeviation="18"/></filter>
      <filter id="brush" {U}><feGaussianBlur stdDeviation=".4"/></filter>""",
        vignette="rgba(0,0,0,0) 55%, rgba(0,0,0,.45) 100%", dim="#000000", flash="#ffffff",
        css="""
  .ph .inner { filter: grayscale(.2) contrast(1.05); }
  .ph { box-shadow: 0 18px 50px rgba(0,0,0,.55); }
  .cap { position:absolute; color: var(--fg); font-family: var(--font-ui); font-size: 28px; font-weight: 500; letter-spacing: 1px; white-space: nowrap; padding-left: 18px; }
  .cap .bar { position:absolute; left:0; top:4px; bottom:4px; width:5px; background: var(--red); }
  .quote { position:absolute; color: var(--fg); font-family: var(--font-big); font-size: 40px; font-weight: 700; white-space: nowrap; text-shadow: 0 2px 16px rgba(0,0,0,.8); }
  #big { color: var(--fg); font-family: var(--font-big); }
""",
        torn=False, photo_ease="power2.out", light=False, pill=("#ebe8e1", "#111315"), ring="#ffffff"),
}


def _lecture(mode):
    """lecture-<mode> (light, dark, story, finance, food) from themes/lecture.json (one file)."""
    t = LECTURE[mode]
    light = t.get("light", mode == "light")
    shadow = "rgba(30,40,70,.18)" if light else "rgba(0,0,0,.6)"
    return dict(
        vars=(f"--bg:{t['bg']}; --bg-solid:{t['bg']}; --fg:{t['fg']}; --red:{t['accent']}; --must:{t['accent2']}; --hi:{t['hi']}; "
              f"--strip:{t['panel']}; --muted:{t['muted']}; --font-big:'{t['font_big']}'; --font-ui:'{t['font_ui']}'; "
              + _rise_vars("red")),
        paper=(f"background: linear-gradient(180deg, {t['panel']} 0%, {t['bg']} 100%);" if light else
               f"background: radial-gradient(ellipse at 50% 40%, {t['panel']} 0%, {t['bg']} 70%);"),
        # light: a clean flat ground; dark: a faint field of small stars (screenshots 8, 9)
        texture="" if light else """<pattern id="stars" width="173" height="149" patternUnits="userSpaceOnUse">
      <circle cx="21" cy="33" r="1.1" fill="#fff" opacity=".35"/><circle cx="97" cy="12" r=".8" fill="#fff" opacity=".25"/>
      <circle cx="140" cy="88" r="1" fill="#fff" opacity=".3"/><circle cx="58" cy="121" r=".7" fill="#fff" opacity=".2"/></pattern>
    <rect width="1920" height="1080" fill="url(#stars)"/>""",
        filters=f"""<filter id="bleed" {U}><feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="{shadow}" flood-opacity="1"/></filter>
      <filter id="wash" {U}><feGaussianBlur stdDeviation="16"/></filter>
      <filter id="brush" {U}><feGaussianBlur stdDeviation=".3"/></filter>""",
        vignette="rgba(0,0,0,0) 70%, rgba(20,30,60,.10) 100%" if light else "rgba(0,0,0,0) 55%, rgba(0,0,0,.5) 100%",
        dim=t["dim"], flash="#ffffff",
        css=f"""
  .ph {{ border-radius: 18px; overflow: hidden; box-shadow: 0 14px 40px {shadow}; }}
  .ph .inner {{ filter: none; }}
  .cap, .quote {{ position:absolute; background: var(--strip); color: var(--fg); font-family: var(--font-ui); font-weight: 700;
                 padding: 10px 22px; border-radius: 999px; white-space: nowrap; box-shadow: 0 6px 18px {shadow}; }}
  .cap {{ font-size: 30px; letter-spacing: 1px; }}
  .cap .bar {{ display:none; }}
  .quote {{ font-family: var(--font-big); font-size: 40px; font-weight: 800; border-radius: 14px; }}
  #big {{ color: var(--fg); font-family: var(--font-big); }}
  #term .main, #label .main {{ background: var(--strip); padding: 6px 18px; border-radius: 12px; display:inline-block; box-shadow: 0 6px 18px {shadow}; }}
""",
        torn=False, photo_ease="power2.out", light=light,
        # keyword pill (doc_cut "pills"): fill, text
        pill=(t["fg"], t["panel"]) if light else (t["panel"], t["fg"]),
        ring=t["ring"])   # the side host frame's outline


LECTURE = json.loads((Path(__file__).resolve().parents[1] / "themes/lecture.json").read_text(encoding="utf-8"))


def _rise_vars(rise):
    """--up / --down for charts (bars "dir"): rise "red" = Taiwan, China, Japan (up is red), "green" = US (up is green)."""
    if rise not in ("red", "green"):
        raise ValueError(f'rise must be "red" or "green": {rise!r}')
    c = LECTURE["_rise"]
    return f"--up:{c[rise]}; --down:{c['green' if rise == 'red' else 'red']};"


for _mode in (k for k in LECTURE if not k.startswith("_")):   # light, dark, then the topic palettes (story, finance, food)
    CODE_THEMES[f"lecture-{_mode}"] = _lecture(_mode)


# Styled themes (themes/styles.json): a palette like lecture.json's, plus a shape and a ground picked by name from the
# presets below, plus the VE look their VE shots use. A theme changes all three layers, not only its colours.
STYLES = json.loads((Path(__file__).resolve().parents[1] / "themes/styles.json").read_text(encoding="utf-8"))
_GRAIN = """<filter id="fib"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="2"/>
      <feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 %s 0"/></filter>
    <rect width="1920" height="1080" filter="url(#fib)"/>"""
# ground: (paper css, texture svg, vignette); t = the palette
GROUNDS = {
    "warm-grain": lambda t: (f"background: radial-gradient(ellipse at 50% 40%, {t['panel']} 0%, {t['bg']} 75%);", _GRAIN % ".06",
                             "rgba(0,0,0,0) 50%, rgba(0,0,0,.55) 100%"),
    "grid": lambda t: (f"background: linear-gradient(180deg, {t['panel']} 0%, {t['bg']} 100%);",
                       f"""<pattern id="grid" width="80" height="80" patternUnits="userSpaceOnUse">
      <path d="M 80 0 L 0 0 0 80" fill="none" stroke="{t['fg']}" stroke-width="1" opacity=".06"/></pattern>
    <rect width="1920" height="1080" fill="url(#grid)"/>""", "rgba(0,0,0,0) 60%, rgba(0,0,0,.4) 100%"),
    "paper-halftone": lambda t: (f"background: {t['bg']};", f"""<filter id="fib"><feTurbulence type="fractalNoise" baseFrequency="0.7" numOctaves="3" seed="2"/>
      <feColorMatrix values="0 0 0 0 .30  0 0 0 0 .22  0 0 0 0 .12  0 0 0 .16 0"/></filter>
    <rect width="1920" height="1080" filter="url(#fib)"/>
    <pattern id="ht" width="9" height="9" patternUnits="userSpaceOnUse"><circle cx="4.5" cy="4.5" r="1.3" fill="{t['fg']}" opacity=".08"/></pattern>
    <rect width="1920" height="1080" fill="url(#ht)"/>""", "rgba(0,0,0,0) 62%, rgba(70,45,15,.25) 100%"),
    "flat": lambda t: (f"background: {t['bg']};", "", "rgba(0,0,0,0) 75%, rgba(40,30,30,.06) 100%"),
    "dark-vignette": lambda t: (f"background: radial-gradient(ellipse at 50% 45%, {t['panel']} 0%, {t['bg']} 55%, #000 100%);",
                                _GRAIN % ".05", "rgba(0,0,0,0) 40%, rgba(0,0,0,.7) 100%"),
}
# shape: css for cards, captions, quotes, photos and the burst word; plus the keyword pill (fill, text) and the svg
# dot shadow. Cards are .card blocks (scenes' boxes), --strip is the palette's panel.
SHAPES = {
    "gold-frame": lambda t, sh: (f"""
  .card {{ border: 2px solid var(--red); border-radius: 0; outline: 1px solid {t['accent']}55; outline-offset: 7px; }}
  .ph {{ border: 2px solid var(--red); box-shadow: 0 18px 50px {sh}; }}
  .cap, .quote {{ position:absolute; color: var(--fg); font-family: var(--font-ui); font-weight: 600; padding: 6px 4px;
                 border-bottom: 2px solid var(--red); white-space: nowrap; }}
  .cap {{ font-size: 30px; letter-spacing: 3px; }} .cap .bar {{ display:none; }}
  .quote {{ font-family: var(--font-big); font-size: 40px; font-weight: 700; }}
  #big {{ color: var(--red); font-family: var(--font-big); }}
  #term .main, #label .main {{ border-bottom: 2px solid var(--red); padding: 4px 10px; display:inline-block; }}
""", (t["accent"], t["bg"]), f'<feDropShadow dx="0" dy="6" stdDeviation="8" flood-color="{sh}" flood-opacity="1"/>'),
    "news-bar": lambda t, sh: (f"""
  .card {{ border-left: 10px solid var(--red); border-radius: 0; box-shadow: 0 10px 24px {sh}; }}
  .ph {{ box-shadow: 0 14px 40px {sh}; outline: 4px solid var(--fg); }}
  .cap, .quote {{ position:absolute; background: var(--red); color: var(--bg); font-family: var(--font-ui); font-weight: 900;
                 padding: 8px 18px; white-space: nowrap; }}
  .cap {{ font-size: 30px; letter-spacing: 1px; }} .cap .bar {{ display:none; }}
  .quote {{ background: var(--strip); color: var(--fg); border-left: 10px solid var(--red); font-size: 40px; }}
  #big {{ color: var(--fg); font-family: var(--font-big); }}
  #term .main, #label .main {{ background: var(--red); color: var(--bg); padding: 6px 18px; display:inline-block; }}
""", (t["accent"], t["bg"]), f'<feDropShadow dx="0" dy="6" stdDeviation="6" flood-color="{sh}" flood-opacity="1"/>'),
    "offset-print": lambda t, sh: (f"""
  .card {{ border: 4px solid var(--fg); border-radius: 0; box-shadow: 10px 10px 0 var(--red); }}
  .ph {{ border: 4px solid var(--fg); box-shadow: 12px 12px 0 var(--must); }}
  .ph .inner {{ filter: sepia(.35) contrast(1.1); }}
  .cap, .quote {{ position:absolute; background: var(--strip); color: var(--fg); font-family: var(--font-ui); font-weight: 900;
                 padding: 8px 18px; border: 3px solid var(--fg); box-shadow: 6px 6px 0 var(--red); white-space: nowrap; }}
  .cap {{ font-size: 30px; }} .cap .bar {{ display:none; }}
  .quote {{ font-family: var(--font-big); font-size: 40px; }}
  #big {{ color: var(--red); font-family: var(--font-big); text-shadow: 8px 8px 0 var(--fg); }}
  #term .main, #label .main {{ background: var(--strip); border: 3px solid var(--fg); padding: 6px 18px; display:inline-block; }}
""", (t["fg"], t["panel"]), f'<feDropShadow dx="5" dy="5" stdDeviation="0" flood-color="{t["accent"]}" flood-opacity="1"/>'),
    "rule": lambda t, sh: (f"""
  .card {{ border-radius: 0; border-top: 3px solid var(--fg); border-bottom: 1px solid var(--muted); box-shadow: none; }}
  .ph {{ box-shadow: 0 10px 30px {sh}; }}
  .cap, .quote {{ position:absolute; background: var(--strip); color: var(--muted); font-family: var(--font-ui); font-weight: 500;
                 font-style: italic; padding: 6px 14px; white-space: nowrap; }}
  .cap {{ font-size: 28px; letter-spacing: 2px; }} .cap .bar {{ display:none; }}
  .quote {{ font-family: var(--font-big); font-style: normal; color: var(--fg); font-size: 40px; border-top: 3px solid var(--fg); }}
  #big {{ color: var(--fg); font-family: var(--font-big); }}
  #term .main, #label .main {{ border-top: 3px solid var(--fg); padding: 6px 10px; display:inline-block; }}
""", (t["fg"], t["panel"]), f'<feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="{sh}" flood-opacity="1"/>'),
    "glow": lambda t, sh: (f"""
  .card {{ border-radius: 0; box-shadow: 0 0 70px rgba(0,0,0,.65); text-shadow: 0 0 22px {t['fg']}40; }}
  .ph {{ box-shadow: 0 30px 80px rgba(0,0,0,.75); }}
  .ph .inner {{ filter: contrast(1.08) saturate(.85); }}
  .cap, .quote {{ position:absolute; color: var(--fg); font-family: var(--font-ui); font-weight: 400; padding: 6px 4px;
                 letter-spacing: 4px; text-shadow: 0 2px 18px rgba(0,0,0,.9); white-space: nowrap; }}
  .cap {{ font-size: 28px; }} .cap .bar {{ display:none; }}
  .quote {{ font-family: var(--font-big); font-size: 40px; font-weight: 600; }}
  #big {{ color: var(--fg); font-family: var(--font-big); text-shadow: 0 0 40px {t['accent']}99; }}
  #term .main, #label .main {{ letter-spacing: 6px; text-shadow: 0 0 24px {t['accent']}88; }}
""", (t["panel"], t["fg"]), f'<feGaussianBlur stdDeviation="3" result="g"/><feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge>'),
}


def _styled(name):
    """A styled theme from themes/styles.json: palette + SHAPES[shape] + GROUNDS[ground]."""
    t = STYLES[name]
    light = t["light"]
    sh = "rgba(30,40,70,.18)" if light else "rgba(0,0,0,.6)"
    paper, texture, vignette = GROUNDS[t["ground"]](t)
    css, pill, bleed = SHAPES[t["shape"]](t, sh)
    return dict(
        vars=(f"--bg:{t['bg']}; --bg-solid:{t['bg']}; --fg:{t['fg']}; --red:{t['accent']}; --must:{t['accent2']}; --hi:{t['hi']}; "
              f"--strip:{t['panel']}; --muted:{t['muted']}; --font-big:'{t['font_big']}'; --font-ui:'{t['font_ui']}'; "
              + _rise_vars("red")),
        paper=paper, texture=texture,
        filters=f"""<filter id="bleed" {U}>{bleed}</filter>
      <filter id="wash" {U}><feGaussianBlur stdDeviation="16"/></filter>
      <filter id="brush" {U}><feGaussianBlur stdDeviation=".3"/></filter>""",
        vignette=vignette, dim=t["dim"], flash="#ffffff", css=css,
        torn=False, photo_ease="power2.out", light=light, pill=pill, ring=t["ring"])


for _name in (k for k in STYLES if not k.startswith("_")):
    CODE_THEMES[_name] = _styled(_name)


VE_THEMES = {
    # v1 水墨（已退役，留作對照）
    "ink": dict(
        medium="traditional Chinese ink-wash painting on cream rice paper", image_type="other",
        style=("Rendered as a traditional Chinese ink-wash painting (shuimo) on aged cream rice paper: layered ink tones from deep "
               "black to pale grey wash, dry-brush strokes with flying-white texture, soft bleeding edges, visible rice-paper fibre, "
               "and vast untouched paper as negative space. The palette is only ink black, grey washes and warm paper cream. "
               "No text, calligraphy, seal stamps, signature, border, or watermark, 16:9."),
        look="ink tones, dry-brush texture, rice-paper fibre and empty paper space of the opening frame. Brushwork stays stable "
             "rather than boiling, crawling or spreading",
        neg="text, calligraphy, seal stamps, red color, photorealistic textures, 3D rendering, boiling or crawling ink"),
    # ① VOX 拼貼：官方四段式（場景／風格／色彩律／closer）
    "collage": dict(
        medium="hand-cut documentary paper collage", image_type="other",
        style=("Hand-cut documentary paper collage: people and objects are halftone photo cutouts with rough scissor-cut edges, "
               "torn newsprint and kraft-paper layers, strips of masking tape, visible print grain and paper fibre, matte flat "
               "documentary lighting with soft cutout shadows, generous empty paper as negative space. "
               "Palette law: desaturated tan, ink black and halftone grey, with exactly one hot red accent and a restrained "
               "mustard yellow secondary. "
               "NOT digital illustration, NOT cartoon, NOT 3D render, NOT glossy, no gradients, no clutter, no watermark, no logos, "
               "no text. Premium Vox-style investigative documentary collage, 16:9, ultra-detailed, 8K."),
        look="cutout shapes, halftone dots, torn paper layers, tape strips and palette of the opening frame, with rigid paper "
             "physics and small stop-motion settles; print grain and soft layered shadows stay stable",
        neg="text, letters, numbers, logos, glossy or 3D look, gradients, faces with detailed features, warping paper"),
    # ② 紀錄片寫實
    "live": dict(
        medium="cinematic live-action documentary footage", image_type="photorealistic",
        style=("Cinematic live-action documentary film still, realistic human identity, natural color like an unedited RAW "
               "frame, soft overcast daylight, fine sensor grain, shallow depth of field, restrained muted palette, NO CGI or "
               "3D-render look, clean frame with no text, signs, captions or watermark, 16:9 aspect ratio."),
        look="natural light, muted color, film grain and depth of field of the opening frame; faces, hands and objects stay "
             "anatomically stable",
        neg="text, signs, captions, logos, CGI or 3D-render look, warped hands, additional people"),
    # ③ 教學片扁平插畫（lecture-light／lecture-dark 預設；色彩律亮暗共用，VE 畫面放在主題的底色與框上）
    "flat": dict(
        medium="clean flat vector explainer illustration", image_type="other",
        style=("Clean flat vector explainer illustration: simple geometric shapes, soft rounded forms, solid colour fills with "
               "at most a gentle two-tone shade, thin even outlines, friendly simplified people with minimal facial detail, "
               "uncluttered composition with generous empty space around one clear subject. "
               "Palette law: soft neutral off-white and cool light grey, deep navy for lines, with exactly one calm blue "
               "accent and a restrained warm yellow secondary. "
               "NOT photorealistic, NOT 3D render, NOT paper collage, no halftone, no texture noise, no clutter, no watermark, "
               "no logos, no text. Modern educational explainer video style, 16:9, crisp clean edges."),
        look="flat shapes, solid fills, thin outlines and palette of the opening frame; shapes move as rigid flat layers and "
             "keep crisp edges",
        neg="text, letters, numbers, logos, photorealistic textures, 3D render, halftone, paper texture, warping shapes"),
}


def ve_look(doc, theme):
    """Which VE_THEMES entry a theme's VE shots use (doc.json "ve_look" overrides). It names the VE folder ve_<look>/, so
    switching lecture-light ↔ lecture-dark reuses the same clips: the VE look is shared by both."""
    return doc.get("ve_look") or ("flat" if theme.startswith("lecture-") else STYLES[theme]["ve"] if theme in STYLES else theme)


# Era palettes for collage (2026-10-25): doc.json "palette": "<時代>" re-inks the code shots and swaps the VE palette
# law, so a series can mark a new stretch of history without changing its look. The cut, paper and tape stay collage.
# Keys are the eight Old Testament eras and three New Testament eras of the series; 原初 and 族長 keep the plain collage colours (episodes 1-6 shipped so).
# (bg, fg, accent, secondary, strip, paper-fibre tint RGB 0-1, tape RGB, VE palette law)
PALETTES = {
    "原初": None,
    "族長": None,
    "出埃及與曠野": ("#d9b97c", "#22180e", "#1d7a80", "#b4502a", "#f6ecd2", (.40, .26, .08), "180,80,42",
                 "warm ochre papyrus and sand tones, ink black and halftone grey, with exactly one turquoise faience accent "
                 "and a restrained terracotta secondary"),
    "征服與士師": ("#c9c29a", "#1f1f14", "#a23a1e", "#4f6b2e", "#f3efdc", (.28, .28, .10), "79,107,46",
               "olive khaki and dry earth tones, ink black and halftone grey, with exactly one rust red accent "
               "and a restrained olive green secondary"),
    "聯合王國": ("#c2b29b", "#1c1612", "#5b2a6e", "#c9a23a", "#f5efe2", (.32, .24, .16), "201,162,58",
             "cedar and sandstone tones, ink black and halftone grey, with exactly one royal purple accent "
             "and a restrained gold secondary"),
    "分裂王國": ("#c3a68a", "#1e140e", "#23415f", "#8e2b2b", "#f4ece2", (.38, .24, .14), "142,43,43",
             "fired clay and rust tones, ink black and halftone grey, with exactly one deep navy accent "
             "and a restrained oxblood secondary"),
    "被擄": ("#b8c0c8", "#16191d", "#b23a26", "#2c4f94", "#eef0f2", (.16, .20, .28), "44,79,148",
           "cool ash grey and slate blue paper, ink black and halftone grey, with exactly one brick red accent "
           "and a restrained lapis blue secondary"),
    "歸回": ("#cfd6c2", "#1a1f18", "#c8642a", "#3f6e5a", "#f2f4ec", (.22, .28, .20), "63,110,90",
           "pale sage and dawn tones, ink black and halftone grey, with exactly one dawn orange accent "
           "and a restrained deep teal secondary"),
    # New Testament eras (2026-11-07): 彌賽亞降臨 approved by the user (ground and sky must be
    # unnatural flat paper colours or VE renders a photo); 教會初期 and 末世盼望 not yet sampled
    "彌賽亞降臨": ("#d6c6c0", "#1d1914", "#a3232f", "#3b3170", "#f4eeec", (.30, .24, .24), "59,49,112",
              "desaturated pale ash-rose paper and halftone grey tones, ink black, with exactly one crimson accent "
              "and a restrained flat deep indigo-violet paper secondary"),
    "教會初期": ("#d6c9a6", "#1c1812", "#c4512a", "#2a4f7a", "#f5efdc", (.32, .26, .12), "42,79,122",
             "desaturated pale parchment and grey road-stone tones, ink black and halftone grey, with exactly one flame vermilion accent "
             "and a restrained Aegean blue secondary"),
    "末世盼望": ("#d9d6cc", "#17171a", "#1f7a55", "#b08a2e", "#f4f2ea", (.24, .24, .22), "176,138,46",
             "desaturated pearl white and pale stone tones, ink black and halftone grey, with exactly one emerald green accent "
             "and a restrained burnished gold secondary"),
}
_COLLAGE_LAW = ("desaturated tan, ink black and halftone grey, with exactly one hot red accent and a restrained mustard yellow "
                "secondary")
_COLLAGE_TINT = "0 0 0 0 .30  0 0 0 0 .22  0 0 0 0 .12"


def _palette(theme, palette):
    if palette is None:
        return None
    if palette not in PALETTES:
        raise ValueError(f"palette must be one of {', '.join(PALETTES)}")
    if theme != "collage":
        raise ValueError("palette only applies to the collage theme")
    return PALETTES[palette]


def code_theme(theme, palette=None, rise=None):
    """CODE_THEMES[theme], re-inked for an era palette, or with green as the rising colour (a copy; the table itself is
    never changed). rise only applies to lecture-* and the styles.json themes (their charts default to red up)."""
    th, p = dict(CODE_THEMES[theme]), _palette(theme, palette)
    if rise is not None:
        if not (theme.startswith("lecture-") or theme in STYLES):
            raise ValueError("rise only applies to the lecture-* and styles.json themes")
        th["vars"] = th["vars"].replace(_rise_vars("red"), _rise_vars(rise))
    if p:
        bg, fg, red, must, strip, tint, tape, _ = p
        th["vars"] = (f"--bg:{bg}; --fg:{fg}; --red:{red}; --must:{must}; --hi:{strip}; --strip:{strip}; "
                      "--font-big:'Noto Serif TC'; --font-ui:'Noto Sans TC';")
        th["texture"] = th["texture"].replace(_COLLAGE_TINT, "0 0 0 0 %.2f  0 0 0 0 %.2f  0 0 0 0 %.2f" % tint)
        th["css"] = th["css"].replace("214,162,39", tape)
    return th


def ve_theme(theme, palette=None):
    """VE_THEMES[theme] with the era's palette law in place of the collage one (a copy)."""
    th, p = dict(VE_THEMES[theme]), _palette(theme, palette)
    if p:
        th["style"] = th["style"].replace(_COLLAGE_LAW, p[7])
    return th
