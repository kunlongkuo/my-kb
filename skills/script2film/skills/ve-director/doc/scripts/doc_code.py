"""Code beats → code_<theme>/<id>/index.html (HyperFrames, GSAP) → code_<theme>/<id>.mp4.

  python3 doc_code.py <project>/doc.json [--theme=collage|live] [--render] [B6 ...]
A code beat names a template from ../scenes (the table in ../README.md) and its params; any beat can add photos /
label / quote layers (see lib/lib.js overlays). Time params are a phrase from the beat's own narration (the shot
starts when that phrase starts being spoken), a number of seconds, or {"w", "d", "f"}.
"veil": [in, out] fades from / to the background colour at the shot's edges (use it next to VE shots, not between
consecutive code shots that continue one board).
"bg_video": {"src", "tone": "light"|"dark", "in"} puts a VE live-action clip under the scene (see bg_video below).
"""
import json, re, shutil, subprocess, sys
from pathlib import Path

from doc_common import SKILL_DOC, asset, gsap_file, hyperframes, load, log_tail, read_beats, read_json, tokens
from doc_credits import credit_groups
from doc_cutout import fg_auto
from doc_themes import CODE_THEMES, code_theme

TAIL = 0.2
# side.beats (a host frame on the right, lecture-style D2): the whole scene layer shrinks into x 40-1220, centred vertically.
# side.zoom (1.0-1.5, default 1.0) enlarges it around the left area's centre (x 630): words read small at 1180/1920
# (2026-10-28 lecture pilot: 「左邊的搭配解說字，可以都同步大一些」); scenes keep their words near the canvas centre, so
# a moderate zoom stays left of the host frame.
SIDE_ZOOM_MIN, SIDE_ZOOM_MAX = 1.0, 1.5


def stage_left(doc):
    k = 1180 / 1920 * max(SIDE_ZOOM_MIN, min(float(doc.get("side", {}).get("zoom", 1.0)), SIDE_ZOOM_MAX))
    return "#content { z-index: 5; transform: translateX(%.1fpx) scale(%.4f); transform-origin: 0 50%%; }" % (630 - 960 * k, k)


# screen_step (lecture-screen D2): where the recorded 1920 x 1080 screen sits in the frame
SCREEN_RECT = {"browser": [160, 118, 1600, 900], "none": [0, 0, 1920, 1080]}   # browser: a 56 px window bar above it
# with the host in the lower-left circle (pip, x 55-365): the window moves right of it (T4 preview: it covered the page)
SCREEN_RECT_PIP = [380, 146, 1500, 844]
NAV_HOLD = 0.8   # a click that opens another page: its mark goes 0.8 s after the click, not at the next step
SCREEN_CLIP_MAX = 10.0


TIME_KEYS = {"sigh", "pulse", "appear", "hits", "word", "loop", "a", "b", "good", "bad", "revenge", "other", "attack", "forgive",
             "start", "pull", "far", "at", "cap_at", "accent_at", "caption_at", "w", "freeze",
             "a_at", "b_at", "merge_at", "sub_at", "hot_at", "title_at", "note_at", "to_at", "pan_at"}


def missing_triggers(params, beat, lang):
    """Every phrase a time parameter names must occur in the beat's own narration; otherwise the shot silently falls back
    to a fixed second and drifts off the voice."""
    words, bad = [t[0] for t in beat["tokens"]], []

    def found(phrase):
        q = tokens(phrase, lang)
        return any(words[i:i + len(q)] == q for i in range(len(words) - len(q) + 1))

    def walk(x, key=None):
        if isinstance(x, dict):
            for k, v in x.items():
                walk(v, k)
        elif isinstance(x, list):
            for v in x:
                walk(v, key)
        elif isinstance(x, str) and key in TIME_KEYS and not found(x):
            bad.append(f"{key}={x!r}")
    walk(params)
    return bad


def phrase_at(beat, v, lang):
    """Seconds from the beat's start for a time parameter (lib.js at()): number, phrase, or {"w", "d"}; None if not found."""
    if isinstance(v, (int, float)):
        return float(v)
    w, d = (v, 0.0) if isinstance(v, str) else (v.get("w"), float(v.get("d", 0)))
    words, q = [t[0] for t in beat["tokens"]], tokens(w or "", lang)
    hit = next((i for i in range(len(words) - len(q) + 1) if q and words[i:i + len(q)] == q), None)
    return None if hit is None else beat["tokens"][hit][1] + d


# Scenes that show nothing until their "at" (quote_card's card, stat_count's number): if that phrase sits in a later line of
# the beat, the whole first line plays over bare paper (once about 4 s).
EMPTY_UNTIL_AT = {"quote_card", "stat_count"}


def empty_first_line(doc, beat, spec):
    """'B19: at='我就是' comes in line 20 (4.3 s)' (doc line numbers) when the scene's first element waits past the beat's first line; else None."""
    at = spec.get("params", {}).get("at")
    if spec.get("scene") not in EMPTY_UNTIL_AT or not isinstance(at, (str, dict)) or len(beat["lines"]) < 2:
        return None
    n1 = len(tokens(doc["lines"][beat["lines"][0] - 1]["text"], doc["lang"]))
    t = phrase_at(beat, at, doc["lang"])
    if t is None or n1 >= len(beat["tokens"]) or t < beat["tokens"][n1][1]:
        return None
    return f"{beat['id']}: at={at!r} comes in line {beat['lines'][1]} ({t:.1f} s)"


# Longest wait, in seconds from the beat's start, before such a scene shows its first element when nothing else is on
# screen: measured on 15 episodes on 2026-11-15, the
# beats it lists that had nothing else on screen were all blank paper. It stops the render, and the start checklist
# runs the same test on the script with estimated timing (the fix costs nothing: change "at").
LEAD_MAX = 1.0


