"""Assemble: code clips + VE clips in beat order → cut_<theme>/plan.json for Concat and a base render (--render).

  python3 doc_cut.py <project>/doc.json [--theme=collage] [--render] [--name <name>]
VE clips: <project>/ve_<look>/shotK.mp4 (ve_collect.py --out; look = doc_themes.ve_look), K in VE-beat order. Code clips: code_<theme>/<id>.mp4.
Builds shell_<theme>/ (subtitle page, narration, synthesized sound: one low impact on the climax word + a faint wind bed),
cut_<theme>.json for <repo>/tools/assemble/assemble.py (cuts each clip to its beat window), then
<repo>/tools/assemble/cut2plan.py writes cut_<theme>/plan.json (plan2concat_mcp.py reads it).
--name is written to the config's timeline.name (default <title>_<theme>). --capcut (removed) only stops with a one-line
pointer to --render and plan2concat_mcp.py.
The joined visual track is deleted unless --render (plan.json reads the per-shot segments, keep those).
The climax subtitle screen (the burst_title beat's line) is dropped: the shot itself shows the word.
"""
import html, json, re, shutil, subprocess, sys

from doc_align import chunks, screen_text
from doc_common import (MIN_SUB_FAIL_S, MIN_SUB_WARN_S, REPO, asset, gsap_file, hyperframes, load, log_tail, parse_srt, read_beats, series_of, sh, short_cues,
                        sub_lang, subs_problems, subtitle_plan, tokens)
from doc_themes import CODE_THEMES, ve_look

sys.path.insert(0, str(REPO / "tools/concat"))
from plan2concat_mcp import loudnorm  # noqa: E402  保底成片與 Concat 成片用同一個響度校正（s2f-1b D5）

SFX_IMPACT = ("[0]volume=1.0,afade=t=out:st=0.05:d=2.1:curve=exp[s];[1]lowpass=f=160,afade=t=out:st=0.02:d=0.55[n];"
              "[s][n]amix=inputs=2:normalize=0,alimiter=limit=0.9")


def sub_highlight(doc):
    """doc.json "sub_highlight": {"words": [...], "color": "#RRGGBB"} → the burned subtitles show those words bold in that
    colour (the product names a film is made for, 2026-11-18); absent → None."""
    h = doc.get("sub_highlight")
    if not h:
        return None
    words, color = h.get("words") or [], h.get("color", "#C8553D")
    if not words or not all(isinstance(w, str) and w.strip() for w in words) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
        sys.exit(f"✗ sub_highlight needs words (a list of strings) and color #RRGGBB: {h!r}")
    return {"words": words, "color": color}


def sub_markup(text, hl):
    """One subtitle as HTML: escaped, the sub_highlight words (whole words, longest first) in <span class="hl">."""
    out = html.escape(text)
    if hl:
        alt = "|".join(re.escape(html.escape(w)) for w in sorted(hl["words"], key=len, reverse=True))
        out = re.sub(rf"(?<!\w)({alt})(?!\w)", r'<span class="hl">\1</span>', out)
    return out


def sub_bg(doc):
    """doc.json "sub_bg": {"color": "#RRGGBB", "alpha": 0-1} → that box, checked; absent → None."""
    bg = doc.get("sub_bg")
    if not bg:
        return None
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(bg.get("color", "#000000"))):
        sys.exit(f"✗ sub_bg.color must be #RRGGBB: {bg.get('color')!r}")
    return {"color": bg.get("color", "#000000"), "alpha": max(0.0, min(float(bg.get("alpha", 0.7)), 1.0))}


def bed_audio(doc, total):
    """殼頁面的底（s2f-1b D5）：稿有 "bgm" 時放配樂（doc_cut 組裝後複製到 <out>/bgm/bgm.wav），沒有時照舊放風聲。
    兩者都用 track 11，不會同時出現；配樂的音量已算進檔裡（bgm()），所以 data-volume 是 1.0。"""
    if doc.get("bgm"):
        return (f'  <audio id="bgm" class="clip" src="bgm/bgm.wav" data-start="0" data-duration="{total}" '
                f'data-volume="1.0" data-track-index="11"></audio>')
    return (f'  <audio id="wind" class="clip" src="sfx/wind.wav" data-start="0" data-duration="{total}" '
            f'data-volume="1.0" data-track-index="11"></audio>')


def sfxbed_audio(doc, total, hits):
    """稿有 "sfx_on" 時放音效底（doc_sfx.py 做的，組裝後複製到 <out>/sfx/sfx_bed.wav），軌號接在重擊後面；沒有就不放。"""
    if not doc.get("sfx_on"):
        return ""
    return (f'  <audio id="sfxbed" class="clip" src="sfx/sfx_bed.wav" data-start="0" data-duration="{total}" '
            f'data-volume="1.0" data-track-index="{12 + len(hits)}"></audio>\n')


