"""MiniMax H3 on the user's own Google Colab GPU, for Optional A (generated shots) and Optional B (host).

  python3 tools/h3/h3_film.py plan <project>/doc.json [--shots] [--host --look <picture> --who "<person, clothes>"]
                                   [--where "<place>"] [--resolution 480P] [--model-set official]
      writes <project>/h3/manifest.json and copies what it needs into <project>/h3/inputs/.
      Shots: one job per VE beat of beats.json (shotK, K in VE-beat order), a DRAFT prompt from doc.json "shots" that the
      agent rewrites (H3 burns subtitles into short prompts) before the run; a picture h3/inputs/shotK.png, when present,
      is used as the first frame. Host: one job per host/parts/partK.mp3 (doc_host.py split --max 15 --min 4), locked to
      that audio, the look picture as the reference, the lines placed at their times inside the part.
  python3 tools/h3/h3_film.py run <project>/doc.json --confirmed [--gpu L4] [--keep MIN] [--skip-checklist "<reason>"]
      start checklist (h3-territory included) → boot a Colab GPU → stop at once unless the machine is in the licence
      territory → the upstream runner (S2F_H3_SKILL_DIR/scripts/h3run.py) generates and downloads into h3/out/.
      --confirmed: the user has seen the spec and agreed to spend the compute units. --keep: keep the GPU MIN minutes
      for the next batch (otherwise it is released when the batch ends).
  python3 tools/h3/h3_film.py collect <project>/doc.json [--theme <theme>]
      h3/out/shotK.mp4 → ve_<look>/shotK.mp4, h3/out/hostK.mp4 → host/parts/partK.mp4 (an older file is kept as .bak.mp4).

Needs the upstream skill (github.com/dseditor/h3-colab-skill, MIT) installed with google-colab-cli and logged in
(its INSTALL_FOR_AGENTS.md); S2F_H3_SKILL_DIR is its h3-multimodal-colab folder.
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / 'tools/config'))
import s2f_config; s2f_config.load()

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "skills/ve-director/doc/scripts"))
sys.path.insert(0, str(REPO / "tools/checklist"))

MAX_LOCK = 15.0          # H3 locks at most 15 s of audio per clip
MIN_SECONDS = 2          # H3 clip length range
MAX_SECONDS = 15
MIN_WORDS = 300          # shorter video prompts make H3 burn subtitles into the picture (upstream prompt-guide.md)
# The H3 open-weight licence (MiniMax H3 Community License, 2026-08-02) excludes these: US, UK, KR and the EU members.
EXCLUDED = {"US", "GB", "KR", "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT",
            "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"}
GPUS = ("L4", "G4")
# Fallback when the IP lookup fails: the Google Cloud region in the Colab machine's URL (…-c.asia-southeast1.prod.r.colab.dev).
# Only regions listed here count; any other region, or no URL, stops the run.
REGION_COUNTRY = {"asia-east1": "TW", "asia-east2": "HK", "asia-northeast1": "JP", "asia-northeast2": "JP",
                  "asia-northeast3": "KR", "asia-south1": "IN", "asia-south2": "IN", "asia-southeast1": "SG",
                  "asia-southeast2": "ID", "australia-southeast1": "AU", "australia-southeast2": "AU"}
PROBE_TRIES, PROBE_WAIT = 3, 20
PROBE = "import urllib.request\nprint(urllib.request.urlopen('https://ipinfo.io/json', timeout=15).read().decode())\n"


# ---------------------------------------------------------------- plan
def words(text):
    return len(re.findall(r"[A-Za-z0-9']+", text))


def shot_draft(sh, seconds, style):
    """A starting point from doc.json "shots": the agent rewrites it into a full 350-500 word prompt."""
    acts = " ".join(f"From {a * seconds:.1f} s to {b * seconds:.1f} s, {t[0].lower() + t[1:]}" for a, b, t in sh.get("acts", []))
    return (f"integrated_multimodal_description: [Shot 1] {style} {sh['scene']}. {sh.get('ident', '')}. {acts} "
            f"{sh.get('camera', '')} There is no text, no subtitle, no caption, no logo and no writing anywhere on the "
            f"screen.\n\noverall_soundscape: Quiet room tone.\n\nnon_diegetic_music: N/A")


def host_lines(lines, part):
    """The narration lines inside one host part, with their start times relative to the part."""
    out = []
    for ln in lines:
        mid = (ln["start"] + ln["end"]) / 2
        if part["start"] <= mid < part["end"]:
            out.append((max(0.0, ln["start"] - part["start"]), ln["text"]))
    return out


def host_prompt(who, where, said, lang="Mandarin"):
    """Reference generation locked to the part's audio (@音訊1 = the recording, @圖片1 = the look picture)."""
    talk = []
    for k, (t, text) in enumerate(said):
        when = "At the start" if k == 0 or t < 0.3 else f"At 00:{t:06.3f}"
        talk.append(f"{when} <Subject 1> says: <d>[{lang}] {text}</d> and ends the sentence with a small, natural nod.")
    place = where or "the place shown in @圖片1"
    return f"""subject_definitions:
<Subject 1> is the person in @圖片1: {who}.
@圖片1 is also the location reference: {place}.
@音訊1 is the recorded voice of <Subject 1> (S1); the lips follow it exactly.

summary:
[reference generation + audio lock] <Subject 1> talks to the camera, explaining calmly.

retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - face, hairstyle, clothing, body position and framing from @圖片1.
@圖片1: location reference - background, props and light.
@音訊1: locked source - the dialogue audio of <Subject 1>, kept as it is.

detailed_description:
The target video is a static medium shot framed from head to waist, live-action, cinematic, matching the framing and composition of @圖片1: <Subject 1> faces the camera directly, shoulders level and square to the lens, and keeps the same place for the whole video. The background stays exactly as in @圖片1, sharp and still.
[Shot 1] <Subject 1> (S1), speaking in a calm, clear, warm voice at an even, unhurried rate, talks to the camera, the lips moving precisely with @音訊1. {' '.join(talk)} Between sentences the eyes blink naturally and the breathing is soft; the eyes stay on the camera. The mouth opens a little wider on open vowels and closes fully on the consonants b, p and m, and the jaw, cheeks and throat move with the words the way a real speaker's do. The head moves only slightly with the rhythm of the speech, the shoulders stay relaxed and the hands stay low and still. Facial movements are natural and restrained, with no exaggerated expressions and no large gestures; the face, hair and clothing stay exactly the same person as in @圖片1 from the first frame to the last. The camera holds a static shot with no camera movement and no cut. The light is soft and even, steady throughout. There is no text, no subtitle, no caption, no logo and no writing anywhere on the screen.

overall_soundscape:
Quiet indoor room tone; no other voices.

non_diegetic_music:
N/A"""


