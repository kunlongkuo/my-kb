"""MiniMax Music 3 on the user's own Google Colab GPU: a song or an instrumental for Optional C (background music).

  python3 tools/music3/music3_film.py plan <project> --caption-file <caption.txt> [--lyrics-file <lyrics.txt>]
                                           [--seconds N] [--seed 7]
      writes <project>/music3/job.json. Without --lyrics-file the piece is instrumental. --seconds defaults to the
      length of the narration (tts/lines.json, last line end + 3 s); a song with lyrics needs it given.
  python3 tools/music3/music3_film.py run <project> --confirmed [--gpu L4]
      boot one Colab GPU → install diffusers → generate in the background on the machine → download
      <project>/music3/out/<id>.wav → release the GPU (always, also on failure or Ctrl-C).
      --confirmed: the user has seen the spec and agreed to spend the compute units.
  python3 tools/music3/music3_film.py collect <project>
      the WAV → <project>/music3_bgm.wav; doc.json "bgm": src and credit set, other bgm keys kept.

Needs google-colab-cli installed and logged in (the same login as tools/h3). No territory check: the Music 3 licence
has no territory limit. Lyrics must be the user's own; a published film is labelled as AI-generated.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

GPUS = ("L4", "A100")
MIN_SECONDS, MAX_SECONDS = 10, 360
MIN_CAPTION_WORDS = 25
POLL = 45                 # seconds between status reads
MAX_MINUTES = 60          # give up (and release the GPU) after this long on the machine
MAX_READ_FAILS = 6        # colab-cli drops a connection now and then: only this many failed reads in a row end the run
CREDIT = "MiniMax Music 3（AI 生成）"
REMOTE_DIR = "/content/m3"

REMOTE = r'''
import json, subprocess, sys, time, traceback
D = "/content/m3"
def state(**kw):
    s = json.load(open(D + "/state.json")) if __import__("os").path.exists(D + "/state.json") else {}
    s.update(kw, at=time.strftime("%H:%M:%S"))
    json.dump(s, open(D + "/state.json", "w"))
try:
    state(stage="installing")
    r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", "git+https://github.com/huggingface/diffusers",
                        "transformers", "accelerate", "soundfile"], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("pip install failed: " + r.stderr[-800:])
    import numpy as np, soundfile as sf, torch
    from diffusers import ModularPipeline, ComponentsManager
    job = json.load(open(D + "/job.json"))
    state(stage="loading", gpu=torch.cuda.get_device_name(0))
    t0 = time.time()
    if torch.cuda.get_device_properties(0).total_memory < 40e9:      # L4: components moved to the GPU as needed
        m = ComponentsManager(); m.enable_auto_cpu_offload(device="cuda")
        pipe = ModularPipeline.from_pretrained("MiniMaxAI/MiniMax-Music3", components_manager=m)
        pipe.load_components(dtype=torch.bfloat16)
    else:
        pipe = ModularPipeline.from_pretrained("MiniMaxAI/MiniMax-Music3")
        pipe.load_components(dtype=torch.bfloat16); pipe.to("cuda")
    state(stage="generating", load_s=round(time.time() - t0))
    t0 = time.time(); torch.cuda.reset_peak_memory_stats()
    a = pipe(prompt=job["caption"], lyrics=job["lyrics"], audio_duration=float(job["seconds"]),
             generator=torch.Generator("cuda").manual_seed(int(job["seed"])), output="audios")[0]
    w = a.T.detach().cpu().float().numpy() if torch.is_tensor(a) else np.asarray(a, dtype=np.float32).T
    sf.write(D + "/" + job["id"] + ".wav", w, pipe.sampling_rate)
    state(stage="done", gen_s=round(time.time() - t0), audio_s=round(len(w) / pipe.sampling_rate, 1),
          peak_gb=round(torch.cuda.max_memory_allocated() / 1e9, 1))
except Exception as e:
    state(stage="error", error=repr(e)[-600:], trace=traceback.format_exc()[-1500:])
'''
LAUNCH = ("import subprocess\nsubprocess.Popen(['python', '/content/m3/gen.py'], stdin=subprocess.DEVNULL, "
          "stdout=open('/content/m3/log.txt', 'w'), stderr=subprocess.STDOUT, start_new_session=True)\nprint('launched')\n")
MKDIR = "import os\nos.makedirs('/content/m3', exist_ok=True)\nprint('ok')\n"
STATUS = "import os\nprint('STATE ' + (open('/content/m3/state.json').read() if os.path.exists('/content/m3/state.json') else '{}'))\n"


# ---------------------------------------------------------------- plan
def project(arg):
    p = Path(arg).expanduser().resolve()
    return p.parent if p.name == "doc.json" else p


def narration_seconds(P):
    f = P / "tts/lines.json"
    if not f.is_file():
        return None
    data = json.loads(f.read_text(encoding="utf-8"))
    lines = data["lines"] if isinstance(data, dict) else data
    return round(max(float(l["end"]) for l in lines) + 3.0, 1) if lines else None


def check_job(job):
    bad = []
    n = len(job.get("caption", "").split())
    if n < MIN_CAPTION_WORDS:
        bad.append(f"caption has {n} words; describe style/tempo, vocals and arrangement in at least {MIN_CAPTION_WORDS}")
    if not job.get("lyrics", "").strip():
        bad.append("lyrics are empty (an instrumental needs at least [Instrumental])")
    s = job.get("seconds")
    if not isinstance(s, (int, float)) or not MIN_SECONDS <= s <= MAX_SECONDS:
        bad.append(f"seconds {s} is outside {MIN_SECONDS}-{MAX_SECONDS}")
    return bad


def plan(P, caption, lyrics=None, seconds=None, seed=7):
    instrumental = lyrics is None
    if seconds is None:
        if not instrumental:
            sys.exit("✗ a song with lyrics needs --seconds (how long the song should be)")
        seconds = narration_seconds(P)
        if seconds is None:
            sys.exit("✗ no tts/lines.json to take the film length from: give --seconds")
    job = {"id": "song" if not instrumental else "bgm", "seconds": float(seconds), "seed": int(seed),
           "caption": caption.strip(),
           "lyrics": "[Intro]\n[Instrumental]\n\n[Verse]\n[Instrumental]\n\n[Outro]\n[Instrumental]\n" if instrumental
           else lyrics.strip() + "\n"}
    bad = check_job(job)
    if bad:
        sys.exit("✗ not planned:\n  " + "\n  ".join(bad))
    (P / "music3").mkdir(exist_ok=True)
    (P / "music3/job.json").write_text(json.dumps(job, ensure_ascii=False, indent=1), encoding="utf-8")
    return job


# ---------------------------------------------------------------- run
def colab(*args, timeout=900):
    exe = shutil.which("colab") or str(Path.home() / ".local/bin/colab")
    try:
        p = subprocess.run([exe, *map(str, args)], capture_output=True, text=True, timeout=timeout,
                           stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    return (p.stdout or "") + (p.stderr or "")


def exec_code(session, code, timeout=60):
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code)
    try:
        return colab("exec", "-s", session, "-f", f.name, "--timeout", timeout, timeout=timeout + 60)
    finally:
        Path(f.name).unlink()


def read_state(out):
    """The machine's state.json from a STATUS read; None when the read itself failed (a dropped connection)."""
    for line in (out or "").splitlines():
        if line.startswith("STATE "):
            try:
                return json.loads(line[6:])
            except ValueError:
                return None
    return None