def late_first_element(doc, beat, spec):
    """'B48: at='當場說' comes 2.5 s into the beat' when an EMPTY_UNTIL_AT scene shows its first element later than LEAD_MAX
    and nothing else is on screen; else None. Something else on screen: a bg_video under the scene, the host in a side or
    round frame, or a "photos" still that comes in by LEAD_MAX. A quote card's own "photo" does not count: it enters
    with the card (quote_card.js). Cases empty_first_line already stops are not repeated here."""
    params = spec.get("params", {})
    at = params.get("at")
    if spec.get("scene") not in EMPTY_UNTIL_AT or at is None or empty_first_line(doc, beat, spec):
        return None
    t = phrase_at(beat, at, doc["lang"])
    if t is None or t <= LEAD_MAX or spec.get("bg_video"):   # phrase not in the beat: missing_triggers reports that
        return None
    if beat["id"] in (doc.get("side") or {}).get("beats", []) + (doc.get("pip") or {}).get("beats", []):
        return None
    for ph in params.get("photos") or []:
        ta = phrase_at(beat, ph.get("at", 0), doc["lang"])
        if ta is not None and ta <= LEAD_MAX:
            return None
    return f"{beat['id']}: at={at!r} comes {t:.1f} s into the beat"


def screen_media(P, doc, b, params, out, d):
    """screen_step: resolve each step's box (from the doc_screen log or given), cut the recording's clip to screen.mp4
    and return (the media element for the template's root, params with "_screen" for scenes/screen_step.js).
    Clip timing (lecture-screen D2): the shot shows the recording from clip[0]; without "clip" it is
    t(first step) - its phrase time, so the first click lands as the narration names it."""
    frame = params.get("frame", "browser")
    z = params.get("zoom")
    if z is not None and (isinstance(z, bool) or not isinstance(z, (int, float)) or z <= 1):
        sys.exit(f"✗ {b['id']}: screen_step zoom is the push-in scale, a number above 1 (e.g. 1.6): {z!r}")
    if frame not in SCREEN_RECT:
        sys.exit(f"✗ {b['id']}: screen_step frame must be one of {', '.join(SCREEN_RECT)}: {frame!r}")
    if b["id"] in doc.get("side", {}).get("beats", []):
        sys.exit(f"✗ {b['id']}: screen_step fills the frame; put the host in pip, not side")
    log = read_json(P / params["log"], "run doc_screen.py first")["steps"] if params.get("log") else []
    by_n = {s["n"]: s for s in log}
    pip = b["id"] in doc.get("pip", {}).get("beats", [])
    rx, ry, rw, rh = SCREEN_RECT_PIP if frame == "browser" and pip else SCREEN_RECT[frame]
    k = rw / 1920
    marks = []
    for s in params["steps"]:
        if "box" in s:
            box, t, nav = s["box"], None, False
        elif s.get("step") in by_n and by_n[s["step"]]["box"]:
            e = by_n[s["step"]]
            # a click that opens another page: the next logged step is on a new url (the click's own entry still
            # has the old one, navigation finishes after click() returns)
            after = by_n.get(s["step"] + 1, {}).get("url", e.get("url"))
            box, t, nav = e["box"], e["t"], e["do"] == "click" and after != e.get("url")
        else:
            sys.exit(f"✗ {b['id']}: screen_step step {s.get('n')} needs box, or log + step naming a click / type step")
        marks.append({"n": s["n"], "label": s["label"], "at": s["at"], "t": t, "nav": nav,
                      "box": [round(rx + box[0] * k, 1), round(ry + box[1] * k, 1), round(box[2] * k, 1), round(box[3] * k, 1)]})
    src = P / params["src"]
    if src.suffix.lower() == ".png":
        media = f'<img src="{params["src"]}" style="position:absolute;left:{rx}px;top:{ry}px;width:{rw}px;height:{rh}px;z-index:3">'
        clip = None
    else:
        clip = params.get("clip")
        if clip is None:
            first = marks[0]
            tau = phrase_at(b, first["at"], doc["lang"])
            if first["t"] is None or tau is None or first["t"] - tau < 0:
                sys.exit(f"✗ {b['id']}: screen_step: set clip explicitly: the recording starts after the narration reaches step "
                         f"{first['n']} (or that step has no logged time)")
            clip = [round(first["t"] - tau, 3), round(first["t"] - tau + b["duration"], 3)]
        if clip[1] - clip[0] > SCREEN_CLIP_MAX:
            sys.exit(f"✗ {b['id']}: screen_step clip is {clip[1] - clip[0]:.1f}s, at most {SCREEN_CLIP_MAX:.0f}s")
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{clip[0]:.3f}", "-i", str(src), "-t", f"{d:.3f}",
               "-vf", f"tpad=stop_mode=clone:stop_duration={d:.3f},fps=30", "-c:v", "libx264", "-crf", "14",
               "-pix_fmt", "yuv420p", "-an", str(out / "screen.mp4")]
        subprocess.run(cmd, check=True)
        media = (f'<video id="screen" class="clip" src="screen.mp4" muted playsinline data-start="0" data-duration="{d}" '
                 f'data-track-index="1" style="position:absolute;left:{rx}px;top:{ry}px;width:{rw}px;height:{rh}px;z-index:3"></video>')
    for m in marks:   # the shot second its mark leaves: a click that opens another page clears it soon after the click
        m["until"] = round(m["t"] - clip[0] + NAV_HOLD, 3) if m.pop("nav") and clip else None
    return media, {**params, "_screen": {"rect": [rx, ry, rw, rh], "frame": frame, "url_text": params.get("url_text", ""),
                                         "clip": clip, "marks": marks}}


VE_HOLD = 2.2       # ve_annotate freeze: telestrator §3 holds 1.8-2.4 s; the long end leaves time for a Chinese label
VE_HOLD_WARN = 2.5  # longer than ~2.5 s "needs a second action inside it" (telestrator §3)