def plan_shots(doc, P, theme, resolution):
    from doc_common import read_beats
    from doc_runsheet import style_for
    from doc_themes import ve_look, ve_theme
    look = ve_look(doc, theme)
    th = ve_theme(look, doc.get("palette") if look == "collage" else None)   # a palette re-inks collage only (doc_themes)
    spec = {b["id"]: b for b in doc["beats"]}
    jobs = []
    for k, b in enumerate([b for b in read_beats(P / "beats.json")["beats"] if b["source"] == "ve"], 1):
        sec = min(MAX_SECONDS, max(MIN_SECONDS, int(b["gen_seconds"])))
        sh = doc["shots"][spec[b["id"]]["shot"]]
        job = {"id": f"shot{k}", "type": "video", "mode": "text", "seconds": sec, "aspect": "16:9",
               "resolution": resolution, "intensity": "off", "draft": True, "beat": b["id"],
               "prompt": shot_draft(sh, sec, style_for(sh, th))}
        if (P / "h3/inputs" / f"shot{k}.png").exists():
            job.update(mode="frames", first=f"inputs/shot{k}.png")
        jobs.append(job)
    return jobs


def plan_host(doc, P, look, who, where, resolution):
    from doc_common import read_json
    parts = read_json(P / "host/parts.json", "run doc_host.py split <doc.json> --max 15 --min 4 first")
    lines = read_json(P / "tts/lines.json", "run doc_voice.py first")
    long = [p for p in parts if p["end"] - p["start"] + p.get("tail", 0.0) > MAX_LOCK + 0.05]   # tail: doc_host's closing silence
    if long:
        sys.exit(f"✗ H3 locks at most {MAX_LOCK:g} s of audio; part{long[0]['k']} is {long[0]['end'] - long[0]['start']:.1f} s: "
                 f"run doc_host.py split <doc.json> --max 15 --min 4 again")
    src = Path(look)
    if not src.is_file():
        sys.exit(f"✗ look picture not found: {look}")
    inp = P / "h3/inputs"
    inp.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, inp / f"look{src.suffix.lower()}")
    lang = {"zh": "Mandarin", "en": "English"}.get(doc.get("lang", "zh"), "Mandarin")
    jobs = []
    for p in parts:
        mp3 = P / "host/parts" / f"part{p['k']}.mp3"
        if not mp3.exists():
            sys.exit(f"✗ missing {mp3}: run doc_host.py split first")
        shutil.copy2(mp3, inp / mp3.name)
        jobs.append({"id": f"host{p['k']}", "type": "video", "mode": "ref", "inputs": [f"inputs/look{src.suffix.lower()}"],
                     "drive_audio": f"inputs/{mp3.name}", "seconds": round(p["end"] - p["start"] + p.get("tail", 0.0), 3), "aspect": "16:9",
                     "resolution": resolution, "intensity": "off",
                     "prompt": host_prompt(who, where, host_lines(lines, p), lang)})
    return jobs