def watch(session, poll=POLL, max_minutes=MAX_MINUTES, clock=time.monotonic, sleep=time.sleep):
    """Poll until the machine says done or error. Only state.json decides the end: a failed read (colab-cli drops a
    connection now and then) is retried, MAX_READ_FAILS in a row give up."""
    start, fails, last = clock(), 0, None
    while clock() - start < max_minutes * 60:
        sleep(poll)
        st = read_state(exec_code(session, STATUS))
        if st is None:
            fails += 1
            if fails >= MAX_READ_FAILS:
                return {"stage": "error", "error": f"{fails} status reads in a row failed"}
            continue
        fails = 0
        if st.get("stage") != last:
            last = st.get("stage")
            print(f"[{(clock() - start) / 60:4.1f} min] {last}", flush=True)
        if last in ("done", "error"):
            return st
    return {"stage": "error", "error": f"not finished after {max_minutes} minutes"}


def run(P, gpu="L4", confirmed=False):
    jf = P / "music3/job.json"
    job = json.loads(jf.read_text(encoding="utf-8")) if jf.is_file() else sys.exit("✗ run plan first")
    bad = check_job(job)
    if bad:
        sys.exit("✗ not sent:\n  " + "\n  ".join(bad))
    if gpu not in GPUS:
        sys.exit(f"✗ --gpu takes {GPUS} (a mistyped name makes colab-cli boot an A100)")
    if not confirmed:
        sys.exit(f"✗ {job['seconds']:g} s of music on {gpu}: show the user this and ask before spending compute units, "
                 "then add --confirmed")
    session = f"s2f-m3-{P.name}"[:40]
    if session in colab("sessions", timeout=120):
        sys.exit(f"✗ {session} is already running: wait for it, or `colab stop -s {session}`")
    print(f"booting {gpu} ({session})", flush=True)
    try:
        colab("new", "-s", session, "--gpu", gpu)
        if session not in colab("sessions", timeout=120):
            sys.exit("✗ the Colab machine did not boot (often no free GPU of that kind); nothing was generated")
        exec_code(session, MKDIR)
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "gen.py").write_text(REMOTE, encoding="utf-8")
            for f in (Path(tmp) / "gen.py", jf):
                colab("upload", "-s", session, f, f"{REMOTE_DIR}/{f.name}", timeout=300)
        exec_code(session, LAUNCH)
        st = watch(session)
        if st.get("stage") != "done":
            sys.exit(f"✗ {st.get('error', 'failed')}\n{st.get('trace', '')}")
        out = P / "music3/out"
        out.mkdir(parents=True, exist_ok=True)
        colab("download", "-s", session, f"{REMOTE_DIR}/{job['id']}.wav", out / f"{job['id']}.wav", timeout=600)
        if not (out / f"{job['id']}.wav").is_file():
            sys.exit("✗ generated, but the download failed")
        (out / "result.json").write_text(json.dumps(dict(st, gpu=gpu), indent=1), encoding="utf-8")
        print(f"✓ {out / (job['id'] + '.wav')}: {st.get('audio_s')} s of audio, generated in {st.get('gen_s')} s "
              f"(load {st.get('load_s')} s, peak {st.get('peak_gb')} GB)")
    finally:
        print("released: " + " ".join(colab("stop", "-s", session, timeout=300).split()[-3:]), flush=True)