def ve_media(P, doc, b, params, out, d):
    """ve_annotate: cut the VE clip into vean.mp4 (play to the freeze, the same frame held `hold` s, play on, last frame
    held to the end) and return (the video element, params with "_ve" for scenes/ve_annotate.js)."""
    tf, hold, t_in = phrase_at(b, params.get("freeze"), doc["lang"]), float(params.get("hold", VE_HOLD)), float(params.get("in", 0))
    if tf is None or tf <= 0:
        sys.exit(f"✗ {b['id']}: ve_annotate freeze must be a phrase in the beat or seconds > 0 (play first, then freeze)")
    if tf + hold > d:
        sys.exit(f"✗ {b['id']}: ve_annotate freeze {tf:.2f}s + hold {hold:.2f}s runs past the beat ({d:.2f}s)")
    if isinstance(params.get("note"), list):
        sys.exit(f"✗ {b['id']}: ve_annotate takes one note per freeze (telestrator: one freeze, one finding)")
    if hold > VE_HOLD_WARN:
        print(f"  ! {b['id']}: hold {hold:.1f}s > {VE_HOLD_WARN}s: give the freeze a second action or shorten it")
    fc = (f"[0:v]scale=1920:1080,setsar=1,split[s1][s2];"
          f"[s1]trim=start={t_in:.3f}:duration={tf:.3f},setpts=PTS-STARTPTS[a];"
          f"[s2]trim=start={t_in + tf:.3f},setpts=PTS-STARTPTS,tpad=start_mode=clone:start_duration={hold:.3f}[b];"
          f"[a][b]concat=n=2:v=1:a=0,fps=30,tpad=stop_mode=clone:stop_duration={d:.3f}[v]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(P / params["src"]), "-filter_complex", fc, "-map", "[v]",
                    "-t", f"{d:.3f}", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", "-an", str(out / "vean.mp4")],
                   check=True)
    media = (f'<video id="vean" class="clip" src="vean.mp4" muted playsinline data-start="0" data-duration="{d}" '
             f'data-track-index="1" style="position:absolute;left:0;top:0;width:1920px;height:1080px;z-index:3"></video>')
    return media, {**params, "_ve": {"freeze": round(tf, 3), "hold": hold}}


