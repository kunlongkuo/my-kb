#!/usr/bin/env bash
# Clean-environment acceptance for doc mode.
#
# Proves that doc mode runs from voice to a base render without Cutline and without any API key:
#   - clones this repo to a temp folder and lays the working tree's uncommitted changes and untracked files over it
#   - runs everything with an empty temp HOME (no ~/.config/script2film/secrets.json), no keys, and only the S2F_*
#     variable names: the old names without the prefix are read once to work out the new ones, then cleared;
#     CUTLINE_DIR, PROMPTSTUDIO_DIR, S2F_DIR and the key names are cleared and checked to be gone
#   - models and browsers are not downloaded again: they are pointed at the real home's existing folders
#   - npm ci, the doc-mode test suite, then the trial film from doc_tts.py to doc_cut.py --render,
#     then a second copy with "sfx_on" and a bgm bed (doc_code --render, doc_sfx --report, doc_cut --render,
#     cut_*/plan.json written, cut_*/index.html has id="bgm" (s2f-1b T9),
#     loudness of that render: -14±0.8 LUFS, peak <= -1.0 dBTP)
# Every step prints "STEP|<name>|<exit>|<seconds>"; the first failing step stops the script with its exit code.
# The temp folders are printed at the end and kept for inspection.
#
#   bash tools/check-standalone.sh [<trial project folder>]
# Default trial project: examples/coffee in this repository (read only: it is copied to a temp folder first).
# When the trial project has an expected.json, the film's beats, lines and length are checked against it.
# After it, examples/brewing is made once from its premade files (skipped when the clone has no premade folder), and its
# Chinese script is voiced once more from scratch (doc_tts.py, doc_voice.py only), because examples/coffee is in English.
# Rendering itself needs no network (GSAP comes from npm since s2f-3c); `npm ci` and the first model use do.
set -u -o pipefail

REAL_HOME="${REAL_HOME:-$HOME}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EP="${1:-$SRC/examples/coffee}"
THEME=lecture-finance

WORK="$(mktemp -d "${TMPDIR:-/tmp}/s2f-standalone.XXXXXX")"
TMPHOME="$(mktemp -d "${TMPDIR:-/tmp}/s2f-home.XXXXXX")"
REPO="$WORK/repo"
DOC="$REPO/skills/ve-director/doc"
P1="$WORK/proj1"
P2="$WORK/proj2"
P3="$WORK/proj3"   # examples/brewing made from its premade files (generated shot + host), no voice step
TIMES="$WORK/timing.tsv"
: > "$TIMES"

echo "source repository: ${SRC}"
echo "trial project: ${EP} (read only)"
echo "temp folder: ${WORK}"
echo "temp HOME: ${TMPHOME}"

summary() {
  echo
  echo "== seconds per step"
  column -t -s '|' "$TIMES" 2>/dev/null || cat "$TIMES"
  echo "temp folder (kept): ${WORK}"
  echo "temp HOME (kept): ${TMPHOME}"
}

# step <name> <command...>: run, time it, print STEP|name|rc|secs, stop on a non-zero exit.
step() {
  local name="$1"; shift
  local t0 t1 rc
  echo
  echo "== ${name}"
  t0=$(date +%s)
  "$@"
  rc=$?
  t1=$(date +%s)
  echo "STEP|${name}|${rc}|$((t1 - t0))"
  echo "${name}|${rc}|$((t1 - t0))" >> "$TIMES"
  if [ "$rc" -ne 0 ]; then
    echo "✗ ${name} failed (exit ${rc}); stopping"
    summary
    exit "$rc"
  fi
}

fail() { echo "✗ $*"; return 1; }

# ---------------------------------------------------------------- environment
# the new names (S2F_*) are worked out before the old ones are cleared, so a shell with only the old names still runs;
# with neither set, the two voice folders come from the settings file (tools/config/s2f_config.py --export, read with
# the real home); with none of the three there is no guess: the script says so and stops
S2F_QWEN_TTS_DIR="${S2F_QWEN_TTS_DIR:-${QWEN_TTS_DIR:-}}"
if [ -z "${S2F_WHISPER_CPP_MODEL:-}" ] || [ -z "$S2F_QWEN_TTS_DIR" ]; then
  CFG_EXPORT="$(HOME="$REAL_HOME" python3 "$SRC/tools/config/s2f_config.py" --export 2>/dev/null)"
  cfg_val() { (eval "$CFG_EXPORT"; printf '%s' "${!1:-}"); }
  S2F_WHISPER_CPP_MODEL="${S2F_WHISPER_CPP_MODEL:-$(cfg_val S2F_WHISPER_CPP_MODEL)}"
  S2F_WHISPER_CLI="${S2F_WHISPER_CLI:-$(cfg_val S2F_WHISPER_CLI)}"
  S2F_QWEN_TTS_DIR="${S2F_QWEN_TTS_DIR:-$(cfg_val S2F_QWEN_TTS_DIR)}"