def shell(P, doc, beats, total, theme, hits, plan):
    S = P / f"shell_{theme}"
    if S.exists():
        shutil.rmtree(S)
    (S / "fonts").mkdir(parents=True); (S / "sfx").mkdir()
    shutil.copy(asset("fonts", "NotoSerifTC-Variable.ttf"), S / "fonts")
    shutil.copy(gsap_file(), S / "gsap.min.js")   # the page loads it from its own folder: no CDN
    shutil.copytree(P / "voice.cleaned", S / "voice.cleaned", ignore=shutil.ignore_patterns("aligned"))
    burst = {n for b in doc["beats"] if b.get("scene") == "burst_title" for n in b["lines"]}
    burst_text = {doc["lines"][n - 1]["text"].strip() for n in burst}
    blocks = [b for b in (S / "voice.cleaned/final.srt").read_text(encoding="utf-8").strip().split("\n\n")
              if " ".join(b.splitlines()[2:]).strip() not in burst_text]
    (S / "voice.cleaned/final.srt").write_text("\n".join(f"{i}\n" + "\n".join(b.splitlines()[1:]) + "\n" for i, b in enumerate(blocks, 1)), encoding="utf-8")
    if plan["main"] == "zh":   # English narration for Chinese viewers: the main subtitle shows the Chinese line (subtitle_plan)
        screens = json.loads((P / "voice.cleaned/screens.json").read_text(encoding="utf-8"))
        (S / "voice.cleaned/final.srt").write_text(srt(zh_screens(doc, screens, skip=burst)), encoding="utf-8")
        blocks = (S / "voice.cleaned/final.srt").read_text(encoding="utf-8").strip().split("\n\n")   # the fallback film burns these
    elif plan["main"] == "en":   # Chinese narration for English viewers: one English cue per line ("en"), nothing in Chinese
        (S / "voice.cleaned/final.srt").write_text(srt([{**c, "text": en_wrap(c["text"])} for c in line_cues(P, doc, skip=burst)]), encoding="utf-8")
        blocks = (S / "voice.cleaned/final.srt").read_text(encoding="utf-8").strip().split("\n\n")   # the film burns these
    # the subtitles that are burned in (this file, whichever way it was made): too brief to read → listed here, and
    # tools/nightly/check.py fails the film on any under MIN_SUB_FAIL_S (this step does not stop: previews still build)
    fail, warn = short_cues(parse_srt((S / "voice.cleaned/final.srt").read_text(encoding="utf-8")))
    (P / "voice.cleaned/short_subs.json").write_text(json.dumps(
        {"source": {"zh": "zh_screens", "en": "en lines"}.get(plan["main"], "final.srt"), "fail": fail, "warn": warn}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"subtitles: {len(fail)} shorter than {MIN_SUB_FAIL_S:g}s, {len(warn)} at {MIN_SUB_FAIL_S:g}–{MIN_SUB_WARN_S:g}s"
          + (" (the film check will fail: merge that line with the one before or after into one screen)" if fail else ""))
    for c in fail:
        print(f"  ✗ {c['start']:.2f}s, on screen {c['dur']:.2f}s: {c['text']}")
    sh("ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=f=48:d=2.2:sample_rate=48000", "-f", "lavfi",
       "-i", "anoisesrc=c=brown:d=0.6:a=0.6:r=48000", "-filter_complex", SFX_IMPACT, "-ac", "1", S / "sfx/impact.wav")
    sh("ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"anoisesrc=c=pink:d={total}:a=0.5:r=48000", "-af",
       f"lowpass=f=700,highpass=f=80,tremolo=f=0.12:d=0.5,volume=0.06,afade=t=in:d=1.5,afade=t=out:st={total - 2}:d=2",
       "-ac", "1", S / "sfx/wind.wav")
    secs = lambda s: sum(float(x) * m for x, m in zip(s.replace(",", ".").split(":"), (3600, 60, 1)))
    cues = []
    for i, b in enumerate(blocks):
        ln = b.splitlines()
        t, end = (secs(x) for x in ln[1].split(" --> "))
        cues.append([round(t, 3), "\n".join(ln[2:])])
        nxt = secs(blocks[i + 1].splitlines()[1].split(" --> ")[0]) if i + 1 < len(blocks) else None
        if nxt is not None and nxt - end > 0.05:   # a dropped climax screen leaves a gap: clear the old line instead of holding it
            cues.append([round(end, 3), ""])
    cues.append([round(total - 0.3, 3), ""])
    light = CODE_THEMES[theme]["light"]
    # a round host frame sits in the lower-left corner: keep the subtitle mist to the middle so it does not veil the face
    mist_mask = ("-webkit-mask-image: linear-gradient(to right, transparent 0, #000 420px, #000 1500px, transparent 1920px);"
                 if doc.get("pip") else "")
    ink, glow = ("#1d1a17", "242,236,221") if light else ("#f2efe8", "10,11,12")
    # doc.json "sub_bg": white subtitles on a dark box instead of the mist (timeline.sub_bg gives plan.json the same box)
    bg = sub_bg(doc)
    sub_bg_css = (f"#sub {{ color: #fff; text-shadow: none; padding: 6px 24px; border-radius: 8px; "
                  f"background: rgba({','.join(str(int(bg['color'][i:i + 2], 16)) for i in (1, 3, 5))},{bg['alpha']}); }} "
                  "#sub:empty { display: none; } .mist { display: none; }") if bg else ""
    hl = sub_highlight(doc)
    hl_css = f" #sub .hl {{ color: {hl['color']}; font-weight: 900; }}" if hl else ""
    (S / "index.html").write_text(f"""<!DOCTYPE html>
<html lang="{html.escape(doc['lang'])}"><head><meta charset="UTF-8"><title>{html.escape(doc['title'])}</title>
<script src="gsap.min.js"></script>
<style>
  @font-face {{ font-family: "Noto Serif TC"; src: url("fonts/NotoSerifTC-Variable.ttf") format("truetype"); font-weight: 200 900; }}
  * {{ box-sizing: border-box; }} body {{ margin: 0; background: #000; overflow: hidden; }}
  #root {{ position: relative; width: 1920px; height: 1080px; overflow: hidden; font-family: "Noto Serif TC", serif; }}
  .mist {{ position: absolute; left: 0; width: 1920px; top: 800px; height: 280px; z-index: 95;
           background: linear-gradient(to bottom, rgba({glow},0) 0%, rgba({glow},.72) 50%, rgba({glow},.82) 100%); {mist_mask} }}
  .subs {{ position: absolute; left: 0; width: 1920px; top: 900px; text-align: center; z-index: 100; }}
  #sub {{ display: inline-block; white-space: pre-line; font-size: 48px; font-weight: 700; letter-spacing: 2px; color: {ink};
          text-shadow: 0 0 10px rgba({glow},.95), 0 0 22px rgba({glow},.85); }}
  {sub_bg_css}{hl_css}
</style></head><body>
<div id="root" data-composition-id="main" data-width="1920" data-height="1080" data-start="0" data-duration="{total}">
  <video id="visual" class="clip" src="visual.mp4" muted playsinline data-start="0" data-duration="{total}" data-track-index="1"
         style="position:absolute;left:0;top:0;width:1920px;height:1080px;object-fit:cover;z-index:20"></video>
  <div class="mist"></div><div class="subs"><div id="sub"></div></div>
  <audio id="voice" class="clip" src="voice.cleaned/audio.m4a" data-start="0" data-duration="{total}" data-volume="1.0" data-track-index="10"></audio>
{bed_audio(doc, total)}
{"".join(f'  <audio id="impact{k}" class="clip" src="sfx/impact.wav" data-start="{h}" data-duration="2.2" data-volume="0.9" data-track-index="{12 + k}"></audio>' + chr(10) for k, h in enumerate(hits))}{sfxbed_audio(doc, total, hits)}</div>
<script>
  const main = gsap.timeline({{ paused: true }});
  {json.dumps([[t, sub_markup(txt, hl)] for t, txt in cues] if hl else cues, ensure_ascii=False)}.forEach(([t, txt]) => main.set("#sub", {{ {"innerHTML" if hl else "textContent"}: txt }}, t));
  main.set({{}}, {{}}, {total});
  window.__timelines = window.__timelines || {{}}; window.__timelines["main"] = main;
</script></body></html>
""", encoding="utf-8")
    return S


WIPE_S = 0.2   # each half of a paper wipe: the sheet covers the frame at the cut, then leaves


def wipe_sheet(path, theme):
    """a frame-wide paper sheet with torn left and right edges (2200 x 1080 PNG), drawn once per cut folder."""
    col = "0xf4ecd8" if CODE_THEMES[theme]["light"] else "0x1d1a17"
    edge = "if(between(X,{l},{r}),255,0)".format(
        l="40+18*sin(Y/7)+12*sin(Y/2.9)+6*sin(Y/1.3)", r="2160-(18*sin(Y/6)+12*sin(Y/3.3)+6*sin(Y/1.7))")
    sh("ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color={col}:s=2200x1080:d=1", "-vf",
       f"format=rgba,noise=alls=10:allf=u,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='{edge}'", "-frames:v", "1", path)


SIDE_RECT = [1300, 120, 560, 624]   # right frame; x < 1240 is the diagram's (2026-10-28: host smaller, more room on the left)


def video_size(clip):
    return tuple(map(int, subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height",
                                          "-of", "csv=p=0", clip], capture_output=True, text=True, check=True).stdout.split(",")))