# ---------------------------------------------------------------- collect
def collect(P):
    job = json.loads((P / "music3/job.json").read_text(encoding="utf-8"))
    src = P / "music3/out" / f"{job['id']}.wav"
    if not src.is_file():
        sys.exit(f"✗ {src} is not there: run first")
    dst = P / "music3_bgm.wav"
    if dst.exists():
        shutil.copy2(dst, P / "music3_bgm.bak.wav")
    shutil.copy2(src, dst)
    df = P / "doc.json"
    doc = json.loads(df.read_text(encoding="utf-8")) if df.is_file() else {}
    doc["bgm"] = dict(doc.get("bgm") or {}, src=dst.name, credit=CREDIT)
    df.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"✓ {dst.name}; doc.json bgm.src and bgm.credit set")
    return dst


# ---------------------------------------------------------------- cli
def opt(args, name, default=None):
    return args[args.index(name) + 1] if name in args else default


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if len(a) < 2 or a[0] not in ("plan", "run", "collect"):
        sys.exit(__doc__)
    P = project(a[1])
    if a[0] == "plan":
        cf, lf = opt(a, "--caption-file"), opt(a, "--lyrics-file")
        if not cf:
            sys.exit("✗ --caption-file is required")
        secs = opt(a, "--seconds")
        job = plan(P, Path(cf).read_text(encoding="utf-8"), Path(lf).read_text(encoding="utf-8") if lf else None,
                   float(secs) if secs else None, int(opt(a, "--seed", 7)))
        print(f"✓ {P / 'music3/job.json'}: {job['id']}, {job['seconds']:g} s, seed {job['seed']}")
    elif a[0] == "run":
        run(P, opt(a, "--gpu", "L4").upper(), "--confirmed" in a)
    else:
        collect(P)


if __name__ == "__main__":
    main()
