"""Script checks for a vox-host doc.json (formats/vox-host/FORMAT.md「機器檢查」).

  python3 doc_lint.py <doc.json> [--off rule ...]     exit 1 and one line per problem; exit 2 on an unknown rule;
                                                      a doc.json that is missing or not valid JSON: one line, exit 1
  python3 doc_lint.py <doc.json> --beats <beats.json>  also report on-screen text held too short to read or shown too late (after doc_align)
When the script passes and the user has not approved this narration yet (doc_approval.py), a `Next:` line follows
`doc_lint: ok`: show the user the narration and the beat table, then doc_tts.py --script-approved once they say yes.

Five reports never fail the doc (FORMAT §9): ai_phrasing (AI-sounding narration, FORMAT §4), peak_weight (generated shots so
many that the high points cannot stand out), read_time and late_reveal (both need beats.json) and vs_prev (this episode against the last three
episodes, found as the sibling folders numbered one, two and three less).

make_doc.py ends with `doc_lint.check(doc)`. Rules and their numbers come from the author's series spec (SERIES.md「時代配色與畫面多樣性」)
and episode 10's make_doc asserts; a series turns one off or changes its parameter, e.g. lint(doc, {**DEFAULT, "quote_card_cap": 8}).
"""
import argparse, math, re, sys
from collections import Counter
from pathlib import Path

import doc_approval
import doc_common
import doc_facts

DEFAULT = {
    "no_em_dash": "—",
    "zh_heteronyms": "熟",            # characters Qwen TTS misreads; rewrite the line (Chinese docs only).
                                     # 「著」is handled by the pronunciation table (tools/tts/lexicon.json), not here
    "quote_card_cap": 12,
    "quote_card_run": 2,
    "banned_scenes": ["seed_dot", "split_duel"],
    # cover, timeline and burst_title are in every episode, so they do not count as a fresh scene; object_draw is only the
    # closing image (FORMAT §3, 2026-11-03: line drawings put in to meet this rule looked bare)
    "needs_fresh_scene": ["cover", "timeline", "quote_card", "compare", "burst_title", "object_draw"],
    "from_in_line": True,
    "lines_covered": True,
    "ids_exist": ["pip.beats", "wipes", "side.beats", "pills[].beat"],
    "shots_match": True,
    "facts": True,                   # doc.json "facts": facts.md beside it; no key, no check
    "map_base": True,                # map_route with a base map: stops inside the crop, clear
                                     # of the subtitles, never on a side-layout beat; a crop narrower than 900 px only warns
}


def map_base(doc):
    """Problems with map_route beats that sit on a base map; a soft crop (narrower than 900 map pixels) is printed, not failed."""
    out, side = [], set(doc.get("side", {}).get("beats", []))
    for b in doc["beats"]:
        B = b.get("params", {}).get("base") if b.get("scene") == "map_route" else None
        if not B:
            continue
        cx, cy, cw, ch = B["crop"]
        s = min(1920 / cw, 1080 / ch)
        oy = (1080 - ch * s) / 2
        if b["id"] in side:
            out.append(f"map_base: {b['id']} has a base map and is in the side layout (side.beats): the map would be shrunk")
        for o in b["params"].get("stops", []):
            if not (cx <= o["x"] <= cx + cw and cy <= o["y"] <= cy + ch):
                out.append(f"map_base: {b['id']} \"{o['name']}\" ({o['x']}, {o['y']}) is outside the crop {B['crop']}")
            elif not 150 <= (y := oy + (o["y"] - cy) * s) <= 820:
                out.append(f"map_base: {b['id']} \"{o['name']}\" is at y={y:.0f} on screen; keep it within 150–820 (above the subtitles)")
        if cw < 900:
            print(f"⚠ map_base: {b['id']} crop is only {cw} px wide and will blur when scaled up")
    return out


def _ids(doc, path):
    """Beat ids listed at a dotted path such as "pip.beats", or "pills[].beat" (one key of each item in a list);
    missing sections list nothing."""
    if "[]." in path:
        head, key = path.split("[].")
        return [x[key] for x in _ids(doc, head) if isinstance(x, dict) and key in x]
    v = doc
    for k in path.split("."):
        if not isinstance(v, dict) or k not in v:
            return []
        v = v[k]
    return list(v)