def check_layers(doc):
    """Stop before any ffmpeg work when the host layers contradict each other (lecture-style D2)."""
    side = set(doc.get("side", {}).get("beats", []))
    both = side & set(doc.get("pip", {}).get("beats", []))
    if both:
        sys.exit(f"✗ beats in both side and pip: {', '.join(sorted(both))}")
    host = sorted(b["id"] for b in doc["beats"] if b.get("source") == "clip" and b["id"] in side)
    if host:
        sys.exit(f"✗ side lists full-frame host beats (they already show the host): {', '.join(host)}")


PILL_FADE = 0.25
# pill centre in the 1920 x 1080 frame. center / upper cover a full-frame host's face, so a pill on a host beat ("source":
# "clip") defaults to lower-left, anything else to center (2026-10-28 preview card: lower-left and right chosen).
# corner (a source-grade label such as 「依古籍推算」 belongs in a corner, not mid-frame):
# upper left, mirroring the chapter tag on the upper right, at the chapter tag's size, held to the end of its beat.
PILL_POS = {"center": (960, 540), "upper": (960, 360), "lower-left": (400, 760), "right": (1500, 540), "corner": (269, 81)}


def phrase_time(doc, b, phrase):
    """Seconds from beat b's start where phrase opens in its narration (the same contiguous match as
    doc_code.missing_triggers), or None."""
    words, q = ([t[0] for t in b["tokens"]] if b else []), tokens(str(phrase), doc["lang"])
    hit = next((k for k in range(len(words) - len(q) + 1) if q and words[k:k + len(q)] == q), None)
    return None if hit is None else b["tokens"][hit][1]


def pill_times(doc, beats):
    """{pill index: (seconds from its beat's start, beat id)}; a phrase must open somewhere in its own beat's narration,
    else stop."""
    by_id, out, bad = {b["id"]: b for b in beats}, {}, []
    for i, p in enumerate(doc.get("pills", [])):
        if p.get("pos", "center") not in PILL_POS:
            sys.exit(f"✗ pills: {p['beat']} pos must be one of {', '.join(PILL_POS)}: {p.get('pos')!r}")
        t = phrase_time(doc, by_id.get(p["beat"]), p["at"])
        if t is None:
            bad.append(f"{p['beat']} \"{p['at']}\"")
        else:
            out[i] = (t, p["beat"])
    if bad:
        sys.exit("✗ pills: phrase not in the beat's narration: " + ", ".join(bad))
    return out


def chapter_spans(doc, beats):
    """doc.json "chapters" → [{start, end, text}]: each tag runs from its beat's start to the next chapter's beat
    (the last one to the "end" beat, or the film's end); numbered 第 N 章 unless "number": false."""
    ch = doc.get("chapters")
    if not ch:
        return []
    by_id = {b["id"]: b for b in beats}
    total = beats[-1]["start"] + beats[-1]["duration"]
    missing = [t["beat"] for t in ch["tags"] if t["beat"] not in by_id] + ([ch["end"]] if ch.get("end") and ch["end"] not in by_id else [])
    if missing:
        sys.exit(f"✗ chapters: unknown beat {', '.join(missing)}")
    starts = [by_id[t["beat"]]["start"] for t in ch["tags"]] + [by_id[ch["end"]]["start"] if ch.get("end") else total]
    if starts != sorted(starts):
        sys.exit("✗ chapters: tags must follow the film's order")
    num = ch.get("number", True)
    dur = ch.get("dur")   # seconds each tag stays up; default: until the next chapter (2026-11-14: a tag up all film adds to the text load)
    return [{"start": round(starts[i], 3), "end": round(min(starts[i + 1], starts[i] + dur) if dur else starts[i + 1], 3),
             "text": (f"第 {i + 1} 章　" if num else "") + t["text"]} for i, t in enumerate(ch["tags"])]


def punch_spans(doc, beats):
    """doc.json "punch" → [{start, end, scale}] in film seconds: a full-frame host beat jumps closer from phrase "at" to
    phrase "to" (default: the beat's end). Only on host beats ("source": "clip"): a punch on a drawn card reads as a glitch."""
    by_id, out, bad = {b["id"]: b for b in beats}, [], []
    for p in doc.get("punch", []):
        b = by_id.get(p["beat"])
        if not b or b["source"] != "clip":
            sys.exit(f"✗ punch: {p['beat']} is not a full-frame host beat")
        t0 = phrase_time(doc, b, p["at"])
        t1 = phrase_time(doc, b, p["to"]) if p.get("to") else b["duration"]
        if t0 is None or t1 is None or t1 - t0 < 0.5:
            bad.append(f"{p['beat']} \"{p['at']}\" → \"{p.get('to', 'beat end')}\"")
            continue
        out.append({"start": round(b["start"] + t0, 3), "end": round(b["start"] + t1, 3), "scale": float(p.get("scale", PUNCH_SCALE))})
    if bad:
        sys.exit("✗ punch: phrase not in the beat's narration, or under 0.5 s: " + ", ".join(bad))
    return out


def corner_frame(path):
    """Four white corner brackets with a thin dark edge (reads on light cards and dark footage), 1920 x 1080 transparent."""
    m, ln, w = 28, 90, 6
    boxes = []
    for x, y, sx, sy in ((m, m, 1, 1), (1920 - m, m, -1, 1), (m, 1080 - m, 1, -1), (1920 - m, 1080 - m, -1, -1)):
        for bx, by, bw, bh in ((min(x, x + sx * ln), min(y, y + sy * w), ln, w), (min(x, x + sx * w), min(y, y + sy * ln), w, ln)):
            boxes.append((bx - 2, by - 2, bw + 4, bh + 4, "0x14203a@0.35"))
            boxes.append((bx, by, bw, bh, "white@0.92"))
    vf = ",".join(f"drawbox=x={x}:y={y}:w={bw}:h={bh}:color={c}:t=fill" for x, y, bw, bh, c in boxes)
    sh("ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black@0:s=1920x1080,format=rgba", "-vf", vf,
       "-frames:v", "1", path)