fi
for v in S2F_WHISPER_CPP_MODEL S2F_QWEN_TTS_DIR; do
  if [ -z "${!v}" ]; then
    echo "✗ ${v} not found: set this environment variable or put it in the config file (python3 tools/config/s2f_config.py --show shows the current values; tools/doctor/setup_voice.sh installs the voice and transcription environments); stopping"
    exit 1
  fi
done
S2F_QWEN_TTS_MODELS="${S2F_QWEN_TTS_MODELS:-${QWEN_TTS_MODELS:-$S2F_QWEN_TTS_DIR/../_models}}"
for v in CUTLINE_DIR GROQ_API_KEY ELEVENLABS_API_KEY ELEVEN_API_KEY GEMINI_API_KEY S2F_ASSETS_LOCAL PROMPTSTUDIO_DIR S2F_DIR S2F_HF_BIN \
         QWEN_TTS_DIR QWEN_TTS_MODELS MLX_WHISPER_DIR S2F_MLX_WHISPER_DIR CONCAT_BIN VE_HEADED; do
  unset "$v"
done
export HOME="$TMPHOME"
export S2F_WHISPER_CPP_MODEL S2F_QWEN_TTS_DIR S2F_QWEN_TTS_MODELS
[ -n "${S2F_WHISPER_CLI:-}" ] && export S2F_WHISPER_CLI
# The font files are not in git, so the clone has none: read the source checkout's assets/. Its sfx/ (sounds and
# manifest) ships with the repository, the same as the clone's; with S2F_ASSETS_LOCAL unset only those sounds are used.
export S2F_ASSETS="$SRC/assets"
export HF_HOME="$REAL_HOME/.cache/huggingface"
export HF_HUB_OFFLINE=1
export PLAYWRIGHT_BROWSERS_PATH="$REAL_HOME/Library/Caches/ms-playwright"
export PALETTE_SRC_ROOTS=/nonexistent
HYPERFRAMES_BROWSER_PATH="$(find "$REAL_HOME/.cache/hyperframes/chrome" -name chrome-headless-shell -type f 2>/dev/null | head -1)"
if [ -z "$HYPERFRAMES_BROWSER_PATH" ]; then
  echo "✗ no chrome-headless-shell under ${REAL_HOME}/.cache/hyperframes/chrome; stopping"
  exit 1
fi
export HYPERFRAMES_BROWSER_PATH

check_env() {
  local leak
  leak="$(env | grep -iE '^[^=]*(groq|eleven|cutline|promptstudio_dir|s2f_dir|s2f_assets_local|gemini)[^=]*=' | cut -d= -f1)"
  [ -z "$leak" ] || fail "still in the environment: ${leak}"
  [ ! -e "$HOME/.config/script2film/secrets.json" ] || fail "the temp HOME has .config/script2film/secrets.json"
  local d
  for d in "$S2F_WHISPER_CPP_MODEL" "$S2F_QWEN_TTS_DIR/.venv/bin/python" "$S2F_QWEN_TTS_MODELS" "$S2F_ASSETS/fonts" \
           "$S2F_ASSETS/sfx/manifest.json" "$HF_HOME" "$PLAYWRIGHT_BROWSERS_PATH" "$EP/doc.json" "$EP/refs"; do
    [ -e "$d" ] || fail "does not exist: ${d}" || return 1
  done
  echo "HOME=${HOME}"
  echo "HYPERFRAMES_BROWSER_PATH=${HYPERFRAMES_BROWSER_PATH}"
  echo "node $(node --version) ($(command -v node))"
  python3 -c "import pytest, opencc, PIL, numpy, fontTools, playwright; print('all python3 packages import (under the temp HOME)')"
}