# ---------------------------------------------------------------- run
def check_jobs(jobs):
    """Problems that would waste compute units: drafts not rewritten, prompts too short, lengths H3 cannot make."""
    bad = []
    for j in jobs:
        if j.get("draft"):
            bad.append(f"{j['id']}: still a draft (rewrite the prompt, then delete \"draft\")")
        if j["type"] == "video" and words(j["prompt"]) < MIN_WORDS:
            bad.append(f"{j['id']}: prompt has {words(j['prompt'])} words; H3 needs {MIN_WORDS}+ or it burns subtitles")
        if j["type"] == "video" and not MIN_SECONDS <= float(j.get("seconds", 10)) <= MAX_SECONDS:
            bad.append(f"{j['id']}: {j.get('seconds')} s is outside {MIN_SECONDS}-{MAX_SECONDS} s")
    return bad


def country_of(probe_output):
    m = re.search(r'"country"\s*:\s*"([A-Z]{2})"', probe_output or "")
    return m.group(1) if m else None


def region_of(url):
    m = re.search(r"\.([a-z]+-[a-z]+\d+)\.prod\.", url or "")
    return m.group(1) if m else None


def region_country(region):
    if region and region.startswith("us-"):
        return "US"
    return REGION_COUNTRY.get(region)


def session_url(session):
    """The machine URL colab-cli keeps for a session (None when it is not there: the machine did not boot)."""
    p = Path(os.environ.get("COLAB_CLI_SESSIONS", Path.home() / ".config/colab-cli/sessions.json"))
    try:
        return json.loads(p.read_text(encoding="utf-8")).get(session, {}).get("url")
    except (OSError, ValueError):
        return None


def machine_country(session, probe_file, wait=PROBE_WAIT):
    """(country, how): the IP lookup, tried PROBE_TRIES times; then the region in the machine's URL."""
    for k in range(PROBE_TRIES):
        cc = country_of(colab("exec", "-s", session, "-f", probe_file, "--timeout", 90, timeout=180))
        if cc:
            return cc, "IP lookup"
        if k < PROBE_TRIES - 1:
            time.sleep(wait)
    region = region_of(session_url(session))
    return region_country(region), f"region {region}" if region else "no machine URL"


def territory_ok(cc):
    return cc is not None and cc not in EXCLUDED