# pill text height as a fraction of the frame height: 0.04 (43 px) looked small on the T6 preview card v2 (2026-10-28)
PILL_SIZE = 0.054
# chapter tag (0.026 read small on the frame sheet, 0.032 approved): upper right, above the side frame
CHAPTER_TAG = {"fill": "#1f3a5fe0", "color": "#ffffff", "size": 0.032, "offsetX": 0.36, "offsetY": -0.425, "fade": 0.4}
PUNCH_SCALE = 1.15   # a host punch-in reads as a second, closer camera (v5); 1.3 starts to show the take's softness
PILL_FONT = ("Noto Sans TC Lecture", 800)   # Concat takes static TTFs only: one weight cut from the variable font


# English under the Chinese screen (fractions of the frame). shared (both languages kept, but the
# English competed: its own plate, as dark and as white as the Chinese, and wider because the sentence is longer): the
# English sits inside the Chinese plate at about half the size in a light grey, read as a note to the Chinese line.
# plan2concat_mcp.py lays it out (plate width measured from the font); offsetY is only used without shared.
EN_SUB = {"size": 0.023, "color": "#c9d1d9", "shared": True, "offsetY": 0.425, "zh_offsetY": 0.32, "wrap": 80}


def en_wrap(text, width=EN_SUB["wrap"]):
    """Lines of about equal length, each break at the space nearest its share, when the text is longer than width characters."""
    n = -(-len(text) // width)
    if n <= 1 or " " not in text:
        return text
    spaces, cuts = [i for i, c in enumerate(text) if c == " "], []
    for j in range(1, n):
        left = [i for i in spaces if i > (cuts[-1] if cuts else -1)]
        if left:
            cuts.append(min(left, key=lambda i: abs(i - len(text) * j / n)))
    return "".join("\n" if i in cuts else c for i, c in enumerate(text))


def srt(cues):
    fmt = lambda t: f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d},{min(999, int(round((t % 1) * 1000))):03d}"
    return "\n".join(f"{i}\n{fmt(c['start'])} --> {fmt(c['end'])}\n{c['text']}\n" for i, c in enumerate(cues, 1))


def zh_screens(doc, screens, skip=()):
    """doc.json "zh" (one Chinese line per script line; English narration with Chinese main subtitles) → subtitle cues.
    Each Chinese line is cut into screens by the same rule as doc_align (chunks) and shares the time span of its
    English line's screens in proportion to the characters on each screen: the times are estimates, not word-aligned.
    Lines in skip (burst_title lines, which show no subtitle) are left out."""
    zh, n = doc["zh"], len(doc["lines"])
    if sub_lang(doc) != "en":
        sys.exit('✗ doc.json "zh" is for English narration ("lang": "en"); a Chinese script uses "en" for the second line')
    if len(zh) != n:
        sys.exit(f"✗ doc.json zh has {len(zh)} lines, the script has {n}")
    cues = []
    for k in range(1, n + 1):
        mine = [o for o in screens if o["line"] == k]
        if not mine:
            sys.exit(f"✗ line {k} has no subtitle screen: run doc_align.py again")
        if k in skip:
            continue
        parts = chunks(zh[k - 1].strip(), "zh")
        if not parts:
            sys.exit(f"✗ doc.json zh line {k} is empty")
        weight = [max(1, len(tokens(p, "zh"))) for p in parts]
        a, span, done = mine[0]["at"], mine[-1]["end"] - mine[0]["at"], 0
        for p, w in zip(parts, weight):
            cues.append({"start": round(a + span * done / sum(weight), 3), "end": round(a + span * (done + w) / sum(weight), 3),
                         "text": screen_text(p)})
            done += w
    return cues


def clip_start(entry, beat):
    """Where a clip_sync beat starts in its take: "clip_in" when the narration was retimed after the take was made
    (longer pauses after other lines), so the lips follow the take's own timing; otherwise the beat's start."""
    return float(entry.get("clip_in", beat["start"]))


def line_cues(P, doc, skip=()):
    """One cue per script line, held for as long as that line's screens (voice.cleaned/screens.json from doc_align), with
    doc.json "en" as the text (one English line per script line, for a Chinese narration with Chinese and English subtitles); without "en"
    (an English narration with "zh") the narration itself. An empty "en" entry gives no cue: a line already in English
    (a code-switching host) is not shown twice."""
    en, n = doc.get("en") or [l["text"] for l in doc["lines"]], len(doc["lines"])   # "zh" episodes: the narration itself
    if len(en) != n:
        sys.exit(f"✗ doc.json en has {len(en)} lines, the script has {n}")
    screens = json.loads((P / "voice.cleaned/screens.json").read_text(encoding="utf-8"))
    cues = []
    for k in range(1, n + 1):
        mine = [o for o in screens if o["line"] == k]
        if not mine:
            sys.exit(f"✗ line {k} has no subtitle screen: run doc_align.py again")
        if en[k - 1].strip() and k not in skip:
            cues.append({"start": mine[0]["at"], "end": mine[-1]["end"], "text": en[k - 1].strip()})
    return cues


def en_subs(P, doc):
    """The second subtitle line for the Concat layers: line_cues, wrapped."""
    return {**EN_SUB, "cues": [{**c, "text": en_wrap(c["text"])} for c in line_cues(P, doc)]}


def write_caption_files(P, doc, out):
    """Caption files for the upload, every episode (FORMAT §4d point 4): <out>/subtitles_<narration lang>.srt is the
    episode's own voice.cleaned/final.srt (the whole narration, including a burst_title line the film shows as a title
    instead of a subtitle); with a translation one more file in that language: "en" one cue per line (line_cues), "zh"
    the same screens the film burns (zh_screens). Returns [(lang, path)]."""
    lang, files = sub_lang(doc), []
    dst = P / out / f"subtitles_{lang}.srt"
    shutil.copy(P / "voice.cleaned/final.srt", dst)
    files.append((lang, dst))
    if doc.get("en") and lang != "en":
        dst = P / out / "subtitles_en.srt"
        dst.write_text(srt(line_cues(P, doc)), encoding="utf-8")
        files.append(("en", dst))
    if doc.get("zh") and lang != "zh":
        dst = P / out / "subtitles_zh.srt"
        screens = json.loads((P / "voice.cleaned/screens.json").read_text(encoding="utf-8"))
        dst.write_text(srt(zh_screens(doc, screens)), encoding="utf-8")
        files.append(("zh", dst))
    print("subtitle files: " + "; ".join(f"{k} {p}" for k, p in files) + " (add them to YouTube by hand after uploading; steps in tools/youtube/README.md)")
    return files