# ---------------------------------------------------------------- steps
clone_overlay() {
  git clone -q "$SRC" "$REPO" || return 1
  git -C "$SRC" diff HEAD --binary > "$WORK/wip.patch" || return 1
  local n_patch n_new=0 f
  n_patch=$(git -C "$REPO" apply --numstat "$WORK/wip.patch" | wc -l | tr -d ' ')
  if [ -s "$WORK/wip.patch" ]; then
    git -C "$REPO" apply "$WORK/wip.patch" || return 1
  fi
  while IFS= read -r -d '' f; do
    mkdir -p "$REPO/$(dirname "$f")"
    cp -p "$SRC/$f" "$REPO/$f" || return 1
    n_new=$((n_new + 1))
  done < <(git -C "$SRC" ls-files --others --exclude-standard -z)
  echo "changes applied: ${n_patch} tracked files (wip.patch), ${n_new} untracked files"
  [ ! -e "$REPO/node_modules" ] || fail "the clone already has node_modules"
}

npm_ci() { (cd "$REPO" && npm ci --no-audit --no-fund); }

run_pytest() {
  (cd "$DOC" && python3 -m pytest -q tests -rs) 2>&1 | tee "$WORK/pytest.log"
  local rc=${PIPESTATUS[0]}
  [ "$rc" -eq 0 ] || return "$rc"
  local tail_line skipped n_skip_lines n_122
  tail_line="$(grep -E '[0-9]+ passed' "$WORK/pytest.log" | tail -1)"
  skipped="$(echo "$tail_line" | grep -oE '[0-9]+ skipped' | grep -oE '[0-9]+')"
  n_skip_lines=$(grep -c '^SKIPPED' "$WORK/pytest.log")
  n_122=$(grep '^SKIPPED' "$WORK/pytest.log" | grep -c 'test_lecture.py:122')
  echo "pytest result: ${tail_line}; SKIPPED lines ${n_skip_lines}, of them at test_lecture.py:122: ${n_122}"
  [ "${skipped:-0}" = 3 ] && [ "$n_skip_lines" = 3 ] && [ "$n_122" = 3 ] || fail "skips are not exactly 3 at test_lecture.py:122"
}

prep_p1() {
  mkdir -p "$P1" && cp "$EP/doc.json" "$P1/" && cp -R "$EP/refs" "$P1/" || return 1
  if [ -f "$EP/expected.json" ]; then cp "$EP/expected.json" "$P1/" || return 1; fi   # check_p1 reads it (s2f-3f D6)
  # The voice reference files must live inside the project: copy any absolute or outside path in and make it relative.
  python3 - "$P1/doc.json" "$EP" <<'PY'
import json, shutil, sys
from pathlib import Path
doc_path, ep = Path(sys.argv[1]), Path(sys.argv[2])
doc = json.loads(doc_path.read_text(encoding="utf-8"))
changed = False
for k in ("ref_wav", "ref_text"):
    v = doc["voice"][k]
    p = Path(v)
    src = p if p.is_absolute() else (ep / p).resolve()
    inside = not p.is_absolute() and src.is_relative_to(ep.resolve())
    print(f"voice.{k} = {v}: " + ("relative path inside the project, unchanged" if inside else "outside the project, copied into refs/ and made relative"))
    if not inside:
        (doc_path.parent / "refs").mkdir(exist_ok=True)
        shutil.copy2(src, doc_path.parent / "refs" / src.name)
        doc["voice"][k] = f"refs/{src.name}"
        changed = True
if changed:
    doc_path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
PY
}

tts()   { "$S2F_QWEN_TTS_DIR/.venv/bin/python" "$DOC/scripts/doc_tts.py" "$1/doc.json"; }
voice() { python3 "$DOC/scripts/doc_voice.py" "$1/doc.json"; }
align() { python3 "$DOC/scripts/doc_align.py" "$1/doc.json"; }
code()  { python3 "$DOC/scripts/doc_code.py" "$1/doc.json" --render; }
cut()   { python3 "$DOC/scripts/doc_cut.py" "$1/doc.json" "${@:2}"; }
sfx()   { python3 "$DOC/scripts/doc_sfx.py" "$1/doc.json" --report 2>&1 | tee "$WORK/sfx_report.log"; return "${PIPESTATUS[0]}"; }

