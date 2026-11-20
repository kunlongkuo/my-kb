"""Narration → subtitles and the beat table (the narration is the timing authority; VOX audio-first).

  python3 doc_align.py <project>/doc.json [--retime]      (the old flag --rescribe also works)
1. tts/voice.wav + 0.45 s lead silence, loudnorm → voice.cleaned/audio.m4a
2. word timing → voice.cleaned/aligned/audio.words.json (cached; --retime after the audio changes; a project made before
   2026-11-13 has audio.scribe.json instead, read as the cache while it is still fresh, never renamed). doc.json "asr":
   "local" (default) is whisper.cpp on this machine (S2F_WHISPER_CPP_MODEL), marked "source": "whisper.cpp"; "cloud" sends the
   audio to ElevenLabs Scribe (ELEVENLABS_API_KEY; model scribe_v2, or S2F_SCRIBE_MODEL), marked "source": "elevenlabs
   <model>", and without a key or when Scribe fails, local whisper.cpp word timing instead (stops when neither works)
3. script tokens × transcript tokens (difflib) → voice.cleaned/final.srt: the script's own text, one screen per chunk
   (zh ≤ 18 characters; en ≤ two lines of 42 characters; cut at punctuation)
4. beats.json: a beat starts up to 0.25 s before its first word (not before the previous line ends), or right after the
   previous line when the beat has "start": "after_prev" (the climax: the dim and the breath live in that shot); it ends
   where the next beat starts; "from": "<phrase>" opens a beat on that phrase inside its first line (several beats
   per line: one cut every 1-2 s). gen_seconds = ceil(duration + 0.1), 3-10 s; a VE beat over 10 s stops the script.
   Each beat carries tokens [[token, seconds from beat start]] for the code shots' keyword triggers.
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[4] / "tools/config"))
import s2f_config; s2f_config.load()
import difflib, json, math, os, re, subprocess, sys
from pathlib import Path

from doc_common import (LOCAL_SETUP, asr_mode, duration, eleven_key, has_local_asr, load, local_asr, need_local_asr, sh,
                        tokens)

LEAD, PRE = 0.45, 0.25
END_HOLD = 1.0   # seconds of picture after the last word
MAX = {"zh": 18, "en": 84}   # en: up to two lines of 42


def chunks(text, lang):
    size = (lambda s: len(tokens(s, "zh"))) if lang == "zh" else len
    parts = [s for s in re.split(r"(?<=[。？！；：，])" if lang == "zh" else r"(?<=[.?!;:,])\s+", text) if s]
    for i in range(len(parts) - 1, 0, -1):     # 「…？」: the closing quote goes with its sentence, not to the next screen
        q = re.match(r"[」』）”]+[，。、]?", parts[i])
        if q:
            parts[i - 1] += q[0]
            parts[i] = parts[i][q.end():]
            if not parts[i]:
                parts.pop(i)
    out, buf = [], ""
    for s in parts:
        joined = (buf + s) if lang == "zh" else (buf + " " + s).strip()
        if buf and size(joined) > MAX[lang]:
            out.append(buf); buf = s
        else:
            buf = joined
        if re.search(r"[。？！；：.?!;:][」』）”]?$", buf):
            out.append(buf); buf = ""
    if buf:
        out.append(buf)
    if lang == "en":
        out = [two_lines(c) for c in out]
    return out


def screen_text(s):
    """A subtitle screen without the comma it was cut at, and without a closing Chinese full stop; ？！ and the English full stop stay."""
    return s.rstrip("，,。")


def two_lines(c, width=42):
    """An English screen longer than one line breaks at the word boundary nearest the middle."""
    if len(c) <= width:
        return c
    spaces = [i for i, ch in enumerate(c) if ch == " "]
    i = min(spaces, key=lambda i: abs(i - len(c) / 2))
    return c[:i] + "\n" + c[i + 1:]


def local_words(audio, lang, sj):
    """whisper.cpp word timing written to sj, marked "source": "whisper.cpp"."""
    res = local_asr([audio], lang, words=True)
    sj.write_text(json.dumps({**next(iter(res.values())), "source": "whisper.cpp"}, ensure_ascii=False), encoding="utf-8")


SCRIBE_URL = "https://api.elevenlabs.io/v1/speech-to-text"


class ScribeError(Exception):
    """Scribe gave no usable word timing (curl failed, the answer is not JSON, or it has no words)."""


def scribe_to_segments(resp, lang):
    """A Scribe answer → [{"words": [{"word", "start", "end"}]}]: only items of type "word" with both times; the text is
    in "text". zh comes back Traditional (OpenCC s2twp, as on the local path)."""
    conv = (lambda t: t)
    if lang == "zh":
        from opencc import OpenCC
        conv = OpenCC("s2twp").convert
    words = [{"word": conv(w["text"]), "start": w["start"], "end": w["end"]} for w in resp.get("words") or []
             if w.get("type") == "word" and w.get("start") is not None and w.get("end") is not None]
    return [{"words": words}]


def scribe_words(audio, lang, sj):
    """ElevenLabs Scribe word timing of audio written to sj, marked "source": "elevenlabs <model>". The key (eleven_key())
    goes to curl on stdin (--config -), never on the command line. Raises ScribeError (and writes nothing) when it fails."""
    key = eleven_key()
    if not key:
        raise ScribeError("no ElevenLabs key (ELEVENLABS_API_KEY)")
    model = os.environ.get("S2F_SCRIBE_MODEL") or "scribe_v2"
    cmd = ["curl", "-sS", "--fail-with-body", "--max-time", "300", "--config", "-", "-X", "POST", SCRIBE_URL,
           "-F", f"model_id={model}", "-F", f"language_code={lang}", "-F", "timestamps_granularity=word",
           "-F", f'file=@"{audio}"']
    r = subprocess.run(cmd, input=f'header = "xi-api-key: {key}"\n', capture_output=True, text=True)
    body = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0:
        raise ScribeError(f"curl exit {r.returncode}: {body[:200]}")
    try:
        resp = json.loads(r.stdout)
    except ValueError:
        raise ScribeError(f"not JSON: {body[:200]}") from None
    if not isinstance(resp, dict) or not isinstance(resp.get("words"), list):
        raise ScribeError(f"no words: {body[:200]}")
    segs = scribe_to_segments(resp, lang)
    if not segs[0]["words"]:
        raise ScribeError(f"no timed words: {body[:200]}")
    sj.write_text(json.dumps({"segments": segs, "source": f"elevenlabs {model}"}, ensure_ascii=False), encoding="utf-8")


def retime_flag(argv):
    """--retime (or the old name --rescribe): transcribe again even when the cached word timing is still fresh."""
    return "--retime" in argv or "--rescribe" in argv


def word_times(doc, P, retime=False):
    """Word timing of voice.cleaned/audio.m4a → voice.cleaned/aligned/audio.words.json. Cache: audio.words.json, else the
    old name audio.scribe.json (read as it is, not copied or renamed), each only while it is not older than tts/voice.wav
    (audio.m4a is rewritten by every run, so it is not the reference); retime, or no fresh cache, transcribes again into
    audio.words.json. "asr" local: whisper.cpp; cloud: ElevenLabs Scribe, whisper.cpp without a key or when
    Scribe fails (only if S2F_WHISPER_CPP_MODEL is set; otherwise it stops with both ways out)."""
    lang, C = doc["lang"], P / "voice.cleaned"
    sj = C / "aligned/audio.words.json"
    # the transcript is of the old voice once tts/voice.wav changes (2026-10-29: two lines re-voiced, beats kept the old times)
    if not retime:
        voiced = (P / "tts/voice.wav").stat().st_mtime
        for f in (sj, C / "aligned/audio.scribe.json"):   # the old file name: projects timed before 2026-11-13
            if f.exists() and f.stat().st_mtime >= voiced:
                return f
    if asr_mode(doc) == "local":
        need_local_asr()
        local_words(C / "audio.m4a", lang, sj)
        return sj
    if eleven_key():
        try:
            scribe_words(C / "audio.m4a", lang, sj)
            return sj
        except ScribeError as e:
            why = f"Scribe failed ({e})"
    else:
        why = "no ElevenLabs key (ELEVENLABS_API_KEY)"
    if not has_local_asr():
        sys.exit(f"✗ {why}: set ELEVENLABS_API_KEY (or ELEVEN_API_KEY), or for local word timing {LOCAL_SETUP}")
    print(f"  {why}: word timing from local whisper.cpp instead", flush=True)
    local_words(C / "audio.m4a", lang, sj)
    return sj


def tail_report(sj, audio):
    """Words the transcript places after the silence that runs to the end of the audio (a Whisper-family model
    adds stock phrases there) → one line to print, or None. Listed only: nothing is removed or re-timed. The guard's
    other rule (a whole word inside a silence) is not used on word timing: line-final words are often stretched
    into the pause (two films measured, 55 hits, none real)."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "tools/qa"))
    import hallucination_guard as hg
    words = [{"start": w["start"], "end": w["end"], "text": w["word"].strip()}
             for seg in json.loads(Path(sj).read_text())["segments"] for w in seg["words"]]
    silences, dur = hg.detect(Path(audio))
    if not silences:
        return "· hallucination guard: no silence found, so it did nothing this time"
    tail = hg.tail_words(words, silences, dur)
    if not tail:
        return None
    return (f"· {len(tail)} words of the word timing fall after the closing silence: {' '.join(w['text'] for w in tail)}"
            " (listed, not removed; re-voice that line or re-time with --retime)")