def concat_layers(P, doc, beats, out, theme, plan):
    """doc.json "side" and "pills" → <out>/layers.json for tools/concat/plan2concat_mcp.py --layers, which lays
    them on their own lanes in Concat so they stay movable there (Concat does these, to depend less on
    CapCut). Nothing is burned in, so --render shows neither. Geometry is in Concat's own units:
    crop as fractions of the source, mask as fractions of the cropped picture's shorter side, transform as a scale plus
    offsets from the frame centre. Sizes and the pill font are computed here once, not in Concat.
    - "side": {"clip", "beats": [ids], "rect": [x, y, w, h] (default SIDE_RECT), "crop": [w, h, x, y] in the take
      (default: the centred full-height cut of the rect's shape), "radius" (28), "ring" (theme ring colour)}.
    - "pills": [{"beat", "text", "at": phrase in that beat, "dur" (2.0), "pos": PILL_POS key (default lower-left on a
      full-frame host beat, else center)}].
    - "chapters": {"tags": [{"beat", "text"}], "end": beat id where the tags stop (default the film's end), "number"
      (true: 第 N 章), "frame" (true: four corner brackets over the whole film)}: a tag in the upper right per chapter.
    - "punch": [{"beat" (a full-frame host beat), "at": phrase, "to": phrase (default the beat's end), "scale" (1.15)}].
    - "grain": film grain on the export, ffmpeg noise strength 1-20 (one approved episode used 7).
    - "en": English subtitles under the Chinese ones (en_subs); the Chinese screens move up to make room.
    - "zh" (with "lang": "en"): the Chinese line is the main subtitle (zh_screens, written in shell()) and the English
      narration takes the second line."""
    sd, pills = doc.get("side"), doc.get("pills", [])
    by_id, layers = {b["id"]: b for b in beats}, {"side": [], "pills": []}
    if sd:
        clip = (P / sd["clip"]).resolve()
        if not clip.exists():
            sys.exit(f"✗ missing side clip: {clip}")
        vw, vh = video_size(clip)
        x, y, w, h = sd.get("rect", SIDE_RECT)
        cw, ch, cx, cy = sd.get("crop") or [min(vw, round(vh * w / h)), vh, (vw - min(vw, round(vh * w / h))) // 2, 0]
        base = min(1920 / vw, 1080 / vh)                # scale 1 fits the take to the frame
        scale = h / (ch * base)
        ox = (x + w / 2 - 960) / 1920 - (cx + cw / 2 - vw / 2) * base * scale / 1920
        oy = (y + h / 2 - 540) / 1080 - (cy + ch / 2 - vh / 2) * base * scale / 1080
        r, ring, short = int(sd.get("radius", 28)), 6, min(cw, ch)
        geo = {"clip": str(clip), "crop": {"left": cx / vw, "top": cy / vh, "right": (vw - cx - cw) / vw, "bottom": (vh - cy - ch) / vh},
               "mask": {"shape": "rectangle", "width": cw / short, "height": ch / short, "roundness": min(1.0, r / (min(w, h) / 2))},
               "scale": round(scale, 5), "offsetX": round(ox, 5), "offsetY": round(oy, 5),
               "plate": {"color": sd.get("ring", CODE_THEMES[theme]["ring"]), "maxWidth": (w + 2 * ring) / 1920,
                         "maxHeight": (h + 2 * ring) / 1080, "radius": (r + ring) / 1080,
                         "offsetX": round((x + w / 2 - 960) / 1920, 5), "offsetY": round((y + h / 2 - 540) / 1080, 5)}}
        # one span per run of consecutive side beats: the frame stays up across their cuts. A full-narration take:
        # the span's own window of it keeps the lips on the voice.
        spans = []
        for b in sorted((by_id[i] for i in sd["beats"]), key=lambda b: b["start"]):
            if spans and abs(spans[-1]["start"] + spans[-1]["dur"] - b["start"]) < 0.05:
                spans[-1]["dur"] = round(b["start"] + b["duration"] - spans[-1]["start"], 3)
                spans[-1]["beats"].append(b["id"])
            else:
                spans.append({"beats": [b["id"]], "start": round(b["start"], 3), "dur": round(b["duration"], 3)})
        layers["side"] = [{**sp, "src": sp["start"], **geo} for sp in spans]
    if pills or doc.get("chapters"):
        font = P / out / "fonts" / "NotoSansTC-800.ttf"
        if not font.exists():
            from fontTools.ttLib import TTFont
            from fontTools.varLib import instancer
            f = instancer.instantiateVariableFont(TTFont(asset("fonts", "NotoSansTC-Variable.ttf")),
                                                  {"wght": PILL_FONT[1]})
            for rec in f["name"].names:   # Concat matches the family name: give the cut weight its own
                if rec.nameID in (1, 16):
                    rec.string = PILL_FONT[0]
            font.parent.mkdir(parents=True, exist_ok=True)
            f.save(font)
        layers["font"] = {"family": PILL_FONT[0], "path": str(font.resolve())}
    if pills:
        fill, ink = CODE_THEMES[theme]["pill"]
        for i, (t, beat) in pill_times(doc, beats).items():
            p = pills[i]
            host = by_id[beat]["source"] == "clip"
            px, py = PILL_POS[p.get("pos", "lower-left" if host else "center")]
            corner = p.get("pos") == "corner"
            if corner:   # a grade label belongs to the whole picture: from the beat's start (EP1 B19 showed it 1.4 s)
                t = 0.2
            dur = p.get("dur", round(by_id[beat]["end"] - by_id[beat]["start"] - t, 3) if corner else 2.0)
            size = CHAPTER_TAG["size"] if corner else PILL_SIZE
            # keep a long pill inside the frame (EP1 B53: 18 characters at lower-left lost its first one off the left
            # edge); width ≈ characters × font px + the pill's padding
            half = (sum(2 if ord(c) > 0x2E7F else 1 for c in p["text"]) / 2 * size * 1080 + 0.8 * size * 1080) / 2
            px = max(60 + half, min(1860 - half, px))
            layers["pills"].append({"beat": beat, "text": p["text"], "start": round(by_id[beat]["start"] + t, 3),
                                    "dur": float(dur), "fade": PILL_FADE, "size": size,
                                    "offsetX": round((px - 960) / 1920, 5), "offsetY": round((py - 540) / 1080, 5),
                                    "fill": fill, "color": ink})
    if doc.get("chapters"):
        layers["chapters"] = {**CHAPTER_TAG, "tags": chapter_spans(doc, beats)}
        if doc["chapters"].get("frame", True):
            corner_frame(P / out / "frame_corners.png")
            layers["chapters"]["frame"] = str((P / out / "frame_corners.png").resolve())
    layers["punch"] = punch_spans(doc, beats)
    if plan["second"]:   # the second line under the main subtitle (old rules only: "subs"."burn" burns one language)
        layers["en"] = en_subs(P, doc)
    if doc.get("grain"):
        layers["grain"] = max(1, min(int(doc["grain"]), 20))   # ffmpeg noise strength on the export (7 in v5)
    (P / out / "layers.json").write_text(json.dumps(layers, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"layers.json: {len(layers['side'])} side spans, {len(layers['pills'])} pills, "
          f"{len(layers.get('chapters', {}).get('tags', []))} chapters, {len(layers['punch'])} punch-ins, "
          f"{len(layers.get('en', {}).get('cues', []))} English lines → plan2concat_mcp.py --layers")


def overlays(P, doc, beats, out, theme):
    """Burn the cross-beat layers into assemble.py's per-shot segments (cut2plan's plan.json reads those; ve_visual.mp4 is
    rejoined from them), one re-encode per touched segment:
    - "pip": a talking host in a round frame over the listed beats (a full-narration TalkingPhoto take, so its lips
      follow the voice-over). {"clip", "beats": [ids], "crop": [w, h, x, y] square on the face, "d", "x", "y",
      "ring" (frame colour), "vf" (a grade for the face)}; pick beats whose lower-left corner is empty, leave gaps.
    - "sticker": a corner badge carried over the next beats, cut from the last frame of a code shot that ends on it
      (merge_bubble "badge"). {"from": beat id, "beats": [ids], "x", "y", "d"} (a round crop).
    - "wipes": [beat ids]: a torn paper sheet wipes across the cut into each listed beat (WIPE_S out, WIPE_S in).
    "side" and "pills" are not burned in: see concat_layers()."""
    seg, pp = P / out / ".segments", doc.get("pip")
    clip_of = {b["id"]: b.get("clip") for b in doc["beats"]}
    st, wipes = doc.get("sticker"), set(doc.get("wipes", []))
    if pp and not (P / pp["clip"]).exists():
        sys.exit(f"✗ missing pip clip: {P / pp['clip']}")
    sheet = seg / "wipe_sheet.png"
    if wipes:
        wipe_sheet(sheet, theme)
    badge = seg / "sticker.png"
    if st:
        r = st["d"] / 2
        sh("ffmpeg", "-v", "error", "-y", "-sseof", "-0.05", "-i", P / f"code_{theme}" / f"{st['from']}.mp4", "-frames:v", "1",
           "-vf", f"crop={st['d']}:{st['d']}:{st['x']}:{st['y']},format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':"
           f"a='if(lte(hypot(X-{r},Y-{r}),{r}-1),255,0)'", badge)
    t = 0.0
    for k, b in enumerate(beats, 1):
        f = seg / f"shot{k}.mp4"
        probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                                           "stream=r_frame_rate,time_base:format=duration", "-of", "json", f],
                                          capture_output=True, text=True, check=True).stdout)
        dur = float(probe["format"]["duration"])
        # ve_visual.mp4 is a stream-copy concat: a rewritten segment must keep its frame rate and timescale or the join drifts
        fps, scale = probe["streams"][0]["r_frame_rate"], probe["streams"][0]["time_base"].split("/")[1]
        nxt = beats[k]["id"] if k < len(beats) else None
        graph, last, inputs = [], "0:v", ["-i", f]
        n_in = 1
        # interleaved; a beat that plays the host take itself already shows the host (an outside clip, e.g. a sample
        # film, still gets the circle: 2026-10-28 lecture pilot)
        if pp and b["id"] in pp["beats"] and not (b["source"] == "clip" and clip_of.get(b["id"]) == pp["clip"]):
            inputs += ["-i", P / pp["clip"]]
            cw, ch, cx, cy = pp["crop"]
            d = max(80, min(int(pp.get("d", 280)), 1080)); x = pp.get("x", 40); y = pp.get("y", 1080 - d - 48)
            vf = (pp["vf"] + ",") if pp.get("vf") else ""
            graph += [f"[{n_in}:v]trim=start={t:.3f}:duration={dur:.3f},setpts=PTS-STARTPTS,fps={fps},crop={cw}:{ch}:{cx}:{cy},"
                      f"scale={d}:{d},{vf}format=yuva420p,geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':"
                      f"a='if(lte(hypot(X-{d / 2},Y-{d / 2}),{d / 2}-1),255,0)'[c]",
                      f"color={pp.get('ring', 'white')}:s={d + 8}x{d + 8}:r={fps}:d={dur:.3f},format=yuva420p,"
                      f"geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':a='if(lte(hypot(X-{(d + 8) / 2},Y-{(d + 8) / 2}),{(d + 8) / 2}-1),255,0)'[w]",
                      f"[{last}][w]overlay={x - 4}:{y - 4}:shortest=1[p1]", f"[p1][c]overlay={x}:{y}:shortest=1[p2]"]
            last, n_in = "p2", n_in + 1
        if st and b["id"] in st["beats"]:
            inputs += ["-loop", "1", "-i", badge]
            graph.append(f"[{last}][{n_in}:v]overlay={st['x']}:{st['y']}:shortest=1[s1]")
            last, n_in = "s1", n_in + 1
        for side, on in (("out", nxt in wipes), ("in", b["id"] in wipes and k > 1)):
            if not on:
                continue
            inputs += ["-loop", "1", "-i", sheet]
            e = (f"1920-(2060)*pow(clip((t-{dur - WIPE_S:.3f})/{WIPE_S},0,1),2)" if side == "out"
                 else f"-140-2060*(1-pow(1-clip(t/{WIPE_S},0,1),2))")
            graph.append(f"[{last}][{n_in}:v]overlay=x='{e}':y=0:shortest=1[w{side}]")
            last, n_in = f"w{side}", n_in + 1
        if graph:
            tmp = f.with_name(f"ov_{f.name}")
            sh("ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(graph), "-map", f"[{last}]",
               "-map", "0:a?", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-r", fps,
               "-video_track_timescale", scale, tmp)
            tmp.replace(f)
        t += dur
    sh("ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", seg / "list.txt", "-c", "copy",
       P / out / "ve_visual.mp4")


