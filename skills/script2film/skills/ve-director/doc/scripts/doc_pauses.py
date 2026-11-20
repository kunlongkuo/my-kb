"""Pauses at punctuation inside a narration line, and a gentle slow-down for fast lines (used by doc_voice.py).

Why (2026-11-06, found in several episodes): Qwen takes often run a comma or even a full stop into the next word
(0.0–0.1 s), so a line sounds rushed even though the gaps between lines are 0.5 s or more.

What it does, per picked take:
  1. Word timings come from local Whisper (whisper.cpp). They can be 0.1–0.2 s off, so they only say roughly where a mark is.
  2. Near each mark (±0.3 s) look for a real pause the voice already made: a run quieter than -38 dB lasting ≥ 0.12 s,
     not touching the start or end of the take. Take the deepest one and lengthen it from its middle
     (comma-type marks to 0.4 s, sentence-final marks and closing quotes to 0.65 s).
  3. No such pause → leave the mark alone. Inserting silence where the voice did not stop cut syllables in half
     (「第⋯三」「你⋯想」, sample D on 2026-11-06), which sounded worse than no pause.
  4. Lines faster than 5.6 characters a second are slowed with atempo, at most 5% (chosen over 10%).
"""
import re

import numpy as np

STRONG, WEAK = "。？！」』", "，、；：「"
# MIN_RUN 0.12 (was 0.06): the closure of b/d/g and the onset of h/s are quiet for 0.06–0.10 s, so a mark whose real
# pause the voice skipped got its silence inside the next word (one episode: 「不吃不⋯喝」, 16 of 120
# pauses rested on runs under 0.12 s; the user heard the 0.12 s version and chose it).
THR_DB, MIN_RUN, WINDOW, HOP = -38.0, 0.12, 0.3, 0.01
DEFAULTS = {"weak": 0.4, "strong": 0.65, "max_rate": 5.6, "max_slow": 0.05, "target_rate": 5.1}


def pace_gap(text, speech_sec, target_rate=5.1):
    """How far a take's speed (characters a second) is from target_rate; ranks takes with the same score. Picking simply
    the slowest take pulled some 070 lines down to 4.1 a second, which drags (2026-11-06)."""
    n = sum(is_char(c) for c in text)
    return abs(n / max(speech_sec, 1e-6) - target_rate)


def is_char(c):
    return bool(re.match(r"[一-鿿0-9A-Za-z]", c))


def char_times(words):
    """[(word, start, end)] → per-character start and end lists (a word's time is split evenly over its characters)."""
    st, en = [], []
    for w, a, b in words:
        n = sum(is_char(c) for c in w)
        d = (b - a) / max(n, 1)
        for k in range(n):
            st.append(a + d * k)
            en.append(a + d * (k + 1))
    return st, en


def marks(text, st, en, weak=0.4, strong=0.65):
    """Estimated (time, target pause) for every mark that has spoken characters on both sides. Marks closer than
    0.05 s (e.g. ：「) merge into one with the larger target."""
    out, cnt = [], 0
    for i, c in enumerate(text):
        if is_char(c):
            cnt += 1
            continue
        if c in STRONG + WEAK and 0 < cnt < len(st) and any(is_char(d) for d in text[i + 1:]):
            t, tgt = (en[cnt - 1] + st[cnt]) / 2, strong if c in STRONG else weak
            if out and abs(out[-1][0] - t) < 0.05:
                out[-1] = (out[-1][0], max(out[-1][1], tgt))
            else:
                out.append((t, tgt))
    return out


def quiet_runs(x, sr, thr_db=THR_DB, min_run=MIN_RUN):
    """(start, end, deepest dB) of every run quieter than thr_db lasting ≥ min_run, excluding runs that touch the
    start or end of x (leading and trailing silence are not pauses)."""
    hop = int(HOP * sr)
    if len(x) < 2 * hop:
        return []
    e = 20 * np.log10(np.sqrt(np.array([np.mean(x[i:i + hop] ** 2) for i in range(0, len(x) - hop + 1, hop)])) + 1e-9)
    q, runs, i = e < thr_db, [], 0
    while i < len(q):
        if not q[i]:
            i += 1
            continue
        j = i
        while j < len(q) and q[j]:
            j += 1
        if i > 0 and j < len(q) and (j - i) * HOP >= min_run - 1e-9:
            runs.append((i * HOP, j * HOP, float(e[i:j].min())))
        i = j
    return runs


def pick_run(runs, t, window=WINDOW):
    """The deepest run whose middle is within `window` of t (ties: the longer), or None."""
    near = [r for r in runs if abs((r[0] + r[1]) / 2 - t) <= window]
    return min(near, key=lambda r: (r[2], -(r[1] - r[0]))) if near else None


def plan(x, sr, text, words, weak=0.4, strong=0.65):
    """[(insert at sec, silence to add)] plus how many marks found a real pause (used to rank takes)."""
    st, en = char_times(words)
    runs, cuts, hits = quiet_runs(x, sr), [], 0
    for t, tgt in marks(text, st, en, weak, strong):
        r = pick_run(runs, t)
        if r is None:
            continue
        hits += 1
        mid, have = (r[0] + r[1]) / 2, r[1] - r[0]
        if cuts and abs(cuts[-1][0] - mid) < 1e-6:   # two marks found the same pause
            cuts[-1] = (mid, max(cuts[-1][1], tgt - have))
        else:
            cuts.append((mid, max(0.0, tgt - have)))
    return cuts, hits


def apply(x, sr, cuts):
    out, pos = [], 0
    for at, add in sorted(cuts):
        k = int(round(at * sr))
        if k <= pos or add <= 0:
            continue
        out += [x[pos:k], np.zeros(int(round(add * sr)), x.dtype)]
        pos = k
    out.append(x[pos:])
    return np.concatenate(out)


def tempo(text, speech_sec, max_rate=5.6, max_slow=0.05):
    """atempo factor (< 1 slows down) for a line faster than max_rate characters a second, never below 1 - max_slow;
    None when the line is not too fast."""
    n = sum(is_char(c) for c in text)
    if speech_sec <= 0 or n / speech_sec <= max_rate:
        return None
    return round(max(1 - max_slow, max_rate / (n / speech_sec)), 4)
