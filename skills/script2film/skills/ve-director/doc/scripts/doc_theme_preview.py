"""Theme preview: three themes side by side on three of this episode's own code beats, before anything is voiced, so the
theme can be picked while the script is read (the theme has to be settled before VE: VE prompts carry its colours).
Optional: an episode that skips it is made exactly as before.

  python3 doc_theme_preview.py <doc.json> [--themes a,b,c] [--beats B3,B7,B12]
  python3 doc_theme_preview.py <doc.json> --pick <theme> "<why>"

Writes <project>/preview/: theme_preview.mp4 (1920x1080, a 2x2 grid: three themes playing the same beats in step, the
fourth cell names them with the reason each was offered; no sound), theme_preview.jpg (the end frame of every beat, one
row per theme), preview.json (what was shown), and code_<theme>/ (the pages and clips). Never writes beats.json or
code_<theme>/ in the project.

Timing: beats.json when the episode is already aligned, else an estimate like doc_runsheet --estimate (5 Chinese
characters or 2.5 English words a second, plus the script's gaps), the words spread evenly over it; so the motion is real
and the pace is a guess.
Beats: --beats, else three code beats with different scenes, the ones that need no VE footage first. A picture the
project does not have yet (a VE still) becomes a grey placeholder; a bg_video clip that is not there is left out.
Themes: --themes, else three: (a) the previous episode's theme (NNN_ folders), else series.json "theme", else the
script's own, else the first in the order below; (b) the first with the other brightness and another shape family;
(c) the first in a third shape family. "The first" follows series.json "themes" when it lists candidates, else ORDER.
Shape family: the eight lecture-* themes are one; collage, live and each styles.json theme are one each.
--pick writes "theme" into doc.json (dropping an era "palette" when the theme is not collage) and records the choice
with its reason in preview/theme_choice.json.
"""
import datetime, json, re, shutil, subprocess, sys
from pathlib import Path

from doc_common import asset, hyperframes, load, log_tail, read_beats, read_json, tokens
import doc_code
from doc_lint import prev_episode
from doc_themes import CODE_THEMES, STYLES

RATE = {"zh": 5.0, "en": 2.5}          # characters / words a second (doc_runsheet --estimate uses 5 for Chinese)
LEAD, MIN_D = 0.45, 2.5                # first word after the beat starts (aligned beats: about 0.5 s); shortest beat
ORDER = ["newsroom", "editorial-serif", "dark-gold", "vintage-poster", "cinematic-dark", "lecture-light", "lecture-dark",
         "collage", "live"] + [t for t in CODE_THEMES if t.startswith("lecture-") and t not in ("lecture-light", "lecture-dark")]
# scenes in the order they are offered: no VE footage first; scenes built on a recording or a screenshot never
PREFER = ("cover", "stat_count", "compare", "timeline", "relation", "formula", "list_reveal", "bars", "line_chart", "pie",
          "breakdown", "flow", "grid_hot", "countdown", "map_route", "merge_bubble", "burst_title", "quote_card", "credits")
NEVER = {"screen_step", "ve_annotate", "web_evidence"}
CELL = (960, 540)


def family(t):
    return "lecture" if t.startswith("lecture-") else t


def light(t):
    return CODE_THEMES[t]["light"]


def pick_themes(doc, P):
    """[(theme, reason), ...] three themes: see the module docstring."""
    sj = P.parent / "series.json"
    series = read_json(sj) if sj.exists() else {}
    order = [t for t in (series.get("themes") or ORDER) if t in CODE_THEMES]
    prev = prev_episode(P / "doc.json")
    pt = read_json(prev).get("theme") if prev else None
    if pt in CODE_THEMES:
        a, why = pt, f"上一集（{prev.parent.name}）用的"
    elif series.get("theme") in CODE_THEMES:
        a, why = series["theme"], "系列預設"
    elif doc.get("theme") in CODE_THEMES:
        a, why = doc["theme"], "稿子目前寫的"
    else:
        a, why = order[0], "候選清單第一套"
    out = [(a, why)]
    b = next((t for t in order if light(t) != light(a) and family(t) != family(a)), None)
    if b:
        out.append((b, "明暗相反（" + ("淺底" if light(b) else "深底") + "）"))
    used = {family(t) for t, _ in out}
    c = next((t for t in order if family(t) not in used), None)
    if c:
        out.append((c, "換一種形狀"))
    return out


def estimate(doc):
    """beats.json-like entries for every beat from the script (see the module docstring)."""
    lang, L, B = doc.get("lang", "zh"), [l["text"] for l in doc["lines"]], doc["beats"]
    gaps = doc.get("gaps", {})
    after = {int(k): v for k, v in gaps.get("after", {}).items()}
    out = []
    for i, b in enumerate(B):
        n = b["lines"][0]
        t = L[n - 1]
        s0 = t.find(b["from"]) if b.get("from") else 0
        nxt = B[i + 1] if i + 1 < len(B) else None
        if nxt and nxt["lines"][0] == n and nxt.get("from"):
            seg, gap = t[max(s0, 0):t.find(nxt["from"])], 0.0
        else:
            seg, gap = t[max(s0, 0):], after.get(b["lines"][-1], gaps.get("default", 0.3))
        seg += "".join(L[m - 1] for m in b["lines"][1:])
        tok = tokens(seg, lang)
        step = 1 / RATE.get(lang, 5.0)
        dur = max(MIN_D, LEAD + len(tok) * step + gap)
        out.append({"id": b["id"], "source": b["source"], "text": seg, "duration": round(dur, 2),
                    "tokens": [[w, round(LEAD + k * step, 2)] for k, w in enumerate(tok)]})
    return out