check_p1() {
  local mp4="$P1/cut_$THEME/output.mp4"
  [ -f "$mp4" ] || fail "no ${mp4}" || return 1
  python3 - "$mp4" "$P1" <<'PY'
import json, subprocess, sys
from pathlib import Path
mp4, P = sys.argv[1], Path(sys.argv[2])
probe = lambda *a: subprocess.run(["ffprobe", "-v", "error", *a, mp4], capture_output=True, text=True, check=True).stdout.split()
dur = float(probe("-show_entries", "format=duration", "-of", "csv=p=0")[0])
beats = json.loads((P / "beats.json").read_text(encoding="utf-8"))
total = float(beats["total"])
audio = probe("-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0")
print(f"output.mp4 length {dur:.3f} s; beats.json total {total:.3f} s; difference {abs(dur - total):.3f} s; audio tracks {len(audio)}")
ok = abs(dur - total) <= 0.05 and len(audio) == 1
# the example's own expected.json (s2f-3f D6): a trial project given on the command line may not have one
if (P / "expected.json").is_file():
    want = json.loads((P / "expected.json").read_text(encoding="utf-8"))
    lines = len(json.loads((P / "doc.json").read_text(encoding="utf-8"))["lines"])
    lo, hi = want["seconds"]
    for text, good in [(f"beats {len(beats['beats'])} (expected.json wants {want['beats']})", len(beats["beats"]) == want["beats"]),
                       (f"lines {lines} (wants {want['lines']})", lines == want["lines"]),
                       (f"length {dur:.2f} s (wants {lo}–{hi})", lo <= dur <= hi)]:
        print(("✓ " if good else "✗ ") + text)
        ok = ok and good
else:
    print("no expected.json: skipping the beat count, line count and length range")
print("passed" if ok else "✗ failed")
sys.exit(0 if ok else 1)
PY
}

prep_p2() {
  mkdir -p "$P2" && cp "$P1/doc.json" "$P1/beats.json" "$P2/" && cp -R "$P1/refs" "$P1/voice.cleaned" "$P1/tts" "$P2/" || return 1
  mkdir -p "$P2/music"
  ffmpeg -v error -y -f lavfi -i sine=frequency=220:duration=30 "$P2/music/sine220.wav" || return 1
  python3 - "$P2/doc.json" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
doc = json.loads(p.read_text(encoding="utf-8"))
doc["sfx_on"] = True
doc["bgm"] = {"src": "music/sine220.wav"}
p.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
print('doc.json gets "sfx_on": true and "bgm": {"src": "music/sine220.wav"} (a 30 s 220 Hz sine wave)')
PY
}

check_p2() {
  local hits
  hits="$(grep -l '"pop"' "$P2/code_$THEME"/*.sfx.json 2>/dev/null)"
  [ -n "$hits" ] || fail "no *.sfx.json contains pop" || return 1
  echo "sound-effect marks with pop: $(echo "$hits" | xargs -n1 basename | tr '\n' ' ')"
  echo "pop lines in the report:"
  grep -E '\bpop\b' "$WORK/sfx_report.log"
  python3 - "$P2/sfx_plan.json" <<'PY'
import json, sys
plan = json.load(open(sys.argv[1]))
pops = [x for x in plan["kept"] if x["kind"] == "pop"]
files = sorted({x["file"] for x in pops if x["file"]})
print(f"sfx_plan.json: {len(pops)} pops kept, matched files {files or 'none'}; kinds without a sound {plan['missing_kinds']}")
sys.exit(0 if pops and all(x["file"] for x in pops) else 1)
PY
  [ -f "$P2/bgm/bgm.wav" ] || fail "no bgm/bgm.wav" || return 1
  echo "bgm/bgm.wav written"
  ls "$P2/cut_$THEME" >/dev/null || return 1
}

# s2f-1b T9：第二份稿的 Concat plan 與殼頁面的配樂標籤
check_plan_bgm() {
  local cut="$P2/cut_$THEME"
  [ -f "$cut/plan.json" ] || fail "no ${cut}/plan.json" || return 1
  echo "${cut}/plan.json exists"
  [ -f "$cut/index.html" ] || fail "no ${cut}/index.html" || return 1
  grep -q 'id="bgm"' "$cut/index.html" || fail "${cut}/index.html has no id=\"bgm\"" || return 1
  echo "${cut}/index.html has id=\"bgm\""
}