# bgm "duck" / "lift" / "drops" (from a study of a well-paced explainer): its music spans 21 dB
# second to second (ours 12), comes up on title cards and stops for 2-4 s about once a minute, at a question or before a
# key claim. Narration pauses are ~0.6 s (doc.json gaps), so ducking alone holds the bed down for the whole film (lecture
# pilot: 3 spans over 276 of 279 s); "lift" names the beats where the music comes back up under the voice.
DUCK_DB = (0.0, 12.0)        # dB the bed drops under speech
DUCK_RAMP, DUCK_MERGE = 0.3, 1.0   # s to duck / come back; speech gaps shorter than this stay ducked
DROP_S = (1.0, 4.0)          # seconds the music stops from the start of a dropped beat
DROP_OUT, DROP_IN = 0.1, 0.4
# A bed louder than this must duck under the narration (one episode shipped at -20 LUFS with no duck and
# the music covered the voice on headphones). Steady beds in use: -36 (vox-host FORMAT §4), -40 (a daily short series);
# louder beds always ducked: -20 with duck 6 (current-affairs episodes), -24 with duck 6 (lecture).
LOUD_BED = -30.0


def bed_check(b):
    """doc.json "bgm" → an error message when the bed is louder than LOUD_BED and does not duck, else None."""
    lufs, duck = float(b.get("lufs", -40.0)), float(b.get("duck", 0))
    if lufs > LOUD_BED and duck <= 0:
        return (f"✗ bgm lufs {lufs:g} is louder than {LOUD_BED:g} with no duck: the music will cover the narration. "
                f"Set \"duck\" (current-affairs episodes use -20 with duck 6) or lower lufs to -36 (vox-host FORMAT §4)")
    return None