def pick_beats(doc, want):
    """The code beats to show: want (ids), else three with different scenes, PREFER order, kept in script order."""
    code = [b for b in doc["beats"] if b["source"] == "code"]
    if want:
        miss = [w for w in want if w not in {b["id"] for b in code}]
        if miss:
            sys.exit(f"✗ not code beats in this script: {', '.join(miss)}")
        return [b for b in code if b["id"] in want]
    ranked = sorted((b for b in code if b.get("scene") in PREFER), key=lambda b: PREFER.index(b["scene"]))
    seen, out = set(), []
    for b in ranked:
        if b["scene"] not in seen:
            seen.add(b["scene"])
            out.append(b["id"])
        if len(out) == 3:
            break
    if not out:
        sys.exit("✗ no code beat this preview can show (screen_step / ve_annotate / web_evidence need their recordings)")
    return [b for b in code if b["id"] in out]


def placeholder(P):
    """preview/_photo.jpg: a grey frame that says 照片 (pictures VE has not made yet)."""
    from PIL import Image, ImageDraw, ImageFont
    f = P / "preview/_photo.jpg"
    if not f.exists():
        im = Image.new("RGB", (1280, 720), "#8a8a8a")
        d = ImageDraw.Draw(im)
        font = ImageFont.truetype(str(asset("fonts", "NotoSansTC-Variable.ttf")), 96)
        d.text((640, 360), "照片", font=font, fill="#d8d8d8", anchor="mm")
        im.save(f, quality=85)
    return "preview/_photo.jpg"


def fill_missing(P, x, key=None):
    """params with every src / fg the project does not have replaced by the placeholder (fg dropped)."""
    if isinstance(x, dict):
        out = {}
        for k, v in x.items():
            if k in ("src", "fg") and isinstance(v, str) and v != "auto" and not (P / v).exists():
                if k == "src":
                    out[k] = placeholder(P)
                continue
            out[k] = fill_missing(P, v, k)
        return out
    if isinstance(x, list):
        return [fill_missing(P, v, key) for v in x]
    return x


def theme_doc(doc, theme):
    """doc as rendered under theme: an era palette only stays on collage, rise only where the theme takes it."""
    d = dict(doc)
    if theme != "collage":
        d.pop("palette", None)
    if not (theme.startswith("lecture-") or theme in STYLES):
        d.pop("rise", None)
    return d