def film_end(spoken, doc):
    """The film runs on after the last word ("end_hold" seconds, default END_HOLD, at least 0.6): a face or a chart is
    not cut off the moment the voice stops (2026-11-18)."""
    return round(spoken + max(0.6, float(doc.get("end_hold", END_HOLD))), 2)


def first_screen_at(at, end, voiced):
    """An unmatched screen that opens its line: no earlier than the line's voiced start in tts/lines.json (plus LEAD),
    and at least 0.3 s before its end."""
    return min(max(at, voiced + float(LEAD)), end - 0.3)


def main():
    doc, P = load(sys.argv[1])
    lang, C = doc["lang"], P / "voice.cleaned"
    (C / "aligned").mkdir(parents=True, exist_ok=True)
    sh("ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-t", LEAD, "-i", "anullsrc=r=48000:cl=mono", "-i", P / "tts/voice.wav",
       "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[o]",
       "-map", "[o]", "-c:a", "aac", "-b:a", "192k", C / "audio.m4a")
    sj = word_times(doc, P, retime=retime_flag(sys.argv))
    note = tail_report(sj, C / "audio.m4a")
    if note:
        print(note, flush=True)
    asr = []                                   # transcript tokens with times (a multi-token word shares its span evenly)
    for seg in json.loads(sj.read_text())["segments"]:
        for w in seg["words"]:
            ts = tokens(w["word"], lang)
            for i, tk in enumerate(ts):
                a = w["start"] + (w["end"] - w["start"]) * i / len(ts)
                asr.append((tk, a, w["start"] + (w["end"] - w["start"]) * (i + 1) / len(ts)))
    lines = doc["lines"]
    subs = [(n, s) for n, l in enumerate(lines, 1) for s in chunks(l["text"], lang)]
    ref, owner = [], []
    for k, (_, s) in enumerate(subs):
        for tk in tokens(s.replace("\n", " "), lang):
            ref.append(tk); owner.append(k)
    time_of = [None] * len(ref)
    for blk in difflib.SequenceMatcher(None, ref, [x[0] for x in asr], autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            time_of[blk.a + k] = asr[blk.b + k]
    out, worst, line_tok = [], 1.0, {}
    for k, (n, s) in enumerate(subs):
        idx = [i for i, o in enumerate(owner) if o == k]
        hit = [time_of[i] for i in idx if time_of[i]]
        worst = min(worst, len(hit) / len(idx))
        out.append({"line": n, "text": screen_text(s), "at": hit[0][1], "end": hit[-1][2]} if hit else
                   {"line": n, "text": screen_text(s), "at": None, "end": None, "src": s})
    # a screen the transcript never matches (2026-10-31: "Ben-Gvir。" alone, voiced as 班格維爾 via TTS_FIX) sits in the
    # gap between its matched neighbours; two unmatched in a row, or one at either end, still stops
    for k, o in enumerate(out):
        if o["at"] is None:
            if k == 0 or k == len(out) - 1 or out[k - 1]["at"] is None or out[k + 1]["at"] is None:
                sys.exit(f"✗ subtitle not found in the transcript: {o['src']}")
            o["at"], o["end"] = out[k - 1]["end"], out[k + 1]["at"]
            if out[k - 1]["line"] != o["line"] and (P / "tts/lines.json").exists():
                # the first screen of its line: it starts where the voice table says the line is voiced, not right after the
                # previous line (2026-11-18: an unheard "蛤？" took over the pause before it, so the card before ran short)
                voiced = next((x["start"] for x in json.loads((P / "tts/lines.json").read_text(encoding="utf-8")) if x["n"] == o["line"]), None)
                if voiced is not None:
                    o["at"] = first_screen_at(o["at"], o["end"], voiced)
            del o["src"]
            print(f"  unmatched screen placed between its neighbours: {o['text']} {o['at']:.2f}-{o['end']:.2f}")
    for i, o in enumerate(owner):              # per-line token times; an unmatched token takes the previous token's time
        n = subs[o][0]
        t = time_of[i][1] if time_of[i] else (line_tok[n][-1][1] if line_tok.get(n) else None)
        if t is not None:
            line_tok.setdefault(n, []).append([ref[i], round(t, 3)])
    spoken = duration(C / "audio.m4a")
    total = film_end(spoken, doc)   # the last subtitle still ends 0.6 s after the voice (below)
    speech_end = {n: max(o["end"] for o in out if o["line"] == n) for n in range(1, len(lines) + 1)}
    first_at = {n: min(o["at"] for o in out if o["line"] == n) for n in range(1, len(lines) + 1)}
    for i in range(len(out) - 1):
        out[i]["end"] = out[i + 1]["at"]
    out[-1]["end"] = round(min(total, spoken + 0.6), 2)
    fmt = lambda t: f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d},{min(999, int(round((t % 1) * 1000))):03d}"
    (C / "final.srt").write_text("\n".join(f"{i}\n{fmt(o['at'])} --> {fmt(o['end'])}\n{o['text']}\n" for i, o in enumerate(out, 1)), encoding="utf-8")
    # the same screens with the script line each belongs to: doc_cut times a second-language line (doc.json "en") by it
    (C / "screens.json").write_text(json.dumps([{**o, "at": round(o["at"], 3), "end": round(o["end"], 3)} for o in out],
                                               ensure_ascii=False, indent=0), encoding="utf-8")
    def phrase_at(n, phrase):                  # a beat may open mid-line: "from" names the phrase it starts on
        seq, want = line_tok.get(n, []), tokens(phrase, lang)
        for i in range(len(seq) - len(want) + 1):
            if [tk for tk, _ in seq[i:i + len(want)]] == want:
                return seq[i][1]
        sys.exit(f"✗ \"from\" phrase not in line {n}: {phrase}")
    beats = []
    for bi, b in enumerate(doc["beats"]):
        n0 = b["lines"][0]
        if bi == 0:
            start = 0.0
        elif b.get("from"):
            start = round(max(beats[-1]["start"] + 0.3, phrase_at(n0, b["from"]) - 0.08), 2)
        elif b.get("start") == "after_prev":
            start = round(speech_end[n0 - 1] + 0.15, 2)
        else:
            start = round(max(speech_end.get(n0 - 1, 0), first_at[n0] - PRE), 2)
        beats.append({"id": b["id"], "lines": b["lines"], "source": b["source"], "start": start, "first_word": round(first_at[n0], 2),
                      "text": " ".join(lines[n - 1]["text"] for n in b["lines"]),
                      "tokens": [[tk, round(t - start, 3)] for n in b["lines"] for tk, t in line_tok.get(n, [])]})
    for i, b in enumerate(beats):
        b["end"] = beats[i + 1]["start"] if i + 1 < len(beats) else total
        b["duration"] = round(b["end"] - b["start"], 2)
        b["tokens"] = [x for x in b["tokens"] if -PRE <= x[1] < b["duration"]]   # lines shared by split beats: keep this beat's span
        b["gen_seconds"] = max(3, math.ceil(b["duration"] + 0.1))
    (P / "beats.json").write_text(json.dumps({"total": total, "beats": beats}, ensure_ascii=False, indent=1), encoding="utf-8")
    for b in beats:
        print(f"{b['id']:>4} {b['source']:4} {b['start']:6.2f}-{b['end']:6.2f} ({b['duration']:5.2f}s → gen {b['gen_seconds']}s) {b['text'][:34]}")
    print(f"total {total}s; {len(out)} subtitle screens; worst match {worst:.2f}")
    over = [b["id"] for b in beats if b["source"] == "ve" and b["gen_seconds"] > 10]
    if over:
        sys.exit(f"✗ VE beats over 10 s, split them: {over}")


if __name__ == "__main__":
    main()
