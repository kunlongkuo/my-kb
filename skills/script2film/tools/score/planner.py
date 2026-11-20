"""自動編曲器：events JSON → 分段計畫 JSON。"""
import random
import zlib

from styles import PC_NAME, ROLES, STYLES, degree_chord, parse_chord, role_table

MIN_SECTION = 1.5
MEL_LO, MEL_HI = 60, 76
MOTIFS = {"emmanuel": ([0, 3, 7, 7, 7, 5, 8, 7, 5, 3], [1, 1, 1, 1, 1, .5, .5, .5, .5, 2])}
AUTO_RHYTHM = [1, 1, 1, 1, 1.5, .5, 2]


class PlanError(ValueError):
    pass


def validate(ev: dict) -> dict:
    """檢查 events，補預設值後回傳新 dict；違規丟 PlanError（訊息含欄位路徑）。"""
    def need(cond, msg):
        if not cond:
            raise PlanError(msg)

    need(isinstance(ev.get("name"), str) and ev["name"], "name: required string")
    need(isinstance(ev.get("duration"), (int, float)) and ev["duration"] > 0, "duration: must be > 0")
    style = ev.get("style", "devotion")
    need(style in STYLES, f"style: {style!r} is not in {sorted(STYLES)}")
    motif = ev.get("motif", "auto")
    need(motif in ("auto", *MOTIFS), f"motif: {motif!r} is not in {['auto', *MOTIFS]}")
    if motif in MOTIFS:
        tonic = STYLES[style]["tonic"]
        offs = MOTIFS[motif][0]
        need(tonic + min(offs) >= MEL_LO and tonic + max(offs) <= MEL_HI,
             f"motif: {motif} on {style}'s tonic {tonic} goes outside the range {MEL_LO}–{MEL_HI}")
    under_voice = ev.get("under_voice", True)
    need(isinstance(under_voice, bool), "under_voice: must be true/false")
    secs = ev.get("sections")
    need(isinstance(secs, list) and secs, "sections: at least one section")
    prev = None
    for i, s in enumerate(secs):
        t = s.get("t")
        need(isinstance(t, (int, float)), f"sections[{i}].t: must be a number")
        need(s.get("role") in ROLES, f"sections[{i}].role: {s.get('role')!r} is not in the allowed list {list(ROLES)}")
        need(t < ev["duration"], f"sections[{i}].t: {t} must be < duration {ev['duration']}")
        if i == 0:
            need(t == 0, "sections[0].t: the first section must start at 0")
        else:
            need(t > prev, f"sections[{i}].t: {t} must be greater than the previous section's {prev}")
        prev = t
    hits = ev.get("hits", [])
    for i, h in enumerate(hits):
        t = h.get("t")
        need(isinstance(t, (int, float)) and 0 <= t < ev["duration"], f"hits[{i}].t: must be 0 ≤ t < duration")
    seed = ev.get("seed", zlib.crc32(ev["name"].encode()))
    need(isinstance(seed, int), "seed: must be an integer")
    return {**ev, "style": style, "motif": motif, "under_voice": under_voice, "hits": hits, "seed": seed}


def merge_short(sections: list[dict], duration: float) -> list[dict]:
    """sections（含 t, role, label）→ [{start, end, role, label}]，短於 MIN_SECTION 的併掉。"""
    segs = [{"start": s["t"], "end": (sections[i + 1]["t"] if i + 1 < len(sections) else duration),
             "role": s["role"], "label": s.get("label", s["role"])} for i, s in enumerate(sections)]
    changed = True
    while changed and len(segs) > 1:
        changed = False
        for i, s in enumerate(segs):
            if s["end"] - s["start"] < MIN_SECTION:
                if i == 0:
                    segs[1]["start"] = 0
                else:
                    segs[i - 1]["end"] = s["end"]
                del segs[i]
                changed = True
                break
    return segs


def choose_beats(d: float, lo: float, hi: float, target: float) -> int:
    inside = [b for b in range(2, 401) if lo <= 60 * b / d <= hi]
    if inside:
        return min(inside, key=lambda b: (abs(60 * b / d - target) + (3 if b % 2 else 0), b))

    def dist(b):
        bpm = 60 * b / d
        return lo - bpm if bpm < lo else bpm - hi
    return min(range(1, 401), key=lambda b: (dist(b), b))


def chord_degrees(role: str, beats: int, style: str = "devotion") -> list[list]:
    cycle = role_table(style)[role][0]
    unit = 2 if beats <= 10 else 4
    out, k, left = [], 0, beats
    while left >= unit:
        out.append([cycle[k % len(cycle)], unit])
        k, left = k + 1, left - unit
    if left == 1 and out:
        out[-1][1] += 1
    elif left:
        out.append([cycle[k % len(cycle)], left])
    return out