def page_value(out, expr):
    """Evaluate expr in the built page (out/index.html) in a headless browser, once the scene is built (window.__built:
    the template builds it after its fonts load); the GSAP timeline is paused, so every time a scene computed is there."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        pg = br.new_page(viewport={"width": 1920, "height": 1080})
        pg.goto((out / "index.html").resolve().as_uri(), wait_until="load")
        pg.evaluate("window.__built && window.__built.catch(() => {})")   # the template builds the scene once its fonts are in
        v = pg.evaluate(expr)
        br.close()
    return v


def read_marks(out, dst):
    """The boxes screen_step.js actually drew (window.__marks) → dst, read from the built page in a headless browser
    (lecture-screen T2: the alignment check reads what was drawn, not what was asked for)."""
    dst.write_text(json.dumps(page_value(out, "window.__marks"), ensure_ascii=False, indent=1), encoding="utf-8")


def read_sfx(out, dst):
    """The sound marks the scene made (window.__sfx: [{kind, t}], t in seconds from the beat's start) → dst, for doc_sfx.py.
    Rewritten on every build, so it always matches the page."""
    dst.write_text(json.dumps(page_value(out, "window.__sfx || []"), ensure_ascii=False, indent=1), encoding="utf-8")


FLOW_LOOKS = ("web", "pipe", "streams", "lanes")
FLOW_ICONS = ("laptop", "ai", "container", "stamp", "chain", "wallet", "target", "lock", "shield", "coin")


RELATION_KINDS = ("tree", "line", "dash", "arrow")
RELATION_GAP = 8   # px of clear space two cards need between them (the cards are tilted up to 1.2°)


def relation_overlaps(cards):
    """One line per relation card that runs off the frame and per two cards closer than RELATION_GAP;
    cards = [[id, left, top, width, height]] as the built page measured them (window.__relcards). 2026-11-17: three long
    English labels in one p.rows row were drawn on top of each other and nothing stopped it; relation.js now re-spreads such
    a row by the cards' widths, and this catches what still does not fit (a row wider than the frame, cards placed by x / y).
    Measured the same day on the 72 relation beats of earlier episodes (pictures left out): it stops 4, all with cards placed
    by x / y and a long scripture line as the label; the two looked at in their published films
    do run off the frame and cover each other."""
    out = [f"{a} runs off the frame" for a, x, _, w, _ in cards if x < 0 or x + w > 1920]
    for i, (a, ax, ay, aw, ah) in enumerate(cards):
        for c, cx, cy, cw, ch in cards[i + 1:]:
            ox = min(ax + aw, cx + cw) - max(ax, cx) + RELATION_GAP
            oy = min(ay + ah, cy + ch) - max(ay, cy) + RELATION_GAP
            if ox > 0 and oy > 0:
                out.append(f"{a} and {c} overlap by {round(min(ox, oy))} px")
    return out


def relation_params(P, b, params):
    """relation (scenes/relation.js): unique node ids, each placed by x / y inside the frame (subtitles below) or by p.rows,
    pictures that exist in the project, links of a known kind between two different nodes, a focus on nodes that exist,
    look left out or "board"."""
    bid, nodes, rows = b["id"], params.get("nodes") or [], params.get("rows") or []
    if params.get("look", "board") != "board":
        sys.exit(f"✗ {bid}: relation look must be \"board\" or left out: {params['look']!r}")
    if len(nodes) < 2:
        sys.exit(f"✗ {bid}: relation needs at least 2 nodes")
    ids = [n.get("id") for n in nodes]
    if None in ids or len(set(ids)) != len(ids):
        sys.exit(f"✗ {bid}: relation node ids must be given and unique: {ids}")
    in_rows = [i for r in rows for i in r]
    if len(set(in_rows)) != len(in_rows) or any(i not in ids for i in in_rows):
        sys.exit(f"✗ {bid}: relation rows must name each node id once: {rows}")
    for n in nodes:
        if not n.get("label"):
            sys.exit(f"✗ {bid}: relation node {n['id']} needs a label")
        x, y = n.get("x"), n.get("y")
        if x is None and y is None:
            if n["id"] not in in_rows:
                sys.exit(f"✗ {bid}: relation node {n['id']} needs x / y or a place in rows")
        elif not (isinstance(x, (int, float)) and isinstance(y, (int, float)) and 120 <= x <= 1800 and 120 <= y <= 820):
            sys.exit(f"✗ {bid}: relation node {n['id']} needs x 120-1800 and y 120-820 (subtitles below): {x!r}, {y!r}")
        if n.get("src") and not (P / n["src"]).is_file():
            sys.exit(f"✗ {bid}: relation node {n['id']} src not found in the project: {n['src']!r}")
    links = params.get("links") or []
    if not links:
        sys.exit(f"✗ {bid}: relation needs at least 1 link")
    for k, l in enumerate(links):
        if l.get("from") not in ids or l.get("to") not in ids or l.get("from") == l.get("to"):
            sys.exit(f"✗ {bid}: relation link {k} must join two different nodes by id: {l.get('from')!r} → {l.get('to')!r}")
        if l.get("kind", "line") not in RELATION_KINDS:
            sys.exit(f"✗ {bid}: relation link {k} kind must be one of {', '.join(RELATION_KINDS)}: {l.get('kind')!r}")
    foc = params.get("focus")
    if foc is not None and (not foc.get("ids") or any(i not in ids for i in foc["ids"])):
        sys.exit(f"✗ {bid}: relation focus.ids must name existing nodes: {foc.get('ids')!r}")


def flow_params(P, b, params):
    """flow (scenes/flow.js): a known look, unique node ids inside the frame, an icon it can draw or a picture in the project,
    and links (and the shutter) that point at nodes that exist. Stops on the first problem."""
    bid, look = b["id"], params.get("look", "web")
    if look not in FLOW_LOOKS:
        sys.exit(f"✗ {bid}: flow look must be one of {', '.join(FLOW_LOOKS)}: {look!r}")
    nodes = params.get("nodes") or []
    if len(nodes) < 2:
        sys.exit(f"✗ {bid}: flow needs at least 2 nodes")
    ids = [n.get("id") for n in nodes]
    if None in ids or len(set(ids)) != len(ids):
        sys.exit(f"✗ {bid}: flow node ids must be given and unique: {ids}")
    for n in nodes:
        x, y = n.get("x"), n.get("y")
        if not (isinstance(x, (int, float)) and isinstance(y, (int, float)) and 80 <= x <= 1840 and 80 <= y <= 860):
            sys.exit(f"✗ {bid}: flow node {n['id']} needs x 80-1840 and y 80-860 (subtitles below): {x!r}, {y!r}")
        if n.get("src"):
            if not (P / n["src"]).is_file():
                sys.exit(f"✗ {bid}: flow node {n['id']} src not found in the project: {n['src']!r}")
        elif n.get("icon", "laptop") not in FLOW_ICONS:
            sys.exit(f"✗ {bid}: flow node {n['id']} icon must be one of {', '.join(FLOW_ICONS)}: {n.get('icon')!r}")
    links = params.get("links") or []
    if not links:
        sys.exit(f"✗ {bid}: flow needs at least 1 link")
    for k, l in enumerate(links):
        if l.get("from") not in ids or l.get("to") not in ids or l.get("from") == l.get("to"):
            sys.exit(f"✗ {bid}: flow link {k} must join two different nodes by id: {l.get('from')!r} → {l.get('to')!r}")
    blk = params.get("block")
    if blk is not None and not (isinstance(blk.get("link", 0), int) and 0 <= blk.get("link", 0) < len(links)):
        sys.exit(f"✗ {bid}: flow block.link must be a link index 0-{len(links) - 1}: {blk.get('link')!r}")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _index(v, n):
    return isinstance(v, int) and not isinstance(v, bool) and 0 <= v < n


LINE_COLORS = ("accent", "fg", "accent2", "up", "down")


def line_params(P, b, params):
    """line_chart (scenes/line_chart.js): 2-24 labels, 1-3 series of one value per
    label in a known colour, reveals that move forward through the points, at most 4 marks, a band from a point to a later one."""
    bid, labels, series = b["id"], params.get("labels") or [], params.get("series") or []
    if not (isinstance(labels, list) and 2 <= len(labels) <= 24):
        sys.exit(f"✗ {bid}: line_chart needs 2-24 labels: {len(labels) if isinstance(labels, list) else labels!r}")
    n = len(labels)
    if not (isinstance(series, list) and 1 <= len(series) <= 3):
        sys.exit(f"✗ {bid}: line_chart needs 1-3 series: {len(series) if isinstance(series, list) else series!r}")
    for k, s in enumerate(series):
        v = s.get("values")
        if not (isinstance(v, list) and len(v) == n and all(_num(x) for x in v)):
            sys.exit(f"✗ {bid}: line_chart series {k} values must be {n} numbers, one per label")
        if s.get("color", "accent") not in LINE_COLORS:
            sys.exit(f"✗ {bid}: line_chart series {k} color must be one of {', '.join(LINE_COLORS)}: {s.get('color')!r}")
    last = -1
    for r in params.get("reveal") or []:
        u = r.get("upto")
        if not (_index(u, n) and u > last):
            sys.exit(f"✗ {bid}: line_chart reveal upto must go up, each a point 0-{n - 1}: {u!r}")
        last = u
    marks = params.get("marks") or []
    if len(marks) > 4:
        sys.exit(f"✗ {bid}: line_chart takes at most 4 marks: {len(marks)}")
    for m in marks:
        if not (_index(m.get("i"), n) and _index(m.get("series", 0), len(series))):
            sys.exit(f"✗ {bid}: line_chart marks need i 0-{n - 1} and series 0-{len(series) - 1}: {m.get('i')!r}, {m.get('series', 0)!r}")
    band = params.get("band")
    if band is not None and not (_index(band.get("from"), n) and _index(band.get("to"), n) and band["from"] < band["to"]):
        sys.exit(f"✗ {bid}: line_chart band needs from < to, both points 0-{n - 1}: {band.get('from')!r}, {band.get('to')!r}")
    if "hot" in params and not _index(params["hot"], n):
        sys.exit(f"✗ {bid}: line_chart hot must be a point 0-{n - 1}: {params['hot']!r}")
    lo, hi = params.get("min"), params.get("max")
    if lo is not None and hi is not None and not (_num(lo) and _num(hi) and lo < hi):
        sys.exit(f"✗ {bid}: line_chart min must be below max: {lo!r}, {hi!r}")


PIE_SHOW = ("percent", "value")


def pie_params(P, b, params):
    """pie (scenes/pie.js): 2-6 items with a value above 0, a ring of 0-0.7, focus
    and hot on items that exist, a centre text only on a ring."""
    bid, items = b["id"], params.get("items") or []
    if not (isinstance(items, list) and 2 <= len(items) <= 6):
        sys.exit(f"✗ {bid}: pie needs 2-6 items: {len(items) if isinstance(items, list) else items!r}")
    for k, it in enumerate(items):
        if not it.get("label"):
            sys.exit(f"✗ {bid}: pie item {k} needs a label")
        if not (_num(it.get("value")) and it["value"] > 0):
            sys.exit(f"✗ {bid}: pie item {k} value must be a number above 0: {it.get('value')!r}")
    donut = params.get("donut", 0.55)
    if not (_num(donut) and 0 <= donut <= 0.7):
        sys.exit(f"✗ {bid}: pie donut must be 0-0.7 (0: a solid pie): {donut!r}")
    for f in params.get("focus") or []:
        if not _index(f.get("i"), len(items)):
            sys.exit(f"✗ {bid}: pie focus i must be an item 0-{len(items) - 1}: {f.get('i')!r}")
    if params.get("show", "percent") not in PIE_SHOW:
        sys.exit(f"✗ {bid}: pie show must be one of {', '.join(PIE_SHOW)}: {params.get('show')!r}")
    if params.get("center") is not None and donut == 0:
        sys.exit(f"✗ {bid}: pie center needs a ring (donut above 0)")
    if "hot" in params and not _index(params["hot"], len(items)):
        sys.exit(f"✗ {bid}: pie hot must be an item 0-{len(items) - 1}: {params['hot']!r}")


FORMULA_OPS = ("=", "+", "−", "×", "÷", "→", ">", "<")
CJK = re.compile(r"[⺀-鿿가-힯豈-﫿＀-￯]")   # same ranges as scenes/formula.js


def formula_size(terms, ops):
    """Font size of the formula row (D5): 1500 / (characters + 1.2 per operator), CJK 1 each, anything else 0.55, at most
    190. scenes/formula.js computes the same."""
    units = sum(1 if CJK.match(c) else 0.55 for t in terms for c in str(t.get("text", ""))) + 1.2 * len(ops)
    return min(190, int(1500 // units))


def formula_params(P, b, params):
    """formula (scenes/formula.js): 2-5 terms joined by one known operator each (one term only with a strike that rewrites it:
    「不是 A，而是 B」), focus and strike on terms that exist, a rewrite (strike "to") short enough to stay at 72 px or more,
    and a row short enough to stay at 72 px or more."""
    bid, terms, ops = b["id"], params.get("terms") or [], params.get("ops") or []
    rewrites = [s for s in params.get("strike") or [] if isinstance(s, dict) and "to" in s]
    lo = 1 if rewrites else 2
    if not (isinstance(terms, list) and lo <= len(terms) <= 5):
        sys.exit(f"✗ {bid}: formula needs 2-5 terms (1 only with a strike that has to): "
                 f"{len(terms) if isinstance(terms, list) else terms!r}")
    for k, t in enumerate(terms):
        if not str(t.get("text", "")).strip():
            sys.exit(f"✗ {bid}: formula term {k} needs text")
    if not (isinstance(ops, list) and len(ops) == len(terms) - 1):
        sys.exit(f"✗ {bid}: formula needs {len(terms) - 1} ops (one between each two terms): {ops!r}")
    for o in ops:
        if o not in FORMULA_OPS:
            sys.exit(f"✗ {bid}: formula operator must be one of {' '.join(FORMULA_OPS)}: {o!r}")
    for key in ("focus", "strike"):
        for f in params.get(key) or []:
            if not _index(f.get("i"), len(terms)):
                sys.exit(f"✗ {bid}: formula {key} i must be a term 0-{len(terms) - 1}: {f.get('i')!r}")
    if formula_size(terms, ops) < 72:
        sys.exit(f"✗ {bid}: formula too long: shorten the terms or split it into two beats")
    for r in rewrites:   # formula.js: min(row size × 0.8, 1600 / units)
        units = sum(1 if CJK.match(c) else 0.55 for c in str(r["to"]))
        if not str(r["to"]).strip() or 1600 // units < 72:
            sys.exit(f"✗ {bid}: formula strike to must be 1 to about 22 characters: {r['to']!r}")


def _span(v, n):
    """[first, last] item indexes inside 0..n-1 covering 2-6 items, or None."""
    if not (isinstance(v, list) and len(v) == 2 and all(isinstance(i, int) and not isinstance(i, bool) for i in v)):
        return None
    return v if 0 <= v[0] < v[1] < n and 2 <= v[1] - v[0] + 1 <= 6 else None


def timeline_params(P, b, params):
    """timeline (scenes/timeline.js): 2-6 dated items, or up to 12 with a window [first, last] of 2-6 items; from (the
    stretch shown first, before the line slides) is as long as the window; pan_at only with from; hot on an item."""
    bid, items = b["id"], params.get("items") or []
    win, frm = params.get("window"), params.get("from")
    top = 12 if win is not None else 6
    if not (isinstance(items, list) and 2 <= len(items) <= top):
        sys.exit(f"✗ {bid}: timeline needs 2-6 items (up to 12 with a window): "
                 f"{len(items) if isinstance(items, list) else items!r}")
    for k, it in enumerate(items):
        if not isinstance(it, dict) or not str(it.get("date", "")).strip():
            sys.exit(f"✗ {bid}: timeline item {k} needs a date")
    if win is not None and not _span(win, len(items)):
        sys.exit(f"✗ {bid}: timeline window must be [first, last] item indexes 0-{len(items) - 1} covering 2-6 items: {win!r}")
    if frm is not None:
        if win is None:
            sys.exit(f"✗ {bid}: timeline from needs a window (where the line slides to)")
        if not _span(frm, len(items)) or frm[1] - frm[0] != win[1] - win[0]:
            sys.exit(f"✗ {bid}: timeline from must be [first, last] item indexes covering as many items as the window: {frm!r}")
    if "pan_at" in params and frm is None:
        sys.exit(f"✗ {bid}: timeline pan_at needs from (the stretch the line slides from)")
    if params.get("hot") is not None and not _index(params["hot"], len(items)):
        sys.exit(f"✗ {bid}: timeline hot must be an item 0-{len(items) - 1}: {params['hot']!r}")


BREAKDOWN_OPS = ("+", "−", "×", "÷")


def breakdown_params(P, b, params):
    """breakdown (scenes/breakdown.js): a root, 2-5 parts each after the first
    joined by an operator, a second level of 2-3 under any part (at most 6 in all, wide enough: c = min(230, S / m) ≥ 150),
    no third level, focus on positions that exist ("1", "1.0")."""
    bid, root, parts = b["id"], params.get("root") or {}, params.get("parts") or []
    if not str(root.get("text", "")).strip():
        sys.exit(f"✗ {bid}: breakdown root needs text")
    if not (isinstance(parts, list) and 2 <= len(parts) <= 5):
        sys.exit(f"✗ {bid}: breakdown needs 2-5 parts: {len(parts) if isinstance(parts, list) else parts!r}")

    def ops(items, where):
        for k, it in enumerate(items):
            if not str(it.get("text", "")).strip():
                sys.exit(f"✗ {bid}: breakdown {where}{k} needs text")
            if k == 0 and "op" in it:
                sys.exit(f"✗ {bid}: breakdown {where}{k} is the first: no op")
            if k and it.get("op") not in BREAKDOWN_OPS:
                sys.exit(f"✗ {bid}: breakdown {where}{k} needs op, one of {' '.join(BREAKDOWN_OPS)}: {it.get('op')!r}")
    ops(parts, "part ")
    ids, total, s = {str(k) for k in range(len(parts))}, 0, min(520, 1500 / (len(parts) - 1))
    for k, pt in enumerate(parts):
        kids = pt.get("parts")
        if kids is None:
            continue
        if not (isinstance(kids, list) and 2 <= len(kids) <= 3):
            sys.exit(f"✗ {bid}: breakdown part {k} takes 2-3 parts of its own: {len(kids) if isinstance(kids, list) else kids!r}")
        ops(kids, f"part {k}.")
        if any("parts" in c for c in kids):
            sys.exit(f"✗ {bid}: breakdown part {k}: no third level (a second-level part has parts)")
        if min(230, s / len(kids)) < 150:
            sys.exit(f"✗ {bid}: breakdown part {k}: second level too crowded: use fewer items")
        total += len(kids)
        ids |= {f"{k}.{j}" for j in range(len(kids))}
    if total > 6:
        sys.exit(f"✗ {bid}: breakdown second level takes at most 6 parts in all: {total}")
    for f in params.get("focus") or []:
        if f.get("id") not in ids:
            sys.exit(f"✗ {bid}: breakdown focus id must name a part (\"1\", \"1.0\"): {f.get('id')!r}")


def web_params(P, b, params):
    """web_evidence: the source line is required (a quoted page or report must name where it is from, 2026-10-29), the crop
    and every highlight box must lie inside the image. Returns params with "_img" [w, h] for scenes/web_evidence.js."""
    if not str(params.get("source", "")).strip():
        sys.exit(f"✗ {b['id']}: web_evidence needs source (site or outlet and date, shown under the screenshot)")
    src = P / params.get("src", "")
    if src.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp") or not src.is_file():
        sys.exit(f"✗ {b['id']}: web_evidence src must be a png / jpg / webp in the project: {params.get('src')!r}")
    wh = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                         "-of", "csv=p=0", str(src)], capture_output=True, text=True, check=True).stdout.strip()
    iw, ih = (int(v) for v in wh.split(",")[:2])

    def inside(r, x0, y0, x1, y1):
        return (isinstance(r, list) and len(r) == 4 and all(isinstance(v, (int, float)) for v in r) and r[2] > 0 and r[3] > 0
                and r[0] >= x0 and r[1] >= y0 and r[0] + r[2] <= x1 and r[1] + r[3] <= y1)
    crop = params.get("crop", [0, 0, iw, ih])
    if not inside(crop, 0, 0, iw, ih):
        sys.exit(f"✗ {b['id']}: web_evidence crop must be [x, y, w, h] inside the {iw} x {ih} image: {crop!r}")
    # a scrolling card's window moves down the page: its marks only have to sit inside the window's columns
    y0, y1 = (0, ih) if params.get("scroll") else (crop[1], crop[1] + crop[3])
    for m in params.get("marks", []):
        if not inside(m.get("box"), crop[0], y0, crop[0] + crop[2], y1):
            sys.exit(f"✗ {b['id']}: web_evidence mark box must be [x, y, w, h] inside the crop {crop}"
                     f"{' (any row, it scrolls)' if params.get('scroll') else ''}: {m.get('box')!r}")
    for s in params.get("scroll") or []:
        if not (isinstance(s.get("y"), (int, float)) and 0 <= s["y"] <= ih - crop[3]):
            sys.exit(f"✗ {b['id']}: web_evidence scroll y must be 0 … {ih - crop[3]} (image height − window): {s.get('y')!r}")
    return {**params, "_img": [iw, ih]}


BG_TONES = ("light", "dark", "full")


def bg_video(P, b, spec, out, d, real=()):
    """"bg_video": {"src", "tone", "in"} — a VE live-action clip under the scene (data over
    moving footage, never a bare background). tone "light": grey and washed with the
    theme's paper colour, the channel's own look for ordinary beats; tone "dark": dimmed and desaturated, kept for the few
    beats that should read as "this is the point" (reconstructions, turns), and the scene switches to lecture-dark;
    tone "full": the clip as it is, full size, nothing over it: for a beat that is footage with one small card on it
    (a `photo` scene with a `label`; text cards, counting those over washed footage, are kept under 30%), so only scenes whose text sits on its
    own card read on it.
    real: path prefixes of real footage (doc.json "real_footage" and the keys of "footage_credits"). A real clip
    shorter than its beat stops the run: played backward, people walk backward and it shows (FORMAT §4e); a generated
    clip is still played forward then backward, with a line saying so, since its motion has to be looked at.
    Returns the media html (video baked to the beat's length, last frame held) and the theme to draw with."""
    v = spec["bg_video"]
    tone = v.get("tone", "light")
    if tone not in BG_TONES:
        sys.exit(f"✗ {b['id']}: bg_video tone must be one of {', '.join(BG_TONES)}: {tone!r}")
    look = {"light": "hue=s=0,eq=brightness=0.06:contrast=0.85", "dark": "eq=saturation=0.35:brightness=-0.32", "full": "null"}[tone]
    size = "1920:1080" if tone == "full" else "960:540"
    t_in = float(v.get("in", 0))
    have = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(P / v["src"])],
                                capture_output=True, text=True, check=True).stdout) - t_in
    # washed or dimmed footage needs no detail: work at half size (the reversed copy is held in memory), scale up at the end.
    # A beat longer than the clip (a board that grows over five lines can run 20 s; VE clips are at most 10 s) plays it
    # forward then backward, slowed if even that is short, instead of freezing on the last frame.
    base = f"[0:v]trim=start={t_in:.3f},setpts=PTS-STARTPTS,scale={size}:force_original_aspect_ratio=increase,crop={size},setsar=1,{look}"
    if have >= d:
        fc = f"{base}[v]"
    else:
        if any(str(v["src"]).startswith(r) for r in real):
            sys.exit(f"✗ {b['id']}: bg_video {v['src']} is real footage and {d - have:.1f}s shorter than the beat ({have:.1f}s of {d:.1f}s): "
                     f"it would play backward. Use a longer clip, an earlier \"in\", or split the beat")
        print(f"· {b['id']}: bg_video {v['src']} is {d - have:.1f}s shorter than the beat and will play forward, then backward; "
              "check that the motion (cars, people, water) still reads right")
        slow = max(1.0, d / (2 * have))
        fc = (f"{base},split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0,setpts={slow:.4f}*PTS[v]")
    fc = fc[:-3] + f",fps=30,scale=1920:1080,tpad=stop_mode=clone:stop_duration={d:.3f}[v]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(P / v["src"]), "-filter_complex", fc, "-map", "[v]", "-t", f"{d:.3f}",
                    "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-an", str(out / "bgv.mp4")], check=True)
    wash = {"light": "background: var(--bg); opacity: .78;", "full": "display: none;",
            "dark": "background: linear-gradient(180deg, rgba(15,25,45,.35), rgba(10,15,25,.55));"}[tone]
    media = (f'<video id="bgv" class="clip" src="bgv.mp4" muted playsinline data-start="0" data-duration="{d}" data-track-index="1" '
             f'style="position:absolute;left:0;top:0;width:1920px;height:1080px;z-index:2"></video>'
             f'<div class="full" style="z-index:3;{wash}"></div>')
    return media, "lecture-dark" if tone == "dark" else None