def speech_spans(voice, total):
    """Spoken intervals of the narration (silencedetect -35 dB / 0.25 s, as assemble.py cuts lines), gaps < DUCK_MERGE merged."""
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(voice), "-af", "silencedetect=noise=-35dB:d=0.25", "-vn",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    quiet, start = [], None
    for m in re.finditer(r"silence_(start|end): (-?[\d.]+)", log):
        if m.group(1) == "start":
            start = float(m.group(2))
        elif start is not None:
            quiet.append((max(0.0, start), float(m.group(2))))
            start = None
    if start is not None:
        quiet.append((start, total))
    spans, t = [], 0.0
    for a, b in quiet:
        if a > t:
            spans.append([t, a])
        t = max(t, b)
    if t < total:
        spans.append([t, total])
    merged = []
    for a, b in spans:
        if merged and a - merged[-1][1] < DUCK_MERGE:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    return merged


def without(spans, holes):
    """spans minus the hole intervals (both lists of [a, b])."""
    out = [list(s) for s in spans]
    for ha, hb in holes:
        nxt = []
        for a, b in out:
            if hb <= a or ha >= b:
                nxt.append([a, b])
                continue
            if a < ha:
                nxt.append([a, ha])
            if hb < b:
                nxt.append([hb, b])
        out = nxt
    return out


def bed_gain(spans, duck, drops):
    """ffmpeg volume expression: -duck dB over each spoken span (ramping DUCK_RAMP s before / after), silent over each drop
    [a, b] (out over DROP_OUT s before a, back over DROP_IN s after b). Spans are DUCK_MERGE apart, so the ramps never add up."""
    def hump(a, b, up, down):
        return f"clip((t-{a:.3f})/{up}+1,0,1)*clip(({b:.3f}-t)/{down}+1,0,1)"
    parts = []
    if duck and spans:
        parts.append(f"pow(10,-{duck / 20:.4f}*({'+'.join(hump(a, b, DUCK_RAMP, DUCK_RAMP) for a, b in spans)}))")
    if drops:
        parts.append(f"(1-clip({'+'.join(hump(a, b, DROP_OUT, DROP_IN) for a, b in drops)},0,1))")
    return "*".join(parts)