def lint(doc, rules=DEFAULT, base=None):
    """Every problem, one line each; base is the episode folder (facts.md is relative to it; default: the current folder)."""
    out = ["subtitle settings: " + m for m in doc_common.subs_problems(doc, doc_common.series_of(base or Path.cwd()))]
    out += doc_common.speaker_problems(doc)   # the files are checked when they are read: voices are often designed after F1
    lines = [x["text"] for x in doc["lines"]]
    beats = doc["beats"]
    code_scenes = [b.get("scene") for b in beats if b["source"] == "code"]
    for name, p in rules.items():
        if name == "no_em_dash":
            out += [f"no_em_dash: line {n}" for n, t in enumerate(lines, 1) if any(c in t for c in p)]
        elif name == "zh_heteronyms":
            if doc.get("lang") == "zh":
                out += [f"zh_heteronyms: line {n} \"{c}\"" for n, t in enumerate(lines, 1) for c in p if c in t]
        elif name == "quote_card_cap":
            k = code_scenes.count("quote_card")
            if k > p:
                out.append(f"quote_card_cap: {k} cards > {p}")
        elif name == "quote_card_run":
            run = 0
            for b in beats:
                run = run + 1 if b.get("scene") == "quote_card" else 0
                if run > p:
                    out.append(f"quote_card_run: {b['id']} is quote card {run} in a row > {p}")
        elif name == "banned_scenes":
            out += [f"banned_scenes: {b['id']} {b['scene']}" for b in beats if b.get("scene") in p]
        elif name == "needs_fresh_scene":
            if not set(code_scenes) - set(p):
                out.append(f"needs_fresh_scene: only {', '.join(sorted(set(code_scenes)))}, no fresh scene")
        elif name == "from_in_line":
            for b in beats:
                if "from" in b and not (b["lines"][0] <= len(lines) and b["from"] in lines[b["lines"][0] - 1]):
                    out.append(f"from_in_line: {b['id']} \"{b['from']}\" is not in line {b['lines'][0]}")
        elif name == "lines_covered":
            out += [f"lines_covered: {b['id']} points to line {n}, but there are only {len(lines)} lines"
                    for b in beats for n in b["lines"] if not 1 <= n <= len(lines)]
            missed = sorted(set(range(1, len(lines) + 1)) - {n for b in beats for n in b["lines"]})
            if missed:
                out.append(f"lines_covered: no beat for line(s) {', '.join(map(str, missed))}")
        elif name == "ids_exist":
            ids = {b["id"] for b in beats}
            out += [f"ids_exist: {i} in {path} is not a beat" for path in p for i in _ids(doc, path) if i not in ids]
        elif name == "shots_match":
            used = {b["shot"] for b in beats if b["source"] == "ve"}
            out += [f"shots_match: {s} {'is not defined' if s in used else 'is not used'}" for s in sorted(used ^ set(doc.get("shots", {})))]
        elif name == "facts":
            out += doc_facts.check(doc, base or Path.cwd())
        elif name == "map_base":
            out += map_base(doc)
        else:
            raise KeyError(name)
    return out


# AI-sounding narration (FORMAT §4「AI 味」): a report for the writer, never a failure; quoted scripture
# and word studies use some of these words legitimately. The contrast pattern 「不是 X，是 Y」 is listed only when an
# episode has it more than AI_CONTRAST_MAX times.
AI_PHRASES = {
    "預告／自問自答": r"這筆帳|算帳|問題來了|重點來了|有趣的是|答案是|先說結論|你可能會問|引出一個問題|我們來看|一起來看|來看看",
    "故作深刻": r"本質|核心|底層|邏輯|張力|維度|框架|脈絡|意味著|映照|隱喻|留白|拼圖|伏筆|交織|旅程|鏡頭",
    "分析腔": r"拆(?!毀)|做法|系統|機制|公式|失真|路徑|閉環|賦能|抓手|槓桿|變數",
    "收束套語": r"說到底|歸根結底|換句話說|也就是說|說穿了|某種程度上|值得一提|不得不說|耐人尋味|諷刺的是|弔詭",
    "說教": r"記住|別忘了|你注意|你會發現|想一想|問問自己|這提醒我們|這告訴我們|我們應該",
}
AI_CONTRAST = r"不是[^，。？！；：]{1,14}[，；]\s*(而)?是|從來不是|不只是.{1,12}更是|與其說"
AI_CONTRAST_MAX = 1
AI_KIND_EN = {"預告／自問自答": "teaser / self-answered question", "故作深刻": "fake depth", "分析腔": "analyst jargon",
              "收束套語": "stock wrap-up", "說教": "preaching"}   # how each AI_PHRASES kind is named in the report


