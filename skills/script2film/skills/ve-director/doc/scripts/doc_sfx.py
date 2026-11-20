"""Sound effects for a doc film: one mixed track, sfx/sfx_bed.wav, plus sfx_plan.json.

  python3 doc_sfx.py <project>/doc.json [--theme=collage] [--report]
Run after doc_code (it writes code_<theme>/<id>.sfx.json for each code beat when doc.json "sfx_on" is true), before doc_cut
(which puts the track in the draft). Three sources:
  A  visual actions the scenes marked (paper, whoosh, reveal, shutter, click, marker, tick, pluck) + a tear on each "wipes" cut
  B  the series word list (doc.json "sfx_words": a json {word: kind} relative to the project): a whole word in the narration
  C  doc.json "sfx_add": [{"beat", "at", "kind"}] adds; "sfx_off": ["B12", "B12#kind:paper", "B12#word:紅海"] removes
Order (D4): C in; A merged (same beat and kind within A_MERGE s); A capped at A_CAP per beat (earliest); B within B_NEAR s
of any A / C dropped; B spaced B_GAP s apart (any kind, across beats); sfx_off last. Kinds and volumes: ../sfx_map.json
(doc.json "sfx_map" may override a kind). Only CC0, 自製, VideoExpress-generated or with-this-repository (MIT) sounds
are allowed: the licence field must contain one of LICENSED.
"""
import json, re, subprocess, sys

from doc_common import SKILL_DOC, asset, assets, load, read_beats, read_json, tokens

A_MERGE, A_CAP, B_NEAR, B_GAP = 0.25, 3, 1.0, 8.0
FADE = 0.4
# "this repository (MIT)": the author's VideoExpress sounds that ship in assets/sfx/ve-gen (assets/README.md)
LICENSED = ("CC0", "自製", "VideoExpress", "this repository (MIT)")


def sfx_map(doc):
    kinds = json.loads((SKILL_DOC / "sfx_map.json").read_text(encoding="utf-8"))["kinds"]
    for k, v in (doc.get("sfx_map") or {}).items():
        kinds[k] = {**kinds.get(k, {"volume": 0.17}), **v}
    return kinds


def library():
    """(bundled sfx folder, {id: entry}): the manifest.json of both layers (doc_common.assets), the user layer's entry
    winning on the same id. Each entry remembers its own layer's folder in "_dir"; its file is looked up there."""
    dirs, man = assets("sfx"), {}
    for d in reversed(dirs):                   # bundled first, then the user layer over it
        if (d / "manifest.json").exists():
            man.update({m["id"]: {**m, "_dir": d} for m in json.loads((d / "manifest.json").read_text(encoding="utf-8"))})
    if not man:
        asset("sfx", "manifest.json")          # stops with how to restore the bundled sounds
    return dirs[-1], man


def resolve(kinds, lib, man):
    """kind → (path, entry) of its first sound on disk; a referenced sound with any other licence stops the build.
    An entry's file is looked up in its own layer's folder ("_dir"), else in lib."""
    out = {}
    for k, v in kinds.items():
        for i in v.get("files", []):
            m = man.get(i)
            if m and not any(x in m.get("license", "") for x in LICENSED):
                sys.exit(f"✗ sfx_map {k}: {i} is not CC0 / 自製 / VideoExpress / this repository (MIT) ({m.get('license')})")
            f = m and m.get("_dir", lib) / m["file"]
            if m and f.exists() and k not in out:
                out[k] = (f, m)
    return out


def check_words(words, kinds, lang):
    """A series word list: known kinds only, and no single-character Chinese words (「水」 would sound on 「薪水」, 「風」 on
    「風聞」, 「角」 on 「主角」: all in episodes 1-12)."""
    bad = {w: k for w, k in words.items() if k not in kinds}
    if bad:
        sys.exit(f"✗ sfx_words: unknown kinds {bad}")
    short = [w for w in words if lang == "zh" and len(tokens(w, lang)) < 2]
    if short:
        sys.exit(f"✗ sfx_words: single characters match inside other words, list whole words: {', '.join(short)}")