# s2f-1b T7：第二份稿（有配樂與 sfx_on）的保底成片響度，用夜跑的標準（tools/nightly/check.py）
check_loud() {
  local mp4="$P2/cut_$THEME/output.mp4"
  [ -f "$mp4" ] || fail "no ${mp4}" || return 1
  ffmpeg -hide_banner -nostats -i "$mp4" -af ebur128=peak=true -f null - > "$WORK/p2_ebur128.log" 2>&1 || return 1
  python3 - "$WORK/p2_ebur128.log" <<'PY2'
import re, sys
summary = open(sys.argv[1], encoding="utf-8", errors="replace").read().rsplit("Summary:", 1)[-1]
i = re.search(r"I:\s+(-?[\d.]+) LUFS", summary)
tp = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", summary)
if not i or not tp:
    print("✗ could not measure integrated loudness or peak (no I: or Peak: in the ebur128 summary)")
    sys.exit(1)
lufs, peak = float(i.group(1)), float(tp.group(1))
print(f"second output.mp4: integrated loudness {lufs:.1f} LUFS (target -14±0.8); peak {peak:.1f} dBTP (limit ≤ -1.0)")
ok = abs(lufs - (-14.0)) <= 0.8 and peak <= -1.0
print("passed" if ok else "✗ failed")
sys.exit(0 if ok else 1)
PY2
}

check_hf() {
  [ ! -e "$TMPHOME/.cache/huggingface" ] || fail ".cache/huggingface appeared under the temp HOME (a model was downloaded again)" || return 1
  echo "no .cache/huggingface under the temp HOME"
  echo "temp HOME contents: $(cd "$TMPHOME" && find . -maxdepth 2 | sort | tr '\n' ' ')"
}

# ---------------------------------------------------------------- examples/brewing from its premade files (s2f-3e)
# Third pass: the generated shot and the host come from examples/brewing/premade, so nothing is generated and no account
# is needed. It keeps the Chinese path, a `ve` beat, the host circle and the full-frame host under a machine check.
BREW="$REPO/examples/brewing"
HOST_SSIM_MIN=0.915   # B5 against refs/host_look.jpg, top 1920x720: right film 0.968, a code card there 0.863, black 0.491
                      # (measured 2026-11-16; the floor is halfway between the first two)

prep_p3() {
  mkdir -p "$P3" && cp "$BREW/doc.json" "$BREW/expected.json" "$P3/" && cp -R "$BREW/refs" "$P3/" && cp -R "$BREW/premade/." "$P3/"
}
lint_beats_p3() {
  python3 "$DOC/scripts/doc_lint.py" "$P3/doc.json" --beats "$P3/beats.json" | tee "$WORK/p3_lint.log"
  [ "${PIPESTATUS[0]}" -eq 0 ] || return 1
  grep -qx 'read_time: ok' "$WORK/p3_lint.log" || fail "no read_time: ok" || return 1
  grep -qx 'late_reveal: ok' "$WORK/p3_lint.log" || fail "no late_reveal: ok" || return 1
}
host_join_p3() { python3 "$DOC/scripts/doc_host.py" join "$P3/doc.json"; }
clipcheck_p3() { python3 "$REPO/tools/ve-runner/ve_clipcheck.py" "$P3/ve_flat" --strips; }
film_check_p3() { python3 "$REPO/tools/nightly/check.py" "$P3/doc.json" "$P3/cut_$THEME/output.mp4"; }
check_p3() {
  local mp4="$P3/cut_$THEME/output.mp4"
  [ -f "$mp4" ] || fail "no ${mp4}" || return 1
  python3 - "$P3" "$mp4" "$HOST_SSIM_MIN" <<'PY'
import json, re, subprocess, sys
from pathlib import Path
P, mp4, floor = Path(sys.argv[1]), sys.argv[2], float(sys.argv[3])
doc = json.loads((P / "doc.json").read_text(encoding="utf-8"))
beats = json.loads((P / "beats.json").read_text(encoding="utf-8"))["beats"]
want = json.loads((P / "expected.json").read_text(encoding="utf-8"))
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4],
                           capture_output=True, text=True, check=True).stdout.split()[0])
b1, b5 = beats[0], beats[-1]
t = b5["start"] + b5["duration"] / 2
r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{t:.2f}", "-i", mp4, "-i", str(P / "refs/host_look.jpg"),
                    "-frames:v", "1", "-lavfi", "[0]scale=1920:1080,crop=1920:720:0:0[a];[1]scale=1920:1080,crop=1920:720:0:0[b];[a][b]ssim",
                    "-f", "null", "-"], capture_output=True, text=True)