def colab(*args, timeout=900):
    exe = shutil.which("colab") or str(Path.home() / ".local/bin/colab")
    p = subprocess.run([exe, *map(str, args)], capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
    return (p.stdout or "") + (p.stderr or "")


def upstream():
    d = os.environ.get("S2F_H3_SKILL_DIR")
    if not d or not (Path(d).expanduser() / "scripts/h3run.py").is_file():
        sys.exit("✗ S2F_H3_SKILL_DIR must point at the h3-multimodal-colab folder of github.com/dseditor/h3-colab-skill "
                 "(see tools/h3/README.md)")
    return Path(d).expanduser()


def run(P, args):
    import checklist
    mf = P / "h3/manifest.json"
    m = json.loads(mf.read_text(encoding="utf-8")) if mf.exists() else sys.exit("✗ run plan first")
    bad = check_jobs(m["jobs"])
    if bad:
        sys.exit("✗ not sent:\n  " + "\n  ".join(bad))
    if not args["confirmed"]:
        secs = sum(float(j.get("seconds", 10)) for j in m["jobs"] if j["type"] == "video")
        sys.exit(f"✗ {len(m['jobs'])} jobs, {secs:g} s of video on {args['gpu']}: show the user this and ask before spending "
                 f"compute units, then add --confirmed")
    checklist.gate(str(P), "start", args["skip"], "h3")
    h3run = upstream() / "scripts/h3run.py"
    session = f"s2f-h3-{P.name}"[:40]
    if session in colab("sessions", timeout=120):   # kept from the last batch (--keep): checked when it booted
        print(f"reusing {session} (kept from the last batch; models already on it)", flush=True)
    else:
        print(f"booting {args['gpu']} ({session}) and checking where it is", flush=True)
        colab("new", "-s", session, "--gpu", args["gpu"])
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(PROBE)
        try:
            cc, how = machine_country(session, f.name)
        finally:
            os.unlink(f.name)
        print(f"Colab machine country: {cc or 'unknown'} ({how})", flush=True)
        if not territory_ok(cc):
            colab("stop", "-s", session, timeout=300)
            if how == "no machine URL":
                sys.exit("✗ stopped: the Colab machine did not boot (no URL for it, the country lookup got no answer); "
                         "nothing was generated. Try again later or another GPU.")
            sys.exit(f"✗ stopped: the machine is in {cc or 'an unknown country'} ({how}), outside the H3 licence territory "
                     "or not known to be inside it; the GPU was released. Try again later.")
    cmd = [sys.executable, "-u", str(h3run), "run", str(mf), "--gpu", args["gpu"], "--session", session, "--confirmed"]
    cmd += ["--idle-minutes", str(args["keep"])] if args["keep"] else ["--stop-after"]
    sys.exit(subprocess.run(cmd).returncode)


# ---------------------------------------------------------------- collect
def collect(doc, P, theme):
    from doc_themes import ve_look
    out, moved = P / "h3/out", []
    for f in sorted(out.glob("*.mp4")):
        m = re.fullmatch(r"(shot|host)(\d+)\.mp4", f.name)
        if not m:
            continue
        dst = (P / f"ve_{ve_look(doc, theme)}" / f.name) if m[1] == "shot" else (P / "host/parts" / f"part{m[2]}.mp4")
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            dst.replace(dst.with_suffix(".bak.mp4"))
        shutil.copy2(f, dst)
        moved.append((f.name, dst))
    for a, b in moved:
        print(f"{a} → {b.relative_to(P)}")
    if not moved:
        sys.exit(f"✗ nothing to collect in {out}")


def opt(argv, name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


def main(argv):
    if len(argv) < 2 or argv[0] not in ("plan", "run", "collect"):
        sys.exit(__doc__)
    from doc_common import load
    doc, P = load(argv[1])
    theme = opt(argv, "--theme", doc.get("theme", "collage"))
    if argv[0] == "plan":
        res = opt(argv, "--resolution", "480P")
        jobs = plan_shots(doc, P, theme, res) if "--shots" in argv else []
        if "--host" in argv:
            if not opt(argv, "--look") or not opt(argv, "--who"):
                sys.exit("✗ --host needs --look <picture> and --who \"<who is in it, clothes>\"")
            jobs += plan_host(doc, P, opt(argv, "--look"), opt(argv, "--who"), opt(argv, "--where"), res)
        if not jobs:
            sys.exit("✗ nothing to plan: give --shots and/or --host")
        if opt(argv, "--model-set"):
            for j in jobs:
                j["model_set"] = opt(argv, "--model-set")
        (P / "h3").mkdir(exist_ok=True)
        (P / "h3/manifest.json").write_text(json.dumps({"gpu": "L4", "stop_on_error": False, "jobs": jobs},
                                                       ensure_ascii=False, indent=1), encoding="utf-8")
        drafts = [j["id"] for j in jobs if j.get("draft")]
        print(f"h3/manifest.json: {', '.join(j['id'] for j in jobs)}" + (f"\nrewrite these draft prompts first: {', '.join(drafts)}" if drafts else ""))
    elif argv[0] == "run":
        gpu = opt(argv, "--gpu", "L4").upper()
        if gpu not in GPUS:
            sys.exit(f"✗ --gpu must be one of {GPUS}")
        run(P, {"gpu": gpu, "keep": int(opt(argv, "--keep", 0)), "confirmed": "--confirmed" in argv,
                "skip": opt(argv, "--skip-checklist")})
    else:
        collect(doc, P, theme)


if __name__ == "__main__":
    main(sys.argv[1:])
