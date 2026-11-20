"""VE beats → ve-runner run sheet (storyboard_<look>.md in the project).

  python3 doc_runsheet.py <project>/doc.json [--theme=collage|live|lecture-<mode>]
The VE look is doc_themes.ve_look(): doc.json "ve_look", else flat for lecture-*, else the theme itself.
doc.json "shots": {key: {"t2i": [scene paragraph, setting paragraph], "scene", "ident", "acts": [[from, to, text], ...]
(fractions of the clip), "camera"}}; a VE beat names its shot with "shot". The theme's style block is appended to the
image prompt; durations come from beats.json (gen_seconds). Keep the camera locked-off: moves walked people out of frame
and pull-backs dissolved the scene into blank paper (2026-10-11).
--estimate[=CPS]: no beats.json yet (S1 voice still running), so VE can start in parallel: each VE beat's length is
guessed from its share of the line at CPS characters/second (default 5) plus the gap after it, rounded up plus 1 s of margin
(2026-10-22 job 1-13: 15 shots, every guess ≥ the aligned length; spoken rate there was about 4.9 chars/s incl. gaps).
Written to beats_est.json, never beats.json (doc_align writes that; a stale one would be read as aligned).
Run (ve-runner folder): python3 ve_runner.py <storyboard> --no-cc --image-type <theme image_type> [--creative] --auto-pick
"""
import json, math, re, sys

from doc_common import load, read_beats
from doc_themes import VE_THEMES, ve_look, ve_theme


PEOPLE = re.compile(r",[^,:]*\bpeople\b[^,]*,")   # the style block's own call for people (flat: "friendly simplified people …")


def style_for(sh, th):
    """The theme's style block; a shot with "no_people": true drops its people clause (the flat block's
    "friendly simplified people" put smiling bystanders in an empty vault twice, whatever the scene text said)."""
    return PEOPLE.sub(",", th["style"]) + " No people, no figures, no hands unless the scene names one." if sh.get("no_people") else th["style"]


def i2v(sh, L, th):
    acts = " ".join(f"[ACTION {round(a * L)}-{round(b * L)}s] {t}" for a, b, t in sh["acts"])
    return (f"[REFERENCE USE] Use the supplied image as the exact opening frame for a {L}-second continuous shot. "
            f"[IDENTITY / CONTINUITY] {sh['ident']}. [SCENE] {sh['scene']}, as {th['medium']}. {acts} [CAMERA] {sh['camera']} "
            f"[LIGHT AND IMAGE] Maintain the {th['look']}. [PRODUCTION SOUND] Silence, no speech or music. "
            f"[NEGATIVES] No {th['neg']}, cuts or transitions.")


def estimate(doc, cps=5.0):
    """VE beats with gen_seconds guessed from the script: zh only (character count)."""
    if doc.get("lang", "zh") != "zh":
        sys.exit("✗ --estimate counts Chinese characters; lang must be zh")
    L, B = [l["text"] for l in doc["lines"]], doc["beats"]
    gaps = doc.get("gaps", {})
    gap_after = {int(k): v for k, v in gaps.get("after", {}).items()}
    out = []
    for i, b in enumerate(B):
        if b["source"] != "ve":
            continue
        n = b["lines"][0]
        t = L[n - 1]
        s0 = t.find(b["from"]) if "from" in b else 0
        nxt = B[i + 1] if i + 1 < len(B) else None
        if nxt and nxt["lines"][0] == n and "from" in nxt:   # the next beat cuts in mid-line: this beat ends there
            seg, gap = t[s0:t.find(nxt["from"])], 0.0
        else:
            seg, gap = t[s0:], gap_after.get(b["lines"][-1], gaps.get("default", 0.3))
        seg += "".join(L[m - 1] for m in b["lines"][1:])
        dur = len(re.sub(r"[^一-鿿]", "", seg)) / cps + gap
        gen = math.ceil(dur + 0.1) + 1
        if gen > 10:
            sys.exit(f"✗ {b['id']}: estimated {gen}s > VE's 10 s; split the beat")
        out.append({"id": b["id"], "source": "ve", "start": 0.0, "end": round(dur, 2), "text": seg,
                    "duration": round(dur, 2), "gen_seconds": max(3, gen)})
    return out


def main():
    doc, P = load(sys.argv[1])
    theme = next((a.split("=", 1)[1] for a in sys.argv[2:] if a.startswith("--theme=")), doc.get("theme", "collage"))
    look = ve_look(doc, theme)
    if look not in VE_THEMES:
        sys.exit(f"✗ VE look must be one of {', '.join(VE_THEMES)} (doc.json ve_look, or the theme): {look}")
    try:
        th = ve_theme(look, doc.get("palette"))
    except ValueError as e:
        sys.exit(f"✗ {e}")

    def mmss(t):
        return f"{int(t // 60):02d}:{int(t % 60):02d}"
    spec = {b["id"]: b for b in doc["beats"]}
    est = next((a for a in sys.argv[2:] if a.startswith("--estimate")), None)
    if est:
        beats = estimate(doc, float(est.split("=", 1)[1]) if "=" in est else 5.0)
        (P / "beats_est.json").write_text(json.dumps({"estimated": True, "beats": beats}, ensure_ascii=False, indent=1))
    else:
        beats = [b for b in read_beats(P / "beats.json")["beats"] if b["source"] == "ve"]
    md = [f"# {doc['title']} — VE shots ({look}{' / ' + doc['palette'] if doc.get('palette') else ''}; image type {th['image_type']}; timing from {'beats_est.json (estimate)' if est else 'beats.json'})", "",
          "# Scenes, Storyboard And Generation Prompts"]
    for k, b in enumerate(beats, 1):
        sh, L = doc["shots"][spec[b["id"]]["shot"]], b["gen_seconds"]
        md += [f"## Shot {k}", f"- **Beat:** {b['id']} | {b['text']}", f"- **Time:** {mmss(b['start'])}-{mmss(b['end'])}",
               f"- **Duration:** {L}s", "- **Cast:** none",
               f"- **Text-To-Image Prompt:** {' '.join(sh['t2i'] + [style_for(sh, th)])}", f"- **Image-To-Video Prompt:** {i2v(sh, L, th)}", ""]
    out = P / f"storyboard_{look}.md"
    out.write_text("\n".join(md), encoding="utf-8")
    flags = "--creative " if th["image_type"] == "other" else ""
    print(f"{out}: {len(beats)} shots ({', '.join(f'{b['id']}={b['gen_seconds']}s' for b in beats)})")
    print(f"run: python3 ve_runner.py {out} --no-cc --image-type {th['image_type']} {flags}--auto-pick")


if __name__ == "__main__":
    main()
