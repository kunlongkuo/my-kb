#!/usr/bin/env bash
# Sets up the two local speech environments the core flow needs, then writes their paths to the config file:
#   - Qwen3-TTS (narration): the official code, its own Python 3.11 environment, and the Base model (about 4.2 GB)
#   - whisper.cpp (transcription and word timing): the whisper-cli program (macOS: Homebrew) and the turbo model
#     ggml-large-v3-turbo.bin (about 1.6 GB)
# doctor.py only checks; this script is the one that installs. It is safe to run again: finished parts are skipped.
#
#   bash tools/doctor/setup_voice.sh [<folder>] [--design]
#
# <folder>   where to put everything; default ~/s2f-voice
# --design   also download the VoiceDesign model (about 4.2 GB more), needed only to design a new synthetic voice
#            with tools/tts/design_voices.py. The example films ship their reference voices and do not need it.
#
# Measured on a MacBook Pro M3 Max, 2026-11-17: about 20 minutes in all, most of it installing the Qwen3-TTS packages
# (15 minutes); about 6 GB on disk. Needs python3.11 and git (brew install python@3.11).
# Qwen3-TTS is pinned to the commit this project was tested with; set S2F_QWEN_REF to another commit or branch to change it.
set -u -o pipefail

QWEN_REPO="https://github.com/QwenLM/Qwen3-TTS.git"
QWEN_REF="${S2F_QWEN_REF:-022e286}"
BASE_MODEL="Qwen3-TTS-12Hz-1.7B-Base"
DESIGN_MODEL="Qwen3-TTS-12Hz-1.7B-VoiceDesign"
WHISPER_MODEL="ggml-large-v3-turbo.bin"

DEST="$HOME/s2f-voice"; DESIGN=0
for a in "$@"; do
  case "$a" in
    --design) DESIGN=1 ;;
    -h|--help) sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) echo "✗ unknown option: $a" >&2; exit 64 ;;
    *) DEST="$a" ;;
  esac
done
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PY="$(command -v python3.11 || true)"
[ -n "$PY" ] || { echo "✗ python3.11 not found: brew install python@3.11" >&2; exit 1; }
command -v git >/dev/null || { echo "✗ git not found: xcode-select --install" >&2; exit 1; }

mkdir -p "$DEST" && cd "$DEST" || exit 1
DEST="$(pwd)"
echo "folder: $DEST"

step() { echo; echo "== $1"; }
fail() { echo "✗ $1" >&2; exit 1; }

step "1/5 Qwen3-TTS code ($QWEN_REF)"
if [ ! -d qwen3-tts/src/.git ]; then
  git clone -q "$QWEN_REPO" qwen3-tts/src || fail "git clone failed (network?)"
fi
git -C qwen3-tts/src checkout -q "$QWEN_REF" || fail "cannot check out $QWEN_REF in qwen3-tts/src"

step "2/5 Qwen3-TTS Python environment (the slow part: about 15 minutes, it is not stuck)"
[ -x qwen3-tts/.venv/bin/python ] || "$PY" -m venv qwen3-tts/.venv || fail "cannot create qwen3-tts/.venv"
if ! qwen3-tts/.venv/bin/python -c "import qwen_tts" 2>/dev/null; then
  qwen3-tts/.venv/bin/python -m pip install -q -e qwen3-tts/src || fail "installing the Qwen3-TTS packages failed; run this script again to retry"
fi

step "3/5 whisper.cpp (whisper-cli)"
if ! command -v whisper-cli >/dev/null && [ -z "${S2F_WHISPER_CLI:-}" ]; then
  if command -v brew >/dev/null; then
    brew install whisper.cpp || fail "brew install whisper.cpp failed; run this script again to retry"
  else
    fail "whisper-cli not found: build it from github.com/ggml-org/whisper.cpp and put it on PATH (or set S2F_WHISPER_CLI), then run this script again"
  fi
fi

fetch() {   # fetch <model name>: download into _models/<name> unless its weights are already there
  if [ -s "_models/$1/model.safetensors" ] && [ -s "_models/$1/speech_tokenizer/model.safetensors" ]; then
    echo "already here: _models/$1"; return 0
  fi
  qwen3-tts/.venv/bin/hf download "Qwen/$1" --local-dir "_models/$1" > "_models_$1.log" 2>&1 \
    || fail "downloading Qwen/$1 failed (see $DEST/_models_$1.log); run this script again to resume"
  rm -f "_models_$1.log"
}
step "4/5 voice model $BASE_MODEL (about 4.2 GB) and transcription model $WHISPER_MODEL (about 1.6 GB)"
mkdir -p _models && fetch "$BASE_MODEL"
if [ "$DESIGN" = 1 ]; then
  echo "also: $DESIGN_MODEL (about 4.2 GB)"; fetch "$DESIGN_MODEL"
fi
if [ -s "_models/whisper-cpp/$WHISPER_MODEL" ]; then
  echo "already here: _models/whisper-cpp/$WHISPER_MODEL"
else
  qwen3-tts/.venv/bin/hf download ggerganov/whisper.cpp "$WHISPER_MODEL" --local-dir _models/whisper-cpp > _models_whisper.log 2>&1 \
    || fail "downloading $WHISPER_MODEL failed (see $DEST/_models_whisper.log); run this script again to resume"
  rm -f _models_whisper.log
fi

step "5/5 config file"
"$PY" - "$DEST" <<'PYEOF' || fail "cannot write the config file"
import json, os, sys
from pathlib import Path
dest = Path(sys.argv[1])
v = os.environ.get("S2F_CONFIG")
path = Path(v).expanduser() if v and v != "none" else Path.home() / ".config/script2film/config.json"
want = {"S2F_QWEN_TTS_DIR": str(dest / "qwen3-tts"), "S2F_WHISPER_CPP_MODEL": str(dest / "_models/whisper-cpp/ggml-large-v3-turbo.bin")}
cfg = json.loads(path.read_text(encoding="utf-8")) if path.exists() and path.read_text(encoding="utf-8").strip() else {}
for k, val in want.items():
    if cfg.get(k) not in (None, val):
        print(f"kept {k} = {cfg[k]} (already set; change it by hand to use {val})")
    else:
        cfg[k] = val
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"wrote {path}")
PYEOF

echo
echo "✓ done. Next: python3 $HERE/doctor.py"