def word_hits(beats, words, lang):
    """Every whole-word occurrence of a listed word in a beat's narration tokens → (beat id, word, kind, seconds, token index)."""
    hits = []
    for b in beats:
        toks = [t[0] for t in b.get("tokens", [])]
        for w, kind in words.items():
            q = tokens(w, lang)
            for i in range(len(toks) - len(q) + 1):
                if q and toks[i:i + len(q)] == q:
                    hits.append((b["id"], w, kind, round(b["start"] + b["tokens"][i][1], 3), i))
    return hits


def plan(doc, beats, a_marks, words, kinds, lang, phrase_at):
    """Apply D4 in order. a_marks: {beat id: [{kind, t}]} (t from the beat's start). Returns (kept, dropped) lists of
    dicts {t, src, kind, beat, word?, why?}."""
    by_id = {b["id"]: b for b in beats}
    dropped = []
    C = []
    for x in doc.get("sfx_add", []):
        b = by_id.get(x.get("beat"))
        if not b:
            sys.exit(f"✗ sfx_add: no such beat {x.get('beat')!r}")
        if x.get("kind") not in kinds:
            sys.exit(f"✗ sfx_add {b['id']}: kind must be one of {', '.join(kinds)}: {x.get('kind')!r}")
        t = phrase_at(b, x.get("at", 0), lang)
        if t is None:
            sys.exit(f"✗ sfx_add {b['id']}: at={x.get('at')!r} is not in the beat's narration")
        C.append({"t": round(b["start"] + t, 3), "src": "C", "kind": x["kind"], "beat": b["id"]})
    A = []
    for bid, marks in a_marks.items():
        last, n = {}, 0
        for m in sorted(marks, key=lambda m: m["t"]):
            if m["kind"] in last and m["t"] - last[m["kind"]] <= A_MERGE + 1e-6:
                continue
            last[m["kind"]] = m["t"]
            if n == A_CAP:
                dropped.append({"t": round(by_id[bid]["start"] + m["t"], 3), "src": "A", "kind": m["kind"], "beat": bid,
                                "why": f"over {A_CAP} per beat"})
                continue
            n += 1
            A.append({"t": round(by_id[bid]["start"] + m["t"], 3), "src": "A", "kind": m["kind"], "beat": bid})
    for w in doc.get("wipes", []):
        if w in by_id:
            A.append({"t": round(by_id[w]["start"], 3), "src": "A", "kind": "tear", "beat": w})
    B, last_b = [], None
    for bid, word, kind, t, i in sorted(word_hits(beats, words, lang), key=lambda h: h[3]):
        x = {"t": t, "src": "B", "kind": kind, "beat": bid, "word": word, "i": i}
        if any(abs(t - y["t"]) < B_NEAR for y in A + C):
            dropped.append({**x, "why": f"within {B_NEAR:g} s of a visual / manual sound"})
        elif last_b is not None and t - last_b < B_GAP:
            dropped.append({**x, "why": f"within {B_GAP:g} s of the previous word sound"})
        else:
            B.append(x)
            last_b = t
    kept = sorted(C + A + B, key=lambda x: x["t"])
    for off in doc.get("sfx_off", []):
        m = re.fullmatch(r"([^#]+)(?:#(kind|word):(.+))?", off)
        bid, what, val = m.groups() if m else (off, None, None)
        if bid not in by_id:
            sys.exit(f"✗ sfx_off {off!r}: no such beat {bid!r}")
        if what == "kind" and val not in kinds:
            sys.exit(f"✗ sfx_off {off!r}: kind must be one of {', '.join(kinds)}")
        if what == "word" and val not in words:
            sys.exit(f"✗ sfx_off {off!r}: {val!r} is not in the series word list")
        hit = [x for x in kept if x["beat"] == bid and (what is None or (what == "kind" and x["kind"] == val)
                                                      or (what == "word" and x.get("word") == val))]
        kept = [x for x in kept if x not in hit]
        dropped += [{**x, "why": f"sfx_off {off}"} for x in hit]
    return kept, sorted(dropped, key=lambda x: x["t"])