m = re.search(r"All:([0-9.]+)", r.stderr)
ssim = float(m.group(1)) if m else -1.0
lo, hi = want["seconds"]
checks = [
    (f"beats {len(beats)} (wants {want['beats']})", len(beats) == want["beats"]),
    (f"lines {len(doc['lines'])} (wants {want['lines']})", len(doc["lines"]) == want["lines"]),
    (f"length {dur:.2f} s (wants {lo}–{hi})", lo <= dur <= hi),
    (f"B1 source is {b1.get('source')} (wants ve)", b1.get("source") == "ve"),
    (f"last beat frame at {t:.2f} s vs the look image: similarity {ssim:.3f} (wants ≥ {floor})", ssim >= floor),
]
for text, ok in checks:
    print(("✓ " if ok else "✗ ") + text)
sys.exit(0 if all(ok for _, ok in checks) else 1)
PY
}
# Chinese voice step (s2f-3f D5). examples/coffee is in English and the brewing pass above starts from premade files at
# F3, so without this nothing here would run doc_tts.py and doc_voice.py on a Chinese script (conversion to Simplified
# before the model, the pronunciation table, picking takes in Chinese). Voice only: the premade host fits only the
# narration shipped with it, so this copy is not cut into a film.
P4="$WORK/proj4"
prep_p4() { mkdir -p "$P4" && cp "$BREW/doc.json" "$P4/" && cp -R "$BREW/refs" "$P4/"; }
voice_p4() { voice "$P4" 2>&1 | tee "$WORK/p4_voice.log"; return "${PIPESTATUS[0]}"; }
check_p4() {
  [ -f "$P4/tts/voice.wav" ] || fail "no ${P4}/tts/voice.wav" || return 1
  python3 - "$P4" <<'PY' || return 1
import json, sys
from pathlib import Path
P = Path(sys.argv[1])
doc = json.loads((P / "doc.json").read_text(encoding="utf-8"))
rows = json.loads((P / "tts/lines.json").read_text(encoding="utf-8"))
print(f"doc.json lang={doc['lang']}, {len(doc['lines'])} lines; tts/lines.json {len(rows)} rows")
sys.exit(0 if doc["lang"] == "zh" and len(rows) == len(doc["lines"]) else 1)
PY
  # The result line is printed, not judged: this script scores 0.69 on line 4 with a correct reading, because the
  # transcriber writes the spoken numbers as digits and 義式 as a homophone (the shipped premade take has the same score).
  grep 'below 0.85' "$WORK/p4_voice.log" || fail "doc_voice.py printed no result line" || return 1
}
zh_voice_pass() {
  step "Chinese voice: prepare (brewing script and reference voice, no premade files)" prep_p4
  step "Chinese voice: doc_tts.py" tts "$P4"
  step "Chinese voice: doc_voice.py" voice_p4
  step "Chinese voice: check result" check_p4
}

brewing_pass() {
  if [ ! -d "$BREW/premade" ]; then
    echo "brewing: no premade files (${BREW}/premade); skipped"
    return 0
  fi
  step "brewing: prepare (copy premade files)" prep_p3
  step "brewing: doc_lint.py" python3 "$DOC/scripts/doc_lint.py" "$P3/doc.json"
  step "brewing: doc_align.py" align "$P3"
  step "brewing: doc_lint.py --beats" lint_beats_p3
  step "brewing: doc_code.py --render" code "$P3"
  step "brewing: doc_host.py join" host_join_p3
  step "brewing: ve_clipcheck.py --strips" clipcheck_p3
  step "brewing: doc_cut.py --render" cut "$P3" --render
  step "brewing: check.py" film_check_p3
  step "brewing: check the film" check_p3
}

step "environment check" check_env
step "clone and apply working-tree changes" clone_overlay
step "npm ci" npm_ci
step "doc-mode pytest suite" run_pytest
step "prepare the first script" prep_p1
step "doc_tts.py" tts "$P1"
step "doc_voice.py" voice "$P1"
step "doc_align.py" align "$P1"
step "doc_code.py --render" code "$P1"
step "doc_cut.py --render" cut "$P1" --render
step "check output.mp4" check_p1
step "prepare the second script (sfx_on + bgm)" prep_p2
step "second doc_code.py --render" code "$P2"
step "second doc_sfx.py --report" sfx "$P2"
step "second doc_cut.py --render" cut "$P2" --render
step "check sound effects and music" check_p2
step "check the second plan.json and the page music tag" check_plan_bgm
step "check the second film loudness" check_loud
brewing_pass
zh_voice_pass
step "check no model was downloaded again" check_hf
summary
echo "✓ all passed"