def ai_phrasing(doc):
    """One line per AI-sounding phrase in a Chinese doc's narration (FORMAT §4); [] for other languages."""
    if doc.get("lang") != "zh":
        return []
    lines = [x["text"] for x in doc["lines"]]
    out = [f"ai_phrasing: line {n} {AI_KIND_EN[kind]} 「{m.group(0)}」: {t}"
           for kind, pat in AI_PHRASES.items() for n, t in enumerate(lines, 1) for m in [re.search(pat, t)] if m]
    contrast = [(n, t) for n, t in enumerate(lines, 1) if re.search(AI_CONTRAST, t)]
    if len(contrast) > AI_CONTRAST_MAX:
        out += [f"ai_phrasing: line {n} 不是…是… contrast ({len(contrast)} lines in this episode, at most {AI_CONTRAST_MAX}): {t}"
                for n, t in contrast]
    return sorted(out, key=lambda s: int(s.split()[2]))


def host_layout(doc):
    """How many beats show the host which way (lecture-style D3: a report, never a failure)."""
    side, pip = set(doc.get("side", {}).get("beats", [])), set(doc.get("pip", {}).get("beats", []))
    n = {"full": 0, "side": 0, "pip": 0, "none": 0}
    for b in doc["beats"]:
        n["full" if b.get("source") == "clip" else "side" if b["id"] in side else "pip" if b["id"] in pip else "none"] += 1
    return n


# peak_weight (2026-11-20, 3 films read line by line, 43 films counted): the last 20 episodes of a 120-episode series put
# generated shots on 16–34% of the lines, current-affairs films 0–25%; the one film where they hid the high point had 43%.
GEN_SHARE_MAX = 0.40


def _generated(b):
    """A generated shot: a VE beat, or a clip that is not the host."""
    return b.get("source") == "ve" or (b.get("source") == "clip" and "host" not in str(b.get("clip", "")))


def peak_weight(doc):
    """Generated shots on more than GEN_SHARE_MAX of the lines read as the background and the high points cannot stand out
    (a report, never a failure). Tried and dropped: "a card main-line beat between two heavier beats", which fired on 6 of
    the last 20 episodes of a series the user had accepted."""
    gen = {n for b in doc["beats"] if _generated(b) for n in b["lines"]}
    share = len(gen) / max(len(doc["lines"]), 1)
    if share <= GEN_SHARE_MAX:
        return []
    return [f"peak_weight: generated shots on {len(gen)} of {len(doc['lines'])} lines ({share:.0%}, over "
            f"{GEN_SHARE_MAX:.0%}): they read as the background; keep them for the high points"]


# Reading time: after text finishes coming in, hold it (characters / 4.5 + 1.5) s in Chinese,
# (letters / 15 + 1.5) s in English. Narration reads most quote cards aloud, so this is a report for the reviewer.
READ_CPS = {"zh": 4.5, "en": 15}
READ_PAD = 1.5


def _chars(s, lang):
    return len(re.findall(r"[一-鿿]", s)) if lang == "zh" else len(re.findall(r"[A-Za-z0-9]", s))


def _texts(b):
    """(label, text, time param) for the text a code beat puts on screen and keeps there."""
    p, out = b.get("params", {}), []
    if b.get("scene") == "quote_card":
        out.append(("quote card", p.get("text", ""), p.get("at", 0.3)))
    if isinstance(p.get("label"), dict):
        out.append(("label", p["label"].get("text", ""), p["label"].get("at", 0.5)))
    return out


# On-screen text that comes in with under MIN_SHOWN seconds of its beat left is as good as never shown. Same floor as burned
# subtitles (tools/nightly/check.py: a subtitle under 0.5 s fails). Measured 2026-11-16 on seven films: five published ones
# gave one hit in total; 1.5 s (READ_PAD) gave 4–12 per film.
MIN_SHOWN = 0.5