def bgm(P, doc, total, beats=()):
    """doc.json "bgm" {"src": music file (relative to the project), "lufs": -40, "credit": "...", "duck": dB, "lift": [beat
    ids], "drops": [beat ids], "drop_s": s}: one bed under the whole narration, faded in 1.5 s and out over the last 3 s.
    -40 LUFS is the level used for a daily short series: a steady bed, no ducking. "lufs" is the
    bed before ducking. "duck" (0-12 dB) lowers the bed while the narration (voice.cleaned/audio.m4a) speaks; it comes back
    up in pauses of DUCK_MERGE s or more and over the "lift" beats (titles, demos, the close); "drops" stops the music for
    drop_s (1-4 s, default 2.5) from the start of each listed beat.
    Without duck / drops the output is the plain bed, unchanged. Returns the extra_audios entry (relative to the cut folder)."""
    b = doc["bgm"]
    if msg := bed_check(b):
        sys.exit(msg)
    src, out = (P / b["src"]).resolve(), P / "bgm" / "bgm.wav"
    out.parent.mkdir(exist_ok=True)
    err = subprocess.run(["ffmpeg", "-nostats", "-t", f"{total:.1f}", "-i", str(src), "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    gain = max(-60.0, min(float(b.get("lufs", -40.0)), -10.0)) - float(err.rsplit("I:", 1)[1].split("LUFS")[0])
    duck = max(DUCK_DB[0], min(float(b.get("duck", 0)), DUCK_DB[1]))
    drop_s = max(DROP_S[0], min(float(b.get("drop_s", 2.5)), DROP_S[1]))
    at = {x["id"]: (x["start"], x["end"]) for x in beats}
    unknown = [i for k in ("drops", "lift") for i in b.get(k, []) if i not in at]
    if unknown:
        sys.exit(f"✗ bgm drops / lift: no such beat {', '.join(unknown)}")
    drops = [(at[i][0], at[i][0] + drop_s) for i in b.get("drops", [])]
    spans = without(speech_spans(P / "voice.cleaned/audio.m4a", total), [at[i] for i in b.get("lift", [])]) if duck else []
    shape = bed_gain(spans, duck, drops)
    sh("ffmpeg", "-v", "error", "-y", "-i", src, "-t", f"{total:.3f}",
       "-af", f"afade=t=in:d=1.5,afade=t=out:st={total - 3:.3f}:d=3,volume={gain:.1f}dB"
       + (f",volume='{shape}':eval=frame" if shape else ""), "-ar", "48000", "-ac", "2", out)
    print(f"bgm {src.name} {gain:+.1f} dB" + (f", duck {duck:g} dB" if duck else "")
          + (f", {len(b['lift'])} lifted" if duck and b.get("lift") else "") + (f", {len(drops)} drops" if drops else "")
          + (f" | {b['credit']}" if b.get("credit") else ""))
    return {"path": "../bgm/bgm.wav", "start_s": 0, "track": "BGM"}


def sfx_bed(P, doc):
    """doc.json "sfx_on": the sound-effect track doc_sfx.py mixed, on its own track; off → nothing."""
    if not doc.get("sfx_on"):
        return []
    if not (P / "sfx" / "sfx_bed.wav").exists():
        sys.exit("✗ sfx_on is set but sfx/sfx_bed.wav is missing: run doc_sfx.py first")
    return [{"path": "../sfx/sfx_bed.wav", "start_s": 0, "track": "SFX_BED"}]


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):   # usage, not a "no such file" for a path named --help
        print(__doc__.strip())
        sys.exit(0 if len(sys.argv) >= 2 else 1)
    doc, P = load(sys.argv[1])
    args = sys.argv[2:]
    if "--capcut" in args:
        sys.exit("✗ --capcut was removed and no longer writes CapCut drafts: use --render for the film, or tools/concat/plan2concat_mcp.py on cut_<theme>/plan.json for a Concat project")
    theme = next((a.split("=", 1)[1] for a in args if a.startswith("--theme=")), doc.get("theme", "collage"))
    if theme not in CODE_THEMES:               # the theme names folders this script deletes and rebuilds
        sys.exit(f"✗ theme must be one of {', '.join(CODE_THEMES)}")
    name = args[args.index("--name") + 1] if "--name" in args else f"{doc['title']}_{theme}"
    try:
        series = series_of(P)
    except ValueError as e:
        sys.exit(f"✗ cannot read the series settings series.json: {e}")
    bad = subs_problems(doc, series)   # before anything is deleted or built
    if bad:
        sys.exit("✗ " + "; ".join(bad))
    subs = subtitle_plan(doc, series)   # what the burned subtitle shows; passed down, decided once
    if "--captions-only" in args:   # an episode already cut: add the caption files, touch nothing else
        if not (P / f"cut_{theme}").is_dir():
            sys.exit(f"✗ not cut yet: no cut_{theme}/; run doc_cut.py once first")
        write_caption_files(P, doc, f"cut_{theme}")
        return
    check_layers(doc)
    B = read_beats(P / "beats.json")
    beats, total = B["beats"], B["total"]
    pill_times(doc, beats)   # stop on a bad phrase before any rendering
    hits = []
    for burst in (b for b in doc["beats"] if b.get("scene") == "burst_title"):
        bb = next(b for b in beats if b["id"] == burst["id"])
        if not bb["tokens"]:
            sys.exit(f"✗ {bb['id']}: the climax line was not found in the transcript (no word timing)")
        hits.append(round(bb["start"] + bb["tokens"][0][1], 3))   # the climax word opens its line (doc_code checks)
    S = shell(P, doc, beats, total, theme, hits, subs)
    picks = P / f"picks_{theme}"
    if picks.exists():
        shutil.rmtree(picks)
    picks.mkdir()
    ve = [b["id"] for b in beats if b["source"] == "ve"]
    shots = {}
    plan = {b["id"]: b for b in doc["beats"]}
    for k, b in enumerate(beats, 1):
        if b["source"] == "clip":   # an outside clip (a TalkingPhoto host take): doc.json beat names it with "clip"
            src = P / plan[b["id"]]["clip"]
            if plan[b["id"]].get("clip_sync"):   # a full-narration take: cut this beat's window so the lips match the voice
                cut = picks / f"clip_{b['id']}.mp4"
                sh("ffmpeg", "-v", "error", "-y", "-ss", f"{clip_start(plan[b['id']], b):.3f}", "-i", src, "-t", f"{b['duration'] + 0.1:.3f}",
                   "-an", "-vf", plan[b["id"]].get("vf", "scale=1920:1080") + ",fps=30,tpad=stop_mode=clone:stop_duration=3",
                   "-c:v", "libx264",
                   "-pix_fmt", "yuv420p", "-crf", "18", cut)
                src = cut
        elif b["source"] == "code":
            src = P / f"code_{theme}" / f"{b['id']}.mp4"
        else:
            src = P / f"ve_{ve_look(doc, theme)}" / f"shot{ve.index(b['id']) + 1}.mp4"
        if not src.exists():
            sys.exit(f"✗ missing clip for {b['id']}: {src}")
        (picks / f"shot{k}.mp4").symlink_to(src)
        shots[f"shot{k}"] = 1 if k == 1 else f"{b['start']:.2f}s"
    out = f"cut_{theme}"
    if (P / out).exists():
        shutil.rmtree(P / out)
    cfg = {"clips": picks.name, "srt": "voice.cleaned/final.srt", "out": out, "stepped_fps": 0, "shots": shots,
           "max_stretch": max(1.0, min(float(doc.get("max_stretch", 1.2)), 1.5)),   # a VE clip a little short of its window slows down instead of freezing
           "shell": {"dir": S.name, "copy": ["index.html", "gsap.min.js", "fonts", "sfx", "voice.cleaned"], "video_src": "visual.mp4"},
           "timeline": {"name": name, "lines": "tts/lines.json", "audio": "voice.cleaned/audio.m4a", "lead_s": 0.45,
                        "width": 1920, "height": 1080, "fps": 30,
                        **({"sub_bg": sub_bg(doc)} if sub_bg(doc) else {}),
                        "extra_audios": [{"path": "sfx/impact.wav", "start_s": h, "track": "SFX"} for h in hits]
                                        + ([bgm(P, doc, total, beats)] if doc.get("bgm") else [])
                                        + sfx_bed(P, doc)}}
    cfg_path = P / f"cut_{theme}.json"
    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
    sh("python3", REPO / "tools/assemble/assemble.py", cfg_path)
    copy_beds(P, doc, P / out)
    if doc.get("pip") or doc.get("sticker") or doc.get("wipes"):
        overlays(P, doc, beats, out, theme)
    if any(doc.get(k) for k in ("side", "pills", "chapters", "punch", "grain", "en", "zh")):
        concat_layers(P, doc, beats, out, theme, subs)
    write_caption_files(P, doc, out)
    sh("python3", REPO / "tools/assemble/cut2plan.py", cfg_path)   # 放在 overlays() 之後：它會改寫 .segments
    if "--render" in args:
        render(P / out)
    else:
        (P / out / "ve_visual.mp4").unlink(missing_ok=True)


def copy_beds(P, doc, o):
    """把配樂與音效底複製進輸出資料夾，給殼頁面的 bgm、sfxbed 兩個 <audio> 讀（s2f-1b D5）。
    plan.json 不指到這兩份複本，指的是專案資料夾裡的原檔。"""
    if doc.get("bgm"):
        (o / "bgm").mkdir(exist_ok=True)
        shutil.copy(P / "bgm" / "bgm.wav", o / "bgm" / "bgm.wav")
    if doc.get("sfx_on"):
        (o / "sfx").mkdir(exist_ok=True)
        shutil.copy(P / "sfx" / "sfx_bed.wav", o / "sfx" / "sfx_bed.wav")


def render(o):
    """Render the cut folder's page to <o>/output.mp4; a failed render stops the script (the log is <o>/render.log).
    渲染成功後做兩段式響度校正（plan2concat_mcp.loudnorm 的預設目標值；它用字串組暫存檔名，所以傳 str）。"""
    r = hyperframes("render", o, "-o", o / "output.mp4", "--fps", "30", stdout=open(o / "render.log", "w"))
    if r.returncode:
        sys.exit(f"✗ render failed (exit {r.returncode}): {o / 'render.log'}\n{log_tail(o / 'render.log')}")
    loudnorm(str(o / "output.mp4"))
    print(f"rendered {o / 'output.mp4'}")


if __name__ == "__main__":
    main()