def build(P, doc, b, spec, theme, out_root=None):
    """One code beat's page in <out_root or P/code_<theme>>/<id>/ (doc_theme_preview.py builds into its own folder)."""
    th = code_theme(theme, doc.get("palette"), doc.get("rise"))
    d = round(b["duration"] + TAIL, 2)
    out = (Path(out_root) if out_root else P / f"code_{theme}") / b["id"]
    (out / "fonts").mkdir(parents=True, exist_ok=True)
    for f in ("NotoSerifTC-Variable.ttf", "NotoSansTC-Variable.ttf"):
        shutil.copy(asset("fonts", f), out / "fonts" / f)
    shutil.copy(gsap_file(), out / "gsap.min.js")   # the page loads it from its own folder: no CDN
    params = fg_auto(P, spec.get("params", {}))   # photo layers with "fg": "auto" → cut-out png next to the photo
    if spec["scene"] == "credits" and not params.get("groups"):
        params = {**params, "groups": credit_groups(P, doc)}
    for src in set(re.findall(r'"(?:src|fg)":\s*"([^"]+)"', json.dumps(params))):   # fg: a photo's cut-out foreground
        a, dst = (P / src).resolve(), (out / src).resolve()
        if not a.is_relative_to(P.resolve()) or not dst.is_relative_to(out.resolve()):
            sys.exit(f"✗ {b['id']}: asset path must stay inside the project: {src}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(a, dst)
    media = ""
    if spec.get("bg_video"):
        if spec["scene"] in ("screen_step", "ve_annotate"):
            sys.exit(f"✗ {b['id']}: bg_video goes under a drawn scene, not under {spec['scene']} (it has its own video)")
        bgv, tone_theme = bg_video(P, b, spec, out, d, tuple(doc.get("real_footage") or ()) + tuple(doc.get("footage_credits") or ()))
        if tone_theme and theme.startswith("lecture"):
            th = code_theme(tone_theme, doc.get("palette"), doc.get("rise"))
    if spec["scene"] == "screen_step":
        media, params = screen_media(P, doc, b, params, out, d)
    elif spec["scene"] == "ve_annotate":
        media, params = ve_media(P, doc, b, params, out, d)
    elif spec["scene"] == "web_evidence":
        params = web_params(P, b, params)
    elif spec["scene"] == "flow":
        flow_params(P, b, params)
    elif spec["scene"] == "relation":
        relation_params(P, b, params)
    elif spec["scene"] == "line_chart":
        line_params(P, b, params)
    elif spec["scene"] == "pie":
        pie_params(P, b, params)
    elif spec["scene"] == "formula":
        formula_params(P, b, params)
    elif spec["scene"] == "timeline":
        timeline_params(P, b, params)
    elif spec["scene"] == "quote_card" and params.get("reveal", "blur") != "blur":
        sys.exit(f"✗ {b['id']}: quote_card reveal must be \"blur\" or left out: {params['reveal']!r}")
    elif spec["scene"] == "breakdown":
        breakdown_params(P, b, params)
    vin, vout = spec.get("veil", [False, False])
    big = params.get("big_size", 230 if doc["lang"] == "zh" else 170)
    rep = {"__LANG__": doc["lang"], "__ID__": b["id"], "__VARS__": th["vars"], "__PAPER__": th["paper"], "__TEXTURE__": th["texture"],
           "__FILTERS__": th["filters"], "__VIGNETTE__": th["vignette"], "__DIM__": th["dim"], "__FLASH__": th["flash"],
           "__CSS__": th["css"], "__BIGSIZE__": str(big), "__D__": str(d), "__TAIL__": str(TAIL), "__THEME__": theme,
           "__TORN__": "true" if th["torn"] else "false", "__PHEASE__": th["photo_ease"],
           "__TOKENS__": json.dumps(b["tokens"], ensure_ascii=False), "__VIN__": "true" if vin else "false",
           "__VOUT__": "true" if vout else "false", "__PARAMS__": json.dumps(params, ensure_ascii=False),
           "__LIB__": (SKILL_DOC / "lib/lib.js").read_text(encoding="utf-8"),
           "__SCENES__": "\n".join(f.read_text(encoding="utf-8") for f in sorted((SKILL_DOC / "scenes").glob("*.js"))),
           "__SCENE__": spec["scene"],
           "__STAGE__": stage_left(doc) if b["id"] in doc.get("side", {}).get("beats", []) else "",
           "__MEDIA__": (bgv if spec.get("bg_video") else "") + media}
    html = (SKILL_DOC / "lib/template.html").read_text(encoding="utf-8")
    for k in ["__LIB__", "__SCENES__"] + [k for k in rep if k not in ("__LIB__", "__SCENES__")]:
        html = html.replace(k, rep[k])          # code first, so placeholder-looking text inside it is left alone
    (out / "index.html").write_text(html, encoding="utf-8")
    if spec["scene"] == "screen_step":
        read_marks(out, out.parent / f"{b['id']}.marks.json")
    if spec["scene"] == "relation" and (hit := relation_overlaps(page_value(out, "window.__relcards || []"))):
        sys.exit(f"✗ {b['id']}: relation cards do not fit: " + "; ".join(hit)
                 + " (shorten the labels or subs, split the row in two, or place the cards yourself with x / y)")
    return out, d


def main():
    doc, P = load(sys.argv[1])
    theme = next((a.split("=", 1)[1] for a in sys.argv[2:] if a.startswith("--theme=")), doc.get("theme", "collage"))
    if theme not in CODE_THEMES:
        sys.exit(f"✗ theme must be one of {', '.join(CODE_THEMES)}")
    try:
        code_theme(theme, doc.get("palette"), doc.get("rise"))
    except ValueError as e:
        sys.exit(f"✗ {e}")
    want = [a for a in sys.argv[2:] if not a.startswith("--")]
    spec = {b["id"]: b for b in doc["beats"]}
    beats = [b for b in read_beats(P / "beats.json")["beats"] if b["source"] == "code" and (not want or b["id"] in want)]
    bad = {b["id"]: m for b in beats if (m := missing_triggers(spec[b["id"]].get("params", {}), b, doc["lang"]))}
    if bad:
        sys.exit("✗ trigger phrases not in the beat's narration: " + "; ".join(f"{k}: {', '.join(v)}" for k, v in bad.items()))
    # burst_title drops its subtitle and dims until the word: a word late in the line leaves the voice over a dark,
    # empty frame (2026-10-21: 「無故」 1.9 s in, 「恩典」 at the line's end). The word must open the line.
    late = [f"{b['id']}: word={spec[b['id']]['params']['word']!r}" for b in beats if spec[b["id"]]["scene"] == "burst_title"
            and tokens(spec[b["id"]]["params"].get("word", ""), doc["lang"]) != [t[0] for t in b["tokens"]][
                :len(tokens(spec[b["id"]]["params"].get("word", ""), doc["lang"]))]]
    if late:
        sys.exit("✗ burst_title word must be the first words of its line (big may still show another word): " + "; ".join(late))
    empty = [m for b in beats if (m := empty_first_line(doc, b, spec[b["id"]]))]
    if empty:
        sys.exit("✗ the scene stays empty through the beat's first line (use a number at, or start the beat on that line): "
                 + "; ".join(empty))
    slow = [m for b in beats if (m := late_first_element(doc, b, spec[b["id"]]))]
    if slow:
        sys.exit(f"✗ the beat opens on bare paper for more than {LEAD_MAX:g} s (make at the beat's first words or a number like 0.3, "
                 "or put a bg_video / photos under it): " + "; ".join(slow))
    for b in beats:
        out, d = build(P, doc, b, spec[b["id"]], theme)
        if doc.get("sfx_on"):
            read_sfx(out, out.parent / f"{b['id']}.sfx.json")
        msg = f"{theme}/{b['id']} ({spec[b['id']]['scene']}): {d}s"
        if "--render" in sys.argv:
            log = out.parent / f"{b['id']}.render.log"
            r = hyperframes("render", out, "-o", out.parent / f"{b['id']}.mp4", "--fps", "30", stdout=open(log, "w"))
            if r.returncode:
                sys.exit(f"✗ render failed: {log}\n{log_tail(log)}")
            errs = [l.strip() for l in log.read_text(errors="ignore").splitlines() if "PAGEERROR" in l]
            if errs:   # the renderer keeps going after a script error and writes a clip with the scene missing
                sys.exit(f"✗ {b['id']}: page script error ({errs[0]}); see {log}")
            msg += f" rendered → {out.parent / (b['id'] + '.mp4')}"
        print(msg)


if __name__ == "__main__":
    main()