def chord_at(chords: list[list], beat: float) -> list[int]:
    acc = 0
    for name, nb in chords:
        if beat < acc + nb:
            return parse_chord(name)
        acc += nb
    return parse_chord(chords[-1][0])


def tones(pcs, lo=MEL_LO, hi=MEL_HI):
    return [n for n in range(lo, hi + 1) if n % 12 in pcs]


def nearest(cands, ref):
    return min(cands, key=lambda n: (abs(n - ref), n))


def phrase(motif: str, tonic: int, chords, start_beat: float, rng: random.Random):
    """回傳 [(拍位, MIDI, 拍數)]，拍位相對段首。"""
    if motif in MOTIFS:
        offs, durs = MOTIFS[motif]
        notes, b = [], start_beat
        for o, d in zip(offs, durs):
            notes.append((b, tonic + o, d))
            b += d
        return notes
    ref = rng.choice([tonic, tonic + 7 if tonic + 7 <= MEL_HI else tonic])
    notes, b = [], start_beat
    for i, d in enumerate(AUTO_RHYTHM):
        pcs = chord_at(chords, b)
        if i == len(AUTO_RHYTHM) - 1:
            ref = nearest(tones([pcs[0]]), ref)
        else:
            ref = nearest(tones(pcs), ref)
        notes.append((b, ref, d))
        b += d
    return notes


def clip(notes, beats):
    return [[b, n, min(d, beats - b)] for b, n, d in notes if b < beats]


def melody_for(role, beats, chords, motif, tonic, rng):
    if role == "intro":
        return [m + ["motif"] for m in clip(phrase(motif, tonic, chords, 0, rng), beats)]
    if role == "pause":
        return [m + ["motif"] for m in clip(phrase(motif, tonic, chords, 0, rng), min(6, beats))]
    if role == "outro":
        root = nearest(tones([parse_chord(chords[0][0])[0]]), tonic)
        out = [[0, root, min(2, beats), "motif"]]
        s = max(2, beats - 6)
        lead_in = phrase(motif, tonic, chords, 0, random.Random(0))[-4][0]  # 句子最後 4 音之前的拍數
        notes = clip([list(m) for m in phrase(motif, tonic, chords, s - lead_in, rng)[-4:]], beats)
        if notes:
            notes[-1][2] = beats - notes[-1][0]
        return out + [m + ["motif"] for m in notes]
    if role == "reflect":
        return [[b, max(tones(chord_at(chords, b), 64, 72)), min(2, beats - b), "motif"] for b in range(0, beats, 4)]
    if role == "warm":  # 段首一個音樂盒單音：這段只有起音軟的弦樂、豎琴，沒有它換段聽不出來
        return [[0, max(tones(chord_at(chords, 0), 64, 76)), min(2, beats), "motif"]]
    if role == "body":
        return [[b, max(tones(chord_at(chords, b), 64, 74)), min(3, beats - b), "lead"] for b in range(0, beats, 8)]
    return []


def make_plan(raw: dict) -> dict:
    ev = validate(raw)
    st = STYLES[ev["style"]]
    tonic = st["tonic"]
    rng = random.Random(ev["seed"])
    segs = merge_short(ev["sections"], ev["duration"])
    out = []
    for i, s in enumerate(segs):
        d = s["end"] - s["start"]
        beats = choose_beats(d, *st["bpm"], st["target"])
        degs = chord_degrees(s["role"], beats, ev["style"])
        if i + 1 < len(segs) and segs[i + 1]["role"] == "outro":
            degs[-1][0] = "V"
        if i == len(segs) - 1:
            degs[-1][0] = st["final"]
        chords = [[degree_chord(tonic % 12, g, st.get("mode", "minor")), nb] for g, nb in degs]
        _, layers, g_voice, g_free = role_table(ev["style"])[s["role"]]
        layers = list(layers) + (["shaker"] if s["role"] in st["shaker_roles"] else []) \
            + (["drums"] if s["role"] in st.get("drum_roles", ()) else [])
        out.append({"name": s["label"], "role": s["role"], "start": s["start"], "end": s["end"], "beats": beats,
                    "gain_db": g_voice if ev["under_voice"] else g_free, "chords": chords, "layers": layers,
                    "melody": melody_for(s["role"], beats, chords, ev["motif"], tonic, rng)})
    for h in ev["hits"]:
        sec = next(s for s in reversed(out) if s["start"] <= h["t"])
        spb = (sec["end"] - sec["start"]) / sec["beats"]
        b = (h["t"] - sec["start"]) / spb
        sec["melody"].append([b, max(tones(chord_at(sec["chords"], b), 64, 76)), min(1, sec["beats"] - b), "motif", "hit"])
    key = PC_NAME[tonic % 12] + (" major" if st.get("mode") == "major" else " minor")
    return {"name": ev["name"], "style": ev["style"], "key": key, "seed": ev["seed"], "source": "planner",
            "sections": out}