def at_texts(v, path=""):
    """(path, text, at) for every object inside a code beat's params that has both a string "text" and an "at"."""
    if isinstance(v, dict):
        if isinstance(v.get("text"), str) and v["text"] and "at" in v:
            yield path or "text", v["text"], v["at"]
        for k, x in v.items():
            yield from at_texts(x, f"{path}.{k}" if path else k)
    elif isinstance(v, list):
        for i, x in enumerate(v):
            yield from at_texts(x, f"{path}[{i}]")


def late_reveal(doc, beats):
    """One line per on-screen text whose "at" leaves it under MIN_SHOWN s before the beat ends; beats = beats.json["beats"].
    An "at" phrase that is not in the narration is not reported here (the scene falls back to its own time)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from doc_code import phrase_at
    lang, out = doc.get("lang", "zh"), []
    params = {b["id"]: b.get("params", {}) for b in doc["beats"] if b.get("source") == "code"}
    scene = {b["id"]: b.get("scene") for b in doc["beats"]}
    for b in beats:
        for path, text, at in at_texts(params.get(b["id"], {})):
            shown = phrase_at(b, at, lang)
            if shown is not None and b["duration"] - shown < MIN_SHOWN:
                out.append(f"late_reveal: {b['id']} {path} 「{text[:14]}」 has only {max(b['duration'] - shown, 0):.2f}s left"
                           f" after it appears (hang its at on an earlier word)")
        if scene.get(b["id"]) == "countdown" and (m := countdown_late(b, params[b["id"]], lang)):
            out.append(m)
    return out


def countdown_late(beat, p, lang):
    """countdown (scenes/countdown.js) runs its clock for p.dur s (default 3) from p.at (default 0.3), whatever the beat's
    length: a clock still running, or stopping under MIN_SHOWN s before the beat ends, never shows its final value
    (2026-11-17, a DeepSeek trial: the clock was cut off at 0:03 and no report said so). A line, or None."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from doc_code import phrase_at
    t0 = phrase_at(beat, p["at"], lang) if "at" in p else 0.3
    if t0 is None:                         # phrase not in the beat: doc_code.py stops on that before rendering
        return None
    end = t0 + (p.get("dur") or 3)
    if beat["duration"] - end >= MIN_SHOWN:
        return None
    return (f"late_reveal: {beat['id']} countdown clock runs from {t0:.2f}s to {end:.2f}s but the beat is {beat['duration']:.2f}s:"
            f" its final value shows under {MIN_SHOWN}s (make dur at most {max(math.floor((beat['duration'] - MIN_SHOWN - t0) * 10) / 10, 0):.1f}"
            f" or start it earlier)")


def read_time(doc, beats):
    """One line per code-beat text held shorter than its reading time; beats = beats.json["beats"]."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from doc_code import phrase_at
    lang, cps, out = doc.get("lang", "zh"), READ_CPS.get(doc.get("lang", "zh"), 4.5), []
    for b in beats:
        if b.get("source") != "code":
            continue
        for kind, text, at in _texts(b):
            shown = phrase_at(b, at, lang)
            need = _chars(text, lang) / cps + READ_PAD
            have = b["duration"] - (shown if shown is not None else 0)
            if text and have < need:
                out.append(f"read_time: {b['id']} {kind} 「{text[:14]}」 stays {have:.1f}s < needs {need:.1f}s")
    return out


def _profile(doc):
    """The six things compared with the last film, read from a vox-host doc.json."""
    beats = doc["beats"]
    kind = lambda b: b.get("scene") if b["source"] == "code" else b["source"]
    body = [b for b in beats if b.get("scene") != "cover"]
    first_host = next((i for i, b in enumerate(body) if b["source"] == "clip"), len(body))
    special = [kind(b) for b in body if b["source"] == "code" and b.get("scene") not in ("quote_card", "timeline")]
    return {
        "structure (order of code scenes other than quote cards and timelines)": special,
        "opening hook shot": kind(body[0]) if body else None,
        "signature shot (number of burst_title cards)": sum(b.get("scene") == "burst_title" for b in beats),
        "mix of shot kinds": sorted(Counter(kind(b) for b in beats)),
        "shot before the close": kind(body[first_host - 1]) if first_host else None,
        "host placement mix": host_layout(doc),
    }


def vs_prev(doc, prev):
    """(items that match the previous episode, how many differ); at least 4 of 6 must differ."""
    a, b = _profile(doc), _profile(prev)
    same = [k for k in a if a[k] == b[k]]
    return same, len(a) - len(same)


HOOKS = ("反問", "反常識", "數字", "衝突")     # FORMAT §2: the four ways to open
OPEN_N = 4     # first 4 characters of each line: episodes 7-12 measured, 3 lists names, 5 misses 「你有沒有」


def _bare(s):
    return re.sub(r"[\W_]+", "", s)


def fixed_lines(base):
    """The series' fixed lines (series.json "fixed_lines", one folder above the episode), punctuation removed; None if none."""
    f = Path(base).resolve().parent / "series.json"
    v = (doc_common.read_json(f) or {}).get("fixed_lines") if f.exists() else None
    return [_bare(x) for x in v] if v else None