def label(text, size, w, h, bg=(0, 0, 0, 170)):
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype(str(asset("fonts", "NotoSansTC-Variable.ttf")), size)
    im = Image.new("RGBA", (w, h), bg)
    ImageDraw.Draw(im).text((18, h // 2), text, font=font, fill="white", anchor="lm")
    return im


def legend(themes, P):
    """The fourth cell: where each theme is and why it was offered."""
    from PIL import Image, ImageDraw, ImageFont
    f = str(asset("fonts", "NotoSansTC-Variable.ttf"))
    im = Image.new("RGB", CELL, "#1b1b1b")
    d = ImageDraw.Draw(im)
    d.text((48, 50), "主題試看", font=ImageFont.truetype(f, 44), fill="white")
    for k, ((t, why), pos) in enumerate(zip(themes, ("左上", "右上", "左下"))):
        d.text((48, 150 + k * 110), f"{pos}　{t}", font=ImageFont.truetype(f, 36), fill="white")
        d.text((48, 198 + k * 110), why, font=ImageFont.truetype(f, 26), fill="#bbbbbb")
    d.text((48, 490), "動態是真的，節奏是估的（還沒配音）", font=ImageFont.truetype(f, 22), fill="#888888")
    out = P / "preview/_legend.png"
    im.save(out)
    return out


def ff(*args):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"✗ ffmpeg: {r.stderr.strip()[-400:]}")


def compose(P, themes, ids, total):
    """theme_preview.mp4 (2x2) and theme_preview.jpg (end frames, one row per theme)."""
    from PIL import Image
    pv, cells = P / "preview", []
    for t, _ in themes:
        lst = pv / f"code_{t}/_list.txt"
        lst.write_text("".join(f"file '{(pv / f'code_{t}/{i}.mp4').resolve()}'\n" for i in ids))
        tag = pv / f"code_{t}/_tag.png"
        label(t, 30, 330, 52).save(tag)
        cell = pv / f"code_{t}/_cell.mp4"
        ff("-f", "concat", "-safe", "0", "-i", lst, "-i", tag, "-filter_complex",
           f"[0:v]fps=30,scale={CELL[0]}:{CELL[1]}[v];[v][1]overlay=0:0", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", cell)
        cells.append(cell)
    leg = legend(themes, P)
    ins = sum((["-i", c] for c in cells), []) + ["-loop", "1", "-t", f"{total:.2f}", "-i", leg]
    n = len(cells) + 1
    lay = "|".join(("0_0", "w0_0", "0_h0", "w0_h0")[:n])
    ff(*ins, "-filter_complex", "".join(f"[{k}:v]" for k in range(n)) + f"xstack=inputs={n}:layout={lay}:fill=black,format=yuv420p",
       "-t", f"{total:.2f}", "-r", "30", "-c:v", "libx264", "-crf", "20", pv / "theme_preview.mp4")
    W, H = 640, 360
    sheet = Image.new("RGB", (W * len(ids), H * len(themes)), "black")
    for r, (t, _) in enumerate(themes):
        for c, i in enumerate(ids):
            png = pv / f"code_{t}/_{i}_end.png"
            ff("-sseof", "-0.4", "-i", pv / f"code_{t}/{i}.mp4", "-frames:v", "1", "-vf", f"scale={W}:{H}", png)
            sheet.paste(Image.open(png), (c * W, r * H))
        tag = label(t, 26, 300, 44)
        sheet.paste(tag, (0, r * H), tag)
    sheet.save(pv / "theme_preview.jpg", quality=88)


def preview(doc, P, themes_arg, beats_arg):
    pv = P / "preview"
    pv.mkdir(exist_ok=True)
    real = P / "beats.json"
    timing = {b["id"]: b for b in (read_beats(real)["beats"] if real.exists() else estimate(doc))}
    specs = pick_beats(doc, beats_arg)
    if themes_arg:
        bad = [t for t in themes_arg if t not in CODE_THEMES]
        if bad:
            sys.exit(f"✗ not a theme: {', '.join(bad)} (themes: {', '.join(CODE_THEMES)})")
        themes = [(t, "指定") for t in themes_arg][:3]
    else:
        themes = pick_themes(doc, P)
    ids = [s["id"] for s in specs]
    total = 0.0
    for t, _ in themes:
        root, total = pv / f"code_{t}", 0.0
        if root.exists():
            shutil.rmtree(root)
        for s in specs:
            spec = {k: v for k, v in s.items() if not (k == "bg_video" and not (P / v.get("src", "")).exists())}
            spec["params"] = fill_missing(P, s.get("params", {}))
            out, d = doc_code.build(P, theme_doc(doc, t), timing[s["id"]], spec, t, out_root=root)
            log = root / f"{s['id']}.render.log"
            r = hyperframes("render", out, "-o", root / f"{s['id']}.mp4", "--fps", "30", stdout=open(log, "w"))
            if r.returncode:
                sys.exit(f"✗ {t}/{s['id']}: render failed: {log}\n{log_tail(log)}")
            total += d
            print(f"{t}/{s['id']} ({s['scene']}): {d}s")
    compose(P, themes, ids, total)
    (pv / "preview.json").write_text(json.dumps(
        {"themes": [{"theme": t, "why": w} for t, w in themes], "beats": ids,
         "timing": "beats.json" if real.exists() else "estimate"}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"→ {pv / 'theme_preview.mp4'}\n→ {pv / 'theme_preview.jpg'}")
    print("pick one: python3 doc_theme_preview.py <doc.json> --pick <theme> \"<why>\"")


def pick(doc_path, doc, P, theme, why):
    if theme not in CODE_THEMES:
        sys.exit(f"✗ not a theme: {theme} (themes: {', '.join(CODE_THEMES)})")
    raw = Path(doc_path).read_text(encoding="utf-8")
    doc["theme"] = theme
    note = ""
    if theme != "collage" and doc.pop("palette", None) is not None:
        note = " (era palette dropped: it only applies to collage)"
    Path(doc_path).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + ("\n" if raw.endswith("\n") else ""), encoding="utf-8")
    pv = P / "preview"
    pv.mkdir(exist_ok=True)
    shown = read_json(pv / "preview.json") if (pv / "preview.json").exists() else {}
    (pv / "theme_choice.json").write_text(json.dumps(
        {"theme": theme, "why": why, "date": datetime.date.today().isoformat(), "offered": shown.get("themes", [])},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"theme → {theme}{note}")


def main():
    a = sys.argv[1:]
    if not a or a[0].startswith("-"):
        sys.exit(__doc__)
    doc, P = load(a[0])
    if "--pick" in a:
        k = a.index("--pick")
        if len(a) < k + 3:
            sys.exit('✗ --pick <theme> "<why>"')
        return pick(a[0], doc, P, a[k + 1], a[k + 2])

    def opt(name):
        v = next((x.split("=", 1)[1] for x in a if x.startswith(name + "=")), None)
        if v is None and name in a and a.index(name) + 1 < len(a):
            v = a[a.index(name) + 1]
        return [x for x in (v or "").split(",") if x]
    preview(doc, P, opt("--themes"), opt("--beats"))


if __name__ == "__main__":
    main()
