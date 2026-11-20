"""Acted live-action scene (one room, lipsync dialogue) -> ve-runner run sheet. The rules live here, not in memory.

  python3 drama_sheet.py <drama.json> [-o storyboard.md] [--speech-in-prompt]

Rules enforced (sources: 02-modes.md §4.5 "Acted live scenes", 01-core.md §3 dialogue length, §11 closed cast):
- the style line opens every prompt; shots with no character drop "shot on a cinema camera" (it drew a camera 4 times)
- each character's bible line and the location line are pasted word for word ({CODE} in the image text)
- framing comes first; a set master (empty-room image) only on wide / full / medium shots, never on close-ups,
  inserts or over-the-shoulder shots (it pulls them back to a wide), unless the shot sets "force_set"
- a spoken line: one speaker per shot, prefixed "Right from the first second," (lipsync clips run about 4 s),
  length capped by the shot's seconds (01-core.md §3, narrative shape)
- no line: "No dialogue; nobody speaks."; every video prompt ends with the keep line, the sound, no music/subtitles/text
- --speech-in-prompt (ve_runner.py --speech-in-prompt, VE speaks the line itself, no Lipsync): the line is cut at
  「，。？！」 into 2 s segments of <= 8 characters, each segment repeats the full "<WHO> says in <tone> accent: "...""; then an
  optional action segment ("act") and a closing segment of the speaker's own small motion ("end", else the text after
  the quote, else "<WHO> holds still."), at least 1 s. Words before "says" (lead) are dropped with a warning: put them in
  "act" or "end". Tested 2026-11-08 (segmenting test): 3-4 characters/s
  (dialogue.md:96) still plans the segments; VE speaks ~4-5 characters/s and never speeds up, so a longer segment spills over;
  never write the speaker looking or turning to someone in act/end (it drew a second person 2/2).
  Line length (2026-11-09 long-line test; dialogue.md:108-114 says 12-15 characters / 6 s and 15-18 characters / 8 s,
  too many here): 12 characters needs an 8 s shot (8 s two segments 2/2 ended >= 1 s early; 6 s 1/6), 13 characters or more stops: split
  it across two shots of <= 11 characters each (dialogue.md:129; 16 characters in 8 s 0/4, 2 of 4 drew a second person; 6 s 11 characters 3/4).
  Start frame: have the speaker already facing the listener or the camera; a frame that needs a head turn first starts
  the line 1-2 s later (D17 0.9-3.2 s vs D14 0-0.8 s), and no wording fixes that.

drama.json:
{
  "style": "Photorealistic cinematic live-action, real people, natural skin texture, shot on a cinema camera, 35mm lens, ...",
  "location": "Indoors in a dim 1890s ... Soft warm morning daylight from a paper-paned lattice window falls from frame right.",
  "accent": "Taiwanese Mandarin",
  "actors": {"1": "陳朝琛 three-view sheet (uploaded master)", "3": "empty bedroom seen from the doorway (uploaded set master)"},
  "characters": {"CHEN": {"actor": 1, "bible": "CHEN — Han Chinese man of about forty, ..."}},
  "sets": {"roomA": 3},
  "shots": [{
    "id": "D5", "dur": 6, "slug": "she calls from the doorway", "beat": "小美站在門口：「阿明，下來。」",
    "framing": "Medium close-up, waist up, eye level.",
    "image": "{XIAOMEI}, standing in an open dark wooden doorway, ...",
    "location": true,              # true = the location line; false = none (object shots, other places); or a custom string
    "after": "Behind her only the dark door frame ...; nothing outdoors.",
    "cast": ["XIAOMEI"], "set": null,
    "motion": "CHEN frowns in his sleep ...",                       # silent shots
    "line": {"who": "XIAOMEI", "lead": "looking toward the bed", "tone": "calm, firm", "text": "阿明，下來。"},
    "act": "CHEN stands frozen by the table.",   # optional, --speech-in-prompt only: action after the line
    "end": "She sets the basin down.",          # optional, --speech-in-prompt only: closing motion of the speaker
    "camera": "Camera locked.",   # default; "" when the motion text moves the camera itself
    "keep": "...",                # optional override of the keep line
    "sound": "her voice, quiet room tone"
  }]
}
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HEAD = "Motion starts on the very first frame: no static opening, no slow start, no fade-in."
KEEP = "Keep faces, hair, outfits and props identical to the start image; the room stays indoors."
KEEP_EMPTY = "Keep the framing identical to the start image; no person appears."
# "No subtitles." removed 2026-11-08: with --speech-in-prompt it drew burned-in captions (9/10 with it, 0/14 without).
# "No on-screen text." stays.
TAIL = "No music. No on-screen text."
SILENT = "No dialogue; nobody speaks."
END = "Dynamic composition, subject fills the frame."
CAMERA_PHRASE = " shot on a cinema camera,"
# 01-core.md §3 dialogue length, Shape A (narrative): hard ceiling in 字 per shot length
ZH_CAP = {5: 15, 6: 18, 8: 20, 9: 22, 10: 25}
SEG_MAX = 8      # 字 per 2 s segment: 3-4 字/秒 (dialogue.md:96), re-measured 2026-11-08 (~4.1 字/秒)
SEG_SEC = 2
SPOKEN = re.compile(r'^(?P<lead>.*?)\bsays in (?P<tone>an? [^:"]+?) accent:\s*"(?P<text>[^"]+)"\s*(?P<after>.*)$', re.S)
WHO = re.compile(r"^([A-Z][A-Z-]+)\b")
WIDE = re.compile(r"^(wide|extreme wide|full|medium shot|medium wide|establishing)", re.I)
CJK = re.compile(r"[一-鿿]")


class SheetError(ValueError):
    pass


def zh_cap(dur: int) -> int:
    keys = [k for k in sorted(ZH_CAP) if k <= dur]
    return ZH_CAP[keys[-1]] if keys else 12  # under 5 s: below the table; stay under the 5 s range


def t2i(d: dict, s: dict) -> str:
    chars = d["characters"]
    style = d["style"] if s.get("cast") else d["style"].replace(CAMERA_PHRASE, "")
    loc = s.get("location", True)
    loc = d["location"] if loc is True else (loc or "")
    body = " ".join(x for x in (s["framing"], s["image"], loc, s.get("after", "")) if x)
    for code, c in chars.items():  # {CODE} may sit in the framing sentence too ("Close-up: … reflection, {CHEN}, …")
        body = body.replace("{" + code + "}", c["bible"])
    left = re.findall(r"\{([A-Z][A-Z-]*)\}", body)
    if left:
        raise SheetError(f"{s['id']}: unknown character {left}")
    return f"{style} {body}" + ("" if body.endswith(END) else f" {END}")


def split_line(text: str) -> list[str]:
    """Cut at 「，。？！」 and merge neighbours while the segment stays <= SEG_MAX 字."""
    parts = [p for p in re.findall(r"[^，。？！]+[，。？！]?", text) if p.strip()]
    segs: list[str] = []
    for p in parts:
        if segs and len(CJK.findall(segs[-1] + p)) <= SEG_MAX:
            segs[-1] += p
        else:
            segs.append(p)
    return segs


def spoken_parts(d: dict, s: dict) -> dict | None:
    """who / tone ("a calm, firm Taiwanese Mandarin") / text / lead / after, from "line" or from a "says in" motion."""
    line = s.get("line")
    if line:
        return {"who": line["who"], "tone": f'a {line["tone"]} {d.get("accent", "Taiwanese Mandarin")}',
                "text": line["text"], "lead": line.get("lead", ""), "after": line.get("after", "")}
    m = SPOKEN.match(s.get("motion", ""))
    if not m:
        return None
    w = WHO.match(m["lead"])
    if not w:
        raise SheetError(f"{s['id']}: --speech-in-prompt needs the speaker code first in motion (\"XIAOMEI ... says in\")")
    lead = m["lead"][w.end():].strip(" ,")
    lead = re.sub(r"(,?\s*(then|and))$", "", lead).strip(" ,")
    return {"who": w[1], "tone": m["tone"], "text": m["text"], "lead": lead, "after": m["after"].strip()}


def i2v_segmented(d: dict, s: dict, warn: list[str]) -> tuple[str, bool] | None:
    sp = spoken_parts(d, s)
    if not sp:
        return None
    dur, segs = int(s["dur"]), split_line(sp["text"])
    for g in segs:
        if len(CJK.findall(g)) > SEG_MAX:
            raise SheetError(f"{s['id']}: segment \"{g}\" has {len(CJK.findall(g))} characters, over {SEG_MAX} per {SEG_SEC} s "
                             "(dialogue.md:96); add a comma where it can pause, or shorten")
    e = SEG_SEC * len(segs)
    if dur - e < 1:
        raise SheetError(f"{s['id']}: {len(segs)} segments need {e} s + 1 s closing, the shot is {dur} s")
    if sp["lead"] and not (s.get("act") or s.get("end")):
        warn.append(f"{s['id']}: dropped \"{sp['lead']}\" before the line; put it in \"act\"/\"end\" if it matters")
    n = len(CJK.findall(sp["text"]))
    if n >= 13:
        raise SheetError(f"{s['id']}: {n} characters; split the line across two shots of <= 11 characters each "
                         "(16 characters in an 8 s shot: 0/4 ended with 1 s to spare; dialogue.md:129)")
    if n == 12 and dur < 8:
        raise SheetError(f"{s['id']}: 12 characters need an 8 s shot, this one is {dur} s (6 s: 1/6 ended with 1 s to spare)")
    end = s.get("end") or sp["after"] or f"{sp['who']} holds still."
    out = [f'[ACTION {i * SEG_SEC}-{(i + 1) * SEG_SEC}s] {sp["who"]} says in {sp["tone"]} accent: "{g}"'
           for i, g in enumerate(segs)]
    rem = dur - e
    if s.get("act") and rem >= 2:
        close = max(1, rem // 2)
        out.append(f"[ACTION {e}-{dur - close}s] {s['act']}")
        e = dur - close
    elif s.get("act"):
        warn.append(f"{s['id']}: no room for \"act\" ({rem} s left after the line); dropped")
    out.append(f"[ACTION {e}-{dur}s] {end}")
    return " ".join(out), True


def i2v(d: dict, s: dict, segmented: bool = False, warn: list[str] | None = None) -> tuple[str, bool]:
    if segmented:
        seg = i2v_segmented(d, s, warn if warn is not None else [])
        if seg:
            return _wrap(d, s, *seg)
    line = s.get("line")
    if line:
        lead = f", {line['lead']}," if line.get("lead") else ""
        body = (f'Right from the first second, {line["who"]}{lead} says in a {line["tone"]} {d.get("accent", "Taiwanese Mandarin")} '
                f'accent: "{line["text"]}"' + (f" {line['after']}" if line.get("after") else ""))
        spoken = True
    else:
        body = s["motion"]
        spoken = "says in" in body
        if spoken:
            body = "Right from the first second, " + body
    return _wrap(d, s, body, spoken)


def _wrap(d: dict, s: dict, body: str, spoken: bool) -> tuple[str, bool]:
    camera = s.get("camera", "Camera locked.")
    keep = s.get("keep") or (KEEP if s.get("cast") else KEEP_EMPTY)
    parts = [f"{s['id']} — {s['slug']}.", d["style"], HEAD]
    if camera and not body.startswith("Camera"):
        parts.append(camera)
    parts.append(body)
    if not spoken:
        parts.append(SILENT)
    parts += [keep, f"Sound: {s['sound']}.", TAIL]
    return " ".join(parts), spoken


def cast_of(d: dict, s: dict) -> list[str]:
    actors = [f"Actor {d['characters'][c]['actor']}" for c in s.get("cast", [])]
    if s.get("set"):
        if not WIDE.match(s["framing"]) and not s.get("force_set"):
            raise SheetError(f"{s['id']}: set master on a non-wide shot ({s['framing'].split('.')[0]}): it pulls the shot "
                             "back to a wide (02-modes.md §4.5); drop the set or add \"force_set\": true")
        actors.append(f"Actor {d['sets'][s['set']]}")
    return actors


def check_line(s: dict, text: str):
    n = len(CJK.findall(text))
    cap = zh_cap(int(s["dur"]))
    if n > cap:
        raise SheetError(f"{s['id']}: line has {n} characters, over the {cap}-character ceiling for {s['dur']} s (01-core.md §3)")


def render(d: dict, segmented: bool = False, warn: list[str] | None = None) -> str:
    out = ["# Actor Portrait Image Descriptions"] + [f"Actor {k}: {v}" for k, v in sorted(d["actors"].items(), key=lambda x: int(x[0]))]
    out += ["", "# Scenes, Storyboard And Generation Prompts"]
    ids = set()
    for n, s in enumerate(d["shots"], 1):
        if s["id"] in ids:
            raise SheetError(f"duplicate shot id {s['id']}")
        ids.add(s["id"])
        if not 1 <= int(s["dur"]) <= 10:
            raise SheetError(f"{s['id']}: {s['dur']} s is outside VE's 1-10 s")
        v, spoken = i2v(d, s, segmented, warn)
        said = re.findall(r'(?:^|\] |, )([A-Z][A-Z-]*)[^\[]*?says in [^:"]*:\s*"([^"]+)"', v)
        lines = re.findall(r'says in [^:"]*:\s*"([^"]+)"', v)
        if len(lines) > 1 and not (segmented and len({w for w, _ in said}) == 1 and len(said) == len(lines)):
            raise SheetError(f"{s['id']}: {len(lines)} spoken lines; one speaker per shot")
        if lines:
            check_line(s, "".join(lines))
        cast = cast_of(d, s)
        out += [f"## Shot {n}", f"- **Beat:** {s['id']} | {s.get('beat', s['slug'])}", f"- **Duration:** {s['dur']}s",
                f"- **Cast:** {', '.join(cast) if cast else 'none'}", f"- **Text-To-Image Prompt:** {t2i(d, s)}",
                f"- **Image-To-Video Prompt:** {v}", ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("drama")
    ap.add_argument("-o", "--out")
    ap.add_argument("--speech-in-prompt", action="store_true",
                    help="VE speaks the line itself (ve_runner.py --speech-in-prompt): 2 s segments, see the docstring")
    a = ap.parse_args()
    p = Path(a.drama).resolve()
    try:   # one line, not a traceback (same wording as doc_common.read_json)
        d = json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"✗ {p}: no such file")
    except UnicodeDecodeError:
        sys.exit(f"✗ {p}: not UTF-8 text")
    except OSError as e:
        sys.exit(f"✗ {p}: cannot read it ({e.strerror or e.__class__.__name__})")
    except json.JSONDecodeError as e:
        sys.exit(f"✗ {p}: not valid JSON (line {e.lineno}, column {e.colno}: {e.msg})")
    warn: list[str] = []
    try:
        md = render(d, a.speech_in_prompt, warn)
    except SheetError as e:
        sys.exit(f"✗ {e}")
    for w in warn:
        print(f"! {w}")
    out = Path(a.out) if a.out else Path(a.drama).with_name("storyboard.md")
    out.write_text(md, encoding="utf-8")
    print(f"{out}: {len(d['shots'])} shots, {sum(int(s['dur']) for s in d['shots'])} s")


if __name__ == "__main__":
    main()