def _main_kind(doc):
    """(kind of the main-line beat, problem): doc "main_beat", else the second beat after the cover."""
    if doc.get("main_beat"):
        b = next((x for x in doc["beats"] if x["id"] == doc["main_beat"]), None)
        if b is None:
            return None, f"main_beat {doc['main_beat']} is not a beat"
    else:
        body = [x for x in doc["beats"] if x.get("scene") != "cover"]
        b = body[1] if len(body) > 1 else None
    if b is None:
        return None, None
    return (b.get("scene") if b["source"] == "code" else b["source"]), None


def script_vs_prev(doc, prev, fixed):
    """What the script repeats from the previous episode (FORMAT 總目標): hook type, main-line beat, line openings outside
    the series' fixed lines. A report, never a failure."""
    out = [] if fixed is not None else ["no fixed-line list (series.json fixed_lines): every line is compared"]
    h, ph = doc.get("hook"), prev.get("hook")
    if not h:
        out.append("this episode names no hook type (doc.json \"hook\")")
    elif h not in HOOKS:
        out.append(f"hook type 「{h}」 is not one of {' / '.join(HOOKS)}")
    elif not ph:
        out.append("the previous episode names no hook type: not compared")
    elif h == ph:
        out.append(f"same hook type as the previous episode: {h}")
    (k, bad), (pk, _) = _main_kind(doc), _main_kind(prev)
    if bad:
        out.append(bad)
    elif k and k == pk:
        out.append(f"same main-line shot as the previous episode: {k}")
    if doc.get("lang") == "en":
        out.append("English script: line openings are not compared")
        return out
    fx = tuple(fixed or ())

    def keep(lines):
        return [(x["text"], _bare(x["text"])) for x in lines if len(_bare(x["text"])) >= OPEN_N and not _bare(x["text"]).startswith(fx)]
    seen = {b[:OPEN_N] for _, b in keep(prev["lines"])}
    hits = [t for t, b in keep(doc["lines"]) if b[:OPEN_N] in seen]
    if hits:
        out.append(f"line openings as in the previous episode (first {OPEN_N} characters): " + ", ".join(f"「{t[:16]}」" for t in hits))
    return out


def prev_episode(doc_path):
    """The sibling folder numbered one less (NNN_xxx → NNN-1_*), its doc.json, or None."""
    d = Path(doc_path).resolve()
    d = d.parent if d.suffix == ".json" else d
    m = re.match(r"(\d+)_", d.name)
    if not m:
        return None
    hits = sorted(d.parent.glob(f"{int(m[1]) - 1:0{len(m[1])}d}_*/doc.json"))
    return hits[0] if hits else None


# How many earlier episodes the reports look back. Only four hook types (HOOKS), so three is the most an episode can
# differ from every time. Measured 2026-11-20 on a 120-episode series checked against the last episode only: two
# episodes back the same hook came up 21% of the time and the same main-line shot 37% (one back: 0% and 8%).
COMPARE_LAST = 3


def earlier_episodes(prev_path, n=COMPARE_LAST):
    """prev_path and the episodes before it (each numbered one less), at most n, nearest first; a gap ends the chain."""
    out = []
    while prev_path and len(out) < n:
        out.append(Path(prev_path))
        prev_path = prev_episode(prev_path)
    return out