def peak(path):
    err = subprocess.run(["ffmpeg", "-nostats", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.search(r"max_volume: (-?[\d.]+) dB", err)
    return float(m.group(1)) if m else 0.0


def mix(kept, files, kinds, total, out):
    """One track the length of the film: each sound peak-normalised to -1 dBFS, scaled by its kind's volume, placed at t."""
    ins, fx, n = [], [], 0
    for x in kept:
        if x["kind"] not in files:
            continue
        path = files[x["kind"]][0]
        hold = kinds[x["kind"]].get("hold")
        cut = f"atrim=0:{hold},afade=t=out:st={hold - FADE}:d={FADE}," if hold else ""
        gain = -1 - peak(path)
        ins += ["-i", str(path)]
        ms = round(x["t"] * 1000)
        fx.append(f"[{n}]aformat=sample_rates=48000:channel_layouts=stereo,{cut}volume={gain:.2f}dB,"
                  f"volume={kinds[x['kind']]['volume']},adelay={ms}|{ms}[s{n}]")
        n += 1
    out.parent.mkdir(exist_ok=True)
    if not n:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={total:.3f}",
                        str(out)], check=True)
        return
    graph = ";".join(fx) + ";" + "".join(f"[s{k}]" for k in range(n)) + \
        f"amix=inputs={n}:normalize=0:duration=longest,apad=whole_dur={total:.3f},atrim=0:{total:.3f}[a]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", graph, "-map", "[a]", "-ar", "48000", str(out)],
                   check=True)


def main():
    doc, P = load(sys.argv[1])
    if not doc.get("sfx_on"):
        sys.exit("✗ doc.json sfx_on is not true: this film has no sound effects")
    theme = next((a.split("=", 1)[1] for a in sys.argv[2:] if a.startswith("--theme=")), doc.get("theme", "collage"))
    from doc_code import phrase_at      # the same time-parameter rules as the scenes
    B = read_beats(P / "beats.json")
    beats, total = B["beats"], B["total"]
    kinds = sfx_map(doc)
    lib, man = library()
    files = resolve(kinds, lib, man)
    words = {}
    if doc.get("sfx_words"):
        words = read_json(P / doc["sfx_words"])
        check_words(words, kinds, doc["lang"])
    a_marks = {}
    for b in beats:
        f = P / f"code_{theme}" / f"{b['id']}.sfx.json"
        if b["source"] == "code" and f.exists():
            a_marks[b["id"]] = json.loads(f.read_text(encoding="utf-8"))
    kept, dropped = plan(doc, beats, a_marks, words, kinds, doc["lang"], phrase_at)
    missing = sorted({x["kind"] for x in kept if x["kind"] not in files})
    toks = {b["id"]: [t[0] for t in b.get("tokens", [])] for b in beats}
    sep = "" if doc["lang"] == "zh" else " "
    for x in kept + dropped:
        if x.get("word"):     # the words around this occurrence (a beat can say the word twice)
            n = len(tokens(x["word"], doc["lang"]))
            x["context"] = sep.join(toks[x["beat"]][max(0, x["i"] - 5):x["i"] + n + 5])
        x["file"] = files[x["kind"]][1]["id"] if x["kind"] in files else None
    (P / "sfx_plan.json").write_text(json.dumps({"kept": kept, "dropped": dropped, "missing_kinds": missing},
                                                ensure_ascii=False, indent=1), encoding="utf-8")
    mix(kept, files, kinds, total, P / "sfx" / "sfx_bed.wav")
    print(f"sfx: {len(kept)} sounds (A {sum(x['src'] == 'A' for x in kept)}, B {sum(x['src'] == 'B' for x in kept)}, "
          f"C {sum(x['src'] == 'C' for x in kept)}), {len(dropped)} dropped" + (f", no sound yet for {', '.join(missing)}" if missing else ""))
    if "--report" in sys.argv:
        for x in kept:
            print(f"  {x['t']:7.2f}  {x['src']}  {x['beat']:<5} {x['kind']:<8} {x['file'] or '(no sound file, skipped)'}"
                  + (f"  「{x['context']}」" if x.get("context") else ""))
        for x in dropped:
            print(f"  {x['t']:7.2f}  ✗{x['src']} {x['beat']:<5} {x['kind']:<8} {x['why']}"
                  + (f"  「{x['context']}」" if x.get("context") else ""))


if __name__ == "__main__":
    main()
