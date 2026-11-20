#!/usr/bin/env python3
"""Mechanical checks for a VideoExpress storyboard (minimal format).

Usage: lint.py FILE --min 30 --max 45 --names 王生 --human "Actor 1,Actor 3"
Exit code 0 = all checks pass, 1 = at least one FAIL.
"""
import argparse
import re
import sys

TAGS = ["[REFERENCE USE]", "[IDENTITY / CONTINUITY]", "[SCENE]", "[ACTION", "[CAMERA]",
        "[LIGHT AND IMAGE]", "[PRODUCTION SOUND]", "[NEGATIVES]"]
LETTERING = re.compile(r"畫卷|字畫|書法|匾|對聯|招牌|書冊|書本|卷軸|scroll|plaque|calligraphy")


def field(block, name):
    m = re.search(r"\*\*%s:\*\*\s*(.*)" % re.escape(name), block)
    return m.group(1).strip() if m else ""


def to_sec(t):
    mm, ss = t.split(":")
    return int(mm) * 60 + int(ss)


def main():
    ap = argparse.ArgumentParser(description="Mechanical checks for a VideoExpress storyboard (minimal format). "
                                             "Exit 0 when every check passes, 1 on any FAIL.")
    ap.add_argument("file", help="the storyboard .md")
    ap.add_argument("--min", type=int, required=True, help="lower bound of the total length, seconds")
    ap.add_argument("--max", type=int, required=True, help="upper bound of the total length, seconds")
    ap.add_argument("--names", default="", help="the plan's proper names, comma-separated (never role nouns)")
    ap.add_argument("--human", default="", help="Actor N entries with a human face, comma-separated (\"Actor 1,Actor 3\")")
    a = ap.parse_args()

    text = open(a.file, encoding="utf-8").read()
    names = [n for n in a.names.split(",") if n]
    humans = [h.strip() for h in a.human.split(",") if h.strip()]
    shots = re.split(r"(?m)^## Shot (\d+)\s*$", text)[1:]
    shots = list(zip(shots[0::2], shots[1::2]))
    fails = []

    def fail(shot, code, msg):
        fails.append(f"FAIL {code} shot {shot}: {msg}")

    if not shots:
        print("FAIL L0: no '## Shot N' headings found")
        return 1
    for need in ["# Actor Portrait Image Descriptions", "# Scenes, Storyboard And Generation Prompts"]:
        if need not in text:
            fails.append(f"FAIL L0: missing heading '{need}'")

    prev_end, total = 0, 0
    for n, block in shots:
        t = field(block, "Time")
        m = re.fullmatch(r"(\d{2}:\d{2})-(\d{2}:\d{2})", t)
        if not m:
            fail(n, "L1", f"timestamp '{t}' is not 00:00-00:00")
            m2 = re.fullmatch(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})", t)
            if not m2:
                continue
            m = m2
        s, e = to_sec(m.group(1)), to_sec(m.group(2))
        if s != prev_end:
            fail(n, "L1", f"gap/overlap: starts {s}s, previous ended {prev_end}s")
        if e - s > 10 or e <= s:
            fail(n, "L2", f"shot length {e - s}s outside 1-10s")
        d = re.search(r"(\d+)", field(block, "Duration") or "x")
        if not d or int(d.group(1)) != e - s:
            fail(n, "L2", "Duration does not match Time")
        prev_end, total = e, total + (e - s)

        t2i = field(block, "Text-To-Image Prompt")
        i2v = field(block, "Image-To-Video Prompt")
        if not t2i or not i2v:
            fail(n, "L3", "missing T2I or I2V field")
            continue
        pos, ok = -1, True
        for tag in TAGS:
            p = i2v.find(tag, pos + 1)
            if p < 0:
                fail(n, "L3", f"I2V missing or out-of-order tag {tag}")
                ok = False
                break
            pos = p
        if ok:
            k = len(re.findall(r"\[ACTION [0-9.]+-[0-9.]+s\]", i2v))
            if not 1 <= k <= 4:
                fail(n, "L3", f"{k} [ACTION a-bs] segments (want 1-4)")
        # L8: hard-cut pair (07-experimental §2) — checked only when the I2V declares the cut
        if "硬切" in i2v:
            segs = re.findall(r"\[ACTION ([0-9.]+)-([0-9.]+)s\]", i2v)
            cams = [m.end() for m in re.finditer(r"\[CAMERA\]", i2v)]
            if len(segs) != 2 or len(cams) != 2:
                fail(n, "L8", f"hard cut needs exactly 2 [ACTION] and 2 [CAMERA] (got {len(segs)}/{len(cams)})")
            else:
                if any(float(b) - float(a) < 3 for a, b in segs):
                    fail(n, "L8", "hard-cut sub-shot shorter than 3s")
                if not i2v[cams[1]:].lstrip().startswith("硬切至"):
                    fail(n, "L8", "second [CAMERA] must start with 硬切至")
                if "鏡頭一" not in i2v or "鏡頭二" not in i2v:
                    fail(n, "L8", "sub-shots not labelled 鏡頭一 / 鏡頭二")
            if re.search(r"(?<!除上述一次硬切外)不剪接", i2v):
                fail(n, "L8", "hard-cut shot still says 不剪接 without the 除上述一次硬切外 exception")
            if "本次生成由兩個鏡頭組成" not in i2v:
                fail(n, "L8", "hard cut not declared in [IDENTITY / CONTINUITY]")
        # names inside quoted spoken lines are the source's own words and are allowed
        bodies = re.sub(r'"[^"]*"|「[^」]*」', "", t2i + " " + i2v)
        for nm in names:
            if nm in bodies:
                fail(n, "L4", f"character name '{nm}' in prompt body (use Actor Alias)")
        ident = i2v[i2v.find("[IDENTITY / CONTINUITY]"):i2v.find("[SCENE]")]
        sentences = re.split(r"[。；;]", ident)
        # speakers: an Actor named within 80 chars before a quoted line (§11 locks silent faces and listeners only)
        speakers = set()
        for q in re.finditer(r'"[^"]+"|「[^」]+」', i2v):
            speakers.update(re.findall(r"Actor \d+", i2v[max(0, q.start() - 80):q.start()])[-1:])
        for h in humans:
            if h in speakers:
                continue
            hp = re.compile(re.escape(h) + r"(?!\d)")
            mine = [x for x in sentences if hp.search(x)]
            if not mine:
                continue
            if f"{h} 的臉全程不可見" in ident:
                continue  # §11 face-not-visible sentence, verbatim
            if re.search(r"臉[^。]{0,6}(不朝向|側過|背對)", "。".join(mine)):
                fail(n, "L5", f"{h}: vague face-visibility wording; use '{h} 的臉全程不可見。' or add the lock")
                continue
            if not any("嘴" in x for x in mine):
                fail(n, "L5", f"{h} face visible but no mouth-lock sentence")
        # L9: a spoken line is found by ve-runner only through the English wrap `says in …: "…"` (02-modes §0.1);
        # a 繁中 wrap (以…語氣說："…") renders silent. And no caption words anywhere in the I2V, not even negated (01-core §10)
        for q in re.finditer(r'"[^"]+"|「[^」]+」', i2v):
            if not re.search(r'says in [^:"]*:\s*$', i2v[max(0, q.start() - 160):q.start()]):
                fail(n, "L9", f"quoted {q.group(0)[:24]}… not in a `says in <tone>, <accent>:` wrap (a spoken line "
                          "renders silent; quoted on-screen lettering is allowed only when the user asked for text)")
        cw = re.search(r"字幕|畫面文字|subtitle|caption|lower third|text overlay|title card", i2v, re.I)
        if cw:
            fail(n, "L9", f"caption word '{cw.group(0)}' in the I2V (it summons burned-in text even when negated)")
        if "無文字" not in t2i and "No text" not in t2i:
            fail(n, "L6", "T2I lacks the 無文字 cleanliness clause")
        lm = LETTERING.search(t2i)
        if lm and "空白" not in t2i and "blank" not in t2i:
            fail(n, "L7", f"lettering-prone object '{lm.group(0)}' not specified blank")

    if not a.min <= total <= a.max:
        fails.append(f"FAIL L1: total {total}s outside {a.min}-{a.max}s")
    for f in fails:
        print(f)
    print(f"{len(shots)} shots, {total}s, {len(fails)} fail(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