def report_prev(doc, prev_path, base=None):
    """Print the vs_prev report and the script report for the last COMPARE_LAST episodes, starting at prev_path (never
    fail); base: the episode folder, for series.json."""
    eps = earlier_episodes(prev_path)
    if not eps:
        return
    fixed, rep = fixed_lines(base or Path.cwd()), []
    for i, p in enumerate(eps):
        prev = doc_common.read_json(p)
        same, differ = vs_prev(doc, prev)
        mark = "ok" if differ >= 4 else "too close: at least 4 must differ"
        print(f"vs_prev ({p.parent.name}): {differ} of 6 differ, {mark}" + (f"; same: {', '.join(same)}" if same else ""))
        for line in script_vs_prev(doc, prev, fixed):
            if i == 0 or line.startswith(("same ", "line openings")):   # notes about this episode itself: printed once
                rep.append(line.replace("the previous episode", p.parent.name))
    if (t := theme_streak(doc, eps)):
        rep.append(t)
    print(f"script vs the last {len(eps)} episode(s): " + ("\n  " + "\n  ".join(rep) if rep else "no repeats"))


THEME_STREAK = 3   # the same theme this many episodes in a row is reported (the theme ledger; doc_theme_preview offers others)


def theme_streak(doc, eps):
    """'same theme N episodes in a row: X' when this episode and the THEME_STREAK - 1 before it share a theme; else None."""
    t = doc.get("theme")
    back = [doc_common.read_json(p).get("theme") for p in eps[:THEME_STREAK - 1]]
    if t and len(back) == THEME_STREAK - 1 and all(x == t for x in back):
        return f"same theme {THEME_STREAK} episodes in a row: {t} (doc_theme_preview.py shows others; a reminder)"
    return None


AI_NOTE = " (a reminder, not a failure)"   # printed after every ai_phrasing line: a first-time reader took the ⚠ for a failure (2026-11-16)


def check(doc, rules=DEFAULT, prev=None, base=None):
    """make_doc.py's last step: stop with every problem listed; with prev (a doc.json path) also report vs_prev. base: the
    episode folder, for facts.md (make_doc runs inside it, so the default is the current folder)."""
    report_prev(doc, prev, base)
    if rules.get("facts") and (note := doc_facts.scripture_note(doc)):
        print(note)
    for w in ai_phrasing(doc) + peak_weight(doc):
        print("⚠ " + w + AI_NOTE)
    problems = lint(doc, rules, base)
    if problems:
        sys.exit("doc_lint:\n" + "\n".join(problems))


def main():
    ap = argparse.ArgumentParser(description="Script checks for a vox-host doc.json (the machine checks in formats/vox-host/FORMAT.md).")
    ap.add_argument("doc")
    ap.add_argument("--off", nargs="*", default=[], help="rules to skip")
    ap.add_argument("--beats", help="beats.json from doc_align: also report read_time and late_reveal")
    a = ap.parse_args()
    unknown = set(a.off) - set(DEFAULT)
    if unknown:
        print("unknown rule:", ", ".join(sorted(unknown)), "; rules:", ", ".join(DEFAULT))
        sys.exit(2)
    doc, _ = doc_common.load(a.doc)
    problems = lint(doc, {k: v for k, v in DEFAULT.items() if k not in a.off}, Path(a.doc).resolve().parent)
    if "facts" not in a.off and (note := doc_facts.scripture_note(doc)):
        print(note)
    print("host placement: " + ", ".join(f"{k} {v}" for k, v in host_layout(doc).items()))
    report_prev(doc, prev_episode(a.doc), Path(a.doc).resolve().parent)
    if a.beats:
        beats = doc_common.read_beats(a.beats)["beats"]
        slow = read_time(doc, beats)
        print("\n".join(slow) if slow else "read_time: ok")
        late = late_reveal(doc, beats)
        print("\n".join(late) if late else "late_reveal: ok")
    print("\n".join(f"⚠ {w}{AI_NOTE}" for w in ai_phrasing(doc)) or "ai_phrasing: ok")
    print("\n".join(f"⚠ {w}{AI_NOTE}" for w in peak_weight(doc)) or "peak_weight: ok")
    print("\n".join(problems) if problems else "doc_lint: ok")
    if not problems and (nxt := doc_approval.next_step(doc, Path(a.doc).resolve().parent)):
        print(nxt)   # a script the user has not approved yet: doc_tts.py will not voice it (doc_approval.py)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
