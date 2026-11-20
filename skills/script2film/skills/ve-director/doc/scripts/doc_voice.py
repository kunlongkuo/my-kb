"""Pick one TTS candidate per line (each is transcribed, best overlap with the script wins), trim, join with gaps.
doc.json "asr": "local" (default) transcribes with whisper.cpp on this machine (S2F_WHISPER_CPP_MODEL) and never calls Groq;
"cloud" uses Groq Whisper. In cloud mode, when Groq answers "rate limit" and S2F_WHISPER_CPP_MODEL is set, the remaining candidates are transcribed locally (whisper.cpp)
instead of waiting for the limit to reset (2026-10-21: the free tier hit its limit on a 41-line film and every retry waited 15 s or more).

  python3 doc_voice.py <project>/doc.json
Reads tts_lines/<key>_<seed>.wav (doc_tts.py; key = doc_common.line_key), falling back to the older <NN>_<seed>.wav.
Writes tts/voice.wav and tts/lines.json; transcripts are cached in tts/asr_cache.json. Low scores are often homophones the ASR picked (zh: 程式/城市), not misreadings: check `heard`.
doc.json voice.post: an ffmpeg audio filter applied to every picked line before the join (timings follow it).
doc.json voice.tail_fade: seconds of fade-out on the end of every picked line (default 0, off). Qwen takes often stop while
the last syllable is still sounding, so it ends on a hard cut that sounds unfinished before a short gap (2026-10-27: 0.08).
doc.json voice.pitch (off by default; true or {"tol": 0.05}): among the takes whose score is within tol of the line's best, take
the one nearest the film's median pitch instead of the highest score (cloned English read 104-225 Hz line to line, 2026-11-13;
tol 0.05 is a first value, not yet tuned). Pitches are cached in tts/pitch.json; lines.json gets "f0".
doc.json gaps: {"default": 0.32, "after": {"<line n>": seconds}} (pause after line n; lengthen before/after the climax line).
doc.json voice.punct_pause (on by default; false turns it off):
  {"weak": 0.4, "strong": 0.65, "max_rate": 5.6, "max_slow": 0.05, "target_rate": 5.1}.
Inside a line, real pauses at punctuation are lengthened and lines over max_rate characters a second are slowed by at most
max_slow (doc_pauses.py has the why). Among takes with the same score, the one that pauses at more marks wins, then the
one whose speed is nearest target_rate (5.1 characters a second); until 2026-11-06 a tie went to the shortest take, so the
fastest reading was picked line after line.
Word timings for this come from local Whisper (S2F_WHISPER_CPP_MODEL), cached in tts/asr_words.json; without it only the
slow-down and the slower-take rule apply.
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[4] / "tools/config"))
import s2f_config; s2f_config.load()
import json, subprocess, sys, time
from collections import Counter

import numpy as np
import soundfile as sf

import doc_pauses
import doc_common
from doc_common import asr_mode, line_key, load, local_asr, need_local_asr, speaker_of, tokens, voice_of

SR, PAD = 48000, 0.08


def groq(path, key, lang, give_up_on_limit=False):
    """Text, or None when rate-limited and give_up_on_limit (the caller switches to local transcription)."""
    for attempt in range(8):
        r = subprocess.run(["curl", "-s", "https://api.groq.com/openai/v1/audio/transcriptions", "-H", f"Authorization: Bearer {key}",
                            "-F", f"file=@{path}", "-F", "model=whisper-large-v3", "-F", f"language={lang}", "-F", "response_format=json"],
                           capture_output=True, text=True, timeout=120)
        try:
            js = json.loads(r.stdout)
        except ValueError:
            js = {}
        if js.get("text"):
            text = js["text"]
            if lang == "zh":
                from opencc import OpenCC
                text = OpenCC("s2twp").convert(text)
            return text
        if give_up_on_limit and "rate limit" in str(js.get("error", r.stdout)).lower():
            return None
        wait = 15 * (attempt + 1)
        print(f"  Groq gave no text ({str(js.get('error', r.stdout))[:70]}); retry in {wait}s", flush=True)
        time.sleep(wait)
    sys.exit(f"✗ transcription keeps failing: {path}")


def overlap(a, b):
    return round(sum((Counter(a) & Counter(b)).values()) / max(1, len(a), len(b)), 3)


def trim(x):
    idx = np.where(np.abs(x) > 10 ** (-40 / 20) * max(1e-9, np.abs(x).max()))[0]
    return x if not len(idx) else x[max(0, idx[0] - int(PAD * SR)):min(len(x), idx[-1] + int(PAD * SR))]


def mono(path):
    x, sr = sf.read(path, dtype="float32")
    assert sr == SR, (path, sr)
    return x.mean(axis=1) if x.ndim > 1 else x


def pitch(x, sr=SR):
    """Median speaking pitch of a take in Hz (autocorrelation on 16 kHz frames, 60-300 Hz), or None when nothing is voiced."""
    step = sr // 16000
    y = x[::step].astype(np.float64); r = sr // step
    n, hop, lo, hi = int(.064 * r), int(.016 * r), r // 300, r // 60
    if len(y) < n:
        return None
    floor = 10 ** (-30 / 20) * max(1e-9, np.abs(y).max())
    out = []
    for i in range(0, len(y) - n, hop):
        f = y[i:i + n] - y[i:i + n].mean()
        if np.sqrt((f ** 2).mean()) < floor:
            continue
        ac = np.correlate(f, f, "full")[n - 1:]
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] > .5 * ac[0]:
            out.append(r / k)
    return float(np.median(out)) if out else None


def by_pitch(rows, tol):
    """rows: per line, the takes as (score, take, cuts, hits, speech, raw, gap, f0). The film's pitch is the median over the
    takes that read the line as well as its best take (within tol); each line then takes the one of those nearest it."""
    ok = [[c for c in cs if c[0] >= max(x[0] for x in cs) - tol and c[7]] for cs in rows]
    f0 = [c[7] for cs in ok for c in cs]
    if not f0:
        return None, ok
    return float(np.median(f0)), ok


def pitch_targets(rows, speakers, tol):
    """by_pitch for each speaker on its own lines: {speaker: median f0 or None} and the per-line takes in range. One
    film-wide median would pull a dialogue's second voice toward the narrator's."""
    targets, ok = {}, [None] * len(rows)
    for s in dict.fromkeys(speakers):
        idx = [i for i, x in enumerate(speakers) if x == s]
        targets[s], sub = by_pitch([rows[i] for i in idx], tol)
        for i, o in zip(idx, sub):
            ok[i] = o
    return targets, ok


def word_timings(P, cands_by_line, lang):
    """{take name: [[word, start, end], ...]} from local Whisper, cached in tts/asr_words.json; None without S2F_WHISPER_CPP_MODEL."""
    if not doc_common.has_local_asr():
        print("  S2F_WHISPER_CPP_MODEL not set: no pauses at punctuation (slow-down and slower-take rule still apply)", flush=True)
        return None
    cp = P / "tts/asr_words.json"
    cache = json.loads(cp.read_text()) if cp.exists() else {}
    todo = [c for cands in cands_by_line for c in cands if c.name not in cache]
    if todo:
        print(f"  word timings for {len(todo)} takes (whisper.cpp)", flush=True)
        for p, v in local_asr(todo, lang, words=True).items():
            cache[p.name] = [[w["word"], w["start"], w["end"]] for seg in v["segments"] for w in seg.get("words", [])]
        cp.write_text(json.dumps(cache, ensure_ascii=False))
    return cache


def tail_fade(x, sec):
    """Fade the last `sec` seconds to silence (equal-power curve); the length is unchanged."""
    k = min(len(x), int(round(sec * SR)))
    if k <= 0:
        return x
    x = x.copy()
    x[-k:] *= np.cos(np.linspace(0, np.pi / 2, k)) ** 2
    return x


def post(x, af):
    r = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "pipe:", "-af", af,
                        "-ar", str(SR), "-ac", "1", "-f", "f32le", "pipe:"], input=x.astype(np.float32).tobytes(),
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32)


def candidates(folder, key, n):
    """Takes for a line: by content key; projects voiced before 2026-10-28 only have <NN>_<seed> names."""
    return sorted(folder.glob(f"{key}_*.wav")) or sorted(folder.glob(f"{n:02d}_*.wav"))


def transcribe_takes(doc, P, cands_by_line):
    """Transcripts of every take, cached in tts/asr_cache.json. Returns (cache, Groq key or None).
    "asr" local: whisper.cpp only, never Groq; an empty transcript is cached too (a take counts as done when its name is in
    the cache). "asr" cloud: Groq, the rest locally when rate-limited; an empty transcript is tried again."""
    lang, mode = doc["lang"], asr_mode(doc)
    (P / "tts").mkdir(exist_ok=True)
    cache_p = P / "tts/asr_cache.json"
    cache = json.loads(cache_p.read_text()) if cache_p.exists() else {}
    if mode == "local":
        todo = [c for cands in cands_by_line for c in cands if c.name not in cache]   # takes of edited-away text are skipped
        if todo:
            need_local_asr()
            print(f"  transcribing {len(todo)} candidates locally (whisper.cpp)", flush=True)
            for p, t in local_asr(todo, lang).items():
                cache[p.name] = t
            cache_p.write_text(json.dumps(cache, ensure_ascii=False, indent=1))
        return cache, None
    key = doc_common.groq_key()
    todo = [c for cands in cands_by_line for c in cands if not cache.get(c.name)]   # takes of edited-away text are skipped
    local_ok = doc_common.has_local_asr()
    for i, c in enumerate(todo):
        text = groq(c, key, lang, give_up_on_limit=local_ok)
        if text is None:
            print(f"  Groq rate-limited: transcribing the other {len(todo) - i} candidates locally (whisper.cpp)", flush=True)
            for p, t in local_asr(todo[i:], lang).items():
                cache[p.name] = t
            cache_p.write_text(json.dumps(cache, ensure_ascii=False, indent=1))
            break
        cache[c.name] = text
        cache_p.write_text(json.dumps(cache, ensure_ascii=False, indent=1))
    return cache, key


def main():
    doc, P = load(sys.argv[1])
    lang = doc["lang"]
    cache_p = P / "tts/asr_cache.json"
    gaps = doc.get("gaps", {})
    pp = doc["voice"].get("punct_pause", {})
    pp = None if pp is False else {**doc_pauses.DEFAULTS, **(pp or {})}
    cands_by_line = [candidates(P / "tts_lines", line_key(doc, P, line), n) for n, line in enumerate(doc["lines"], 1)]
    cache, key = transcribe_takes(doc, P, cands_by_line)
    words = word_timings(P, cands_by_line, lang) if pp else None
    pieces, meta, t = [], [], 0.0
    pm = doc["voice"].get("pitch")   # {"tol": 0.05}: keep the film at one pitch (2026-11-13: an English film ran 104-225 Hz line to line)
    pm = {"tol": 0.05, **(pm if isinstance(pm, dict) else {})} if pm else None
    f0_p = P / "tts/pitch.json"
    f0s = json.loads(f0_p.read_text()) if pm and f0_p.exists() else {}
    rows = []
    for n, line in enumerate(doc["lines"], 1):
        cands = cands_by_line[n - 1]
        if not cands:
            sys.exit(f"✗ line {n} has no candidates in tts_lines/")
        ref, row = tokens(line["text"], lang), []
        for c in cands:
            k = c.name
            if key and not cache.get(k):   # cloud only: local keeps an empty transcript as it is
                cache[k] = groq(c, key, lang)
                cache_p.write_text(json.dumps(cache, ensure_ascii=False, indent=1))
            sc, raw = overlap(ref, tokens(cache[k], lang)), mono(c)
            cuts, hits = doc_pauses.plan(raw, SR, line["text"], words.get(k, []), pp["weak"], pp["strong"]) if words else ([], 0)
            speech = len(trim(raw)) / SR - 2 * PAD
            gap = doc_pauses.pace_gap(line["text"], speech, (pp or doc_pauses.DEFAULTS)["target_rate"])
            if pm and k not in f0s:
                f0s[k] = pitch(raw)
            row.append((sc, c, cuts, hits, speech, raw, gap, f0s.get(k)))
        rows.append(row)
    spk = [speaker_of(doc, line) for line in doc["lines"]]
    targets, ok = pitch_targets(rows, spk, pm["tol"]) if pm else ({}, [None] * len(rows))
    if pm:
        f0_p.write_text(json.dumps(f0s, indent=1))
        for s, target in targets.items():
            who = "" if len(targets) == 1 else f" ({s})"
            print(f"  pitch{who}: median {target:.0f} Hz over takes within {pm['tol']} of each line's best score" if target else f"  pitch{who}: no voiced takes", flush=True)
    for n, line in enumerate(doc["lines"], 1):
        row, target, v = rows[n - 1], targets.get(spk[n - 1]), voice_of(doc, line)
        if target and ok[n - 1]:
            best = min(ok[n - 1], key=lambda c: (abs(c[7] - target), -c[3], c[6]))   # nearest the film's pitch, then pauses, then pace
        else:
            best = max(row, key=lambda c: (c[0], c[3], -c[6]))   # same score: more pauses, then nearer 5.1/s
        x = trim(doc_pauses.apply(best[5], SR, best[2]))
        f = doc_pauses.tempo(line["text"], best[4], pp["max_rate"], pp["max_slow"]) if pp else None
        if f:
            x = post(x, f"atempo={f}")
        if v.get("post"):   # an ffmpeg filter on each picked line (e.g. asetrate=45120,aresample=48000: lower and slower)
            x = post(x, v["post"])
        x = tail_fade(x, max(0.0, min(float(v.get("tail_fade", 0)), 0.5)))
        if n > 1:
            g = max(0.0, min(float(gaps.get("after", {}).get(str(n - 1), gaps.get("default", 0.32))), 5.0))
            pieces.append(np.zeros(int(g * SR), np.float32)); t += g
        start = t; pieces.append(x); t += len(x) / SR
        meta.append({"n": n, "speaker": spk[n - 1], "text": line["text"], "start": round(start + PAD, 3),
                     "end": round(t - PAD, 3), "pick": best[1].name, "score": best[0], "heard": cache[best[1].name],
                     "pauses": [[round(a, 2), round(b, 2)] for a, b in best[2]], "atempo": f,
                     **({"f0": round(best[7])} if best[7] else {})})
        extra = f" +{sum(b for _, b in best[2]):.2f}s/{len(best[2])}" + (f" atempo {f}" if f else "")
        print(f"{n:2d} {best[0]:.2f} {best[1].name:10s}{extra} {line['text'][:40]}")
    sf.write(P / "tts/voice.wav", np.concatenate(pieces), SR, subtype="PCM_16")
    (P / "tts/lines.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    low = [m["n"] for m in meta if m["score"] < 0.85]
    print(f"narration {t:.1f}s, {len(meta)} lines; lowest {min(m['score'] for m in meta):.2f}; below 0.85: {low or 'none'}")


if __name__ == "__main__":
    main()
