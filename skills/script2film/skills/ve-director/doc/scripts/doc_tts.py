"""Narration candidates with Qwen3-TTS voice cloning: N seeds per line, the picker (doc_voice.py) chooses one.

  python3 doc_tts.py <project>/doc.json [--script-approved] [--lines 3 5] [--n 3] [--force]
Voices only a script the user has approved (doc_approval.py): --script-approved after the user has seen the narration and
the beat table and said yes to this script (recorded in <project>/script_approval.json; the same narration needs no flag
again, a changed line needs a new approval), or an unchanged bundled example. Otherwise it stops before loading the voice
model, makes no audio, and exits 4.
Runs under any python3: when qwen_tts is not importable it re-runs itself with $S2F_QWEN_TTS_DIR/.venv/bin/python
(tools/tts/qwen_python.py). Calling that Python directly works as before.
doc.json: lang ("zh" | "en"), voice.ref_wav / voice.ref_text (paths relative to the project), voice.seed, lines[].text (or .tts).
A dialogue line: lines[].speaker names an entry of "voices" ({"<speaker>": {"ref_wav", "ref_text", "seed"}}), which is
cloned instead of "voice" for that line (doc_common.voice_of); lines without "speaker" use "voice".
Model: $S2F_QWEN_TTS_MODELS/Qwen3-TTS-12Hz-1.7B-Base (default: $S2F_QWEN_TTS_DIR/../_models; the old names without S2F_ also
work, doc_common.qwen_models_dir).
Output: <project>/tts_lines/<key>_<seed>.wav (48 kHz); key = doc_common.line_key (hash of spoken text + voice).
Takes that already exist are kept, so after editing the script (and approving it again) a rerun synthesizes only the changed lines;
--force makes new takes anyway.
Chinese input is converted to Simplified character by character first: Traditional input is read with a regional
accent by this model (tested 2026-10-08); subtitles keep the original text.
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[4] / "tools/config"))
import s2f_config; s2f_config.load()
import argparse, sys, time
from pathlib import Path

import doc_approval
from doc_common import load

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
                             epilog=f"Exit code {doc_approval.EXIT_NOT_APPROVED}: the script has not been approved by the user; nothing was voiced.")
ap.add_argument("doc", type=Path)
ap.add_argument(doc_approval.FLAG, dest="approved", action="store_true",
                help="the user has seen the narration and the beat table and said yes to this script; recorded, so the same "
                     "narration needs no flag again. Never pass it for the user")
ap.add_argument("--lines", type=int, nargs="*", help="only these line numbers (1-based)")
ap.add_argument("--n", type=int, default=3)
ap.add_argument("--force", action="store_true", help="synthesize again even when the take exists")
a = ap.parse_args()
doc, P = load(a.doc)
ok, why = doc_approval.check(doc, P, a.approved)   # 配音前先問：使用者核可過這份稿嗎（在載入配音模型之前）
if not ok:
    print(doc_approval.not_approved_message(a.doc), file=sys.stderr)
    sys.exit(doc_approval.EXIT_NOT_APPROVED)
print(f"script approved: {why}", flush=True)

_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[4] / "tools/tts"))
import qwen_python; qwen_python.ensure()   # 系統的 python3 也能跑：自己轉交給配音環境的 Python

import shutil
if not shutil.which("sox"):   # the voice model's package looks for sox on import and the shell prints an error line
    print("(if \"sox: command not found\" follows, ignore it: the voice step does not use sox and the takes are still written)", flush=True)
import librosa, numpy as np, soundfile as sf, torch
from qwen_tts import Qwen3TTSModel

from doc_common import lexicon, line_key, qwen_models_dir, speaker_of, spoken_text, voice_of

lang = {"zh": "Chinese", "en": "English"}[doc["lang"]]
conv = (lambda s: s)
if doc["lang"] == "zh":
    from opencc import OpenCC
    conv = OpenCC("t2s").convert
models = qwen_models_dir()
model = Qwen3TTSModel.from_pretrained(str(models / "Qwen3-TTS-12Hz-1.7B-Base"),
                                      device_map="mps" if torch.backends.mps.is_available() else "cpu", dtype=torch.float32)
prompts = {}   # one clone prompt per reference voice


def prompt_for(v):
    ref = (v["ref_wav"], v["ref_text"])
    if ref not in prompts:
        prompts[ref] = model.create_voice_clone_prompt(ref_audio=str(P / v["ref_wav"]),
                                                       ref_text=conv((P / v["ref_text"]).read_text(encoding="utf-8").strip()))
    return prompts[ref]


out = P / "tts_lines"; out.mkdir(exist_ok=True)
for n, line in enumerate(doc["lines"], 1):
    if a.lines and n not in a.lines:
        continue
    v = voice_of(doc, line)
    prompt, base = prompt_for(v), int(v.get("seed", 11))
    key = line_key(doc, P, line)
    if (swapped := lexicon.changes(line.get("tts") or line["text"], doc["lang"])):
        print(f"[{n}] lexicon: " + ", ".join(f"{x}→{y}" for x, y in swapped), flush=True)
    for k in range(a.n):
        dst = out / f"{key}_{base + k}.wav"
        if dst.exists() and not a.force:
            print(f"[{n}] seed {base + k}: kept {dst.name}", flush=True)
            continue
        torch.manual_seed(base + k); t0 = time.monotonic()
        wavs, sr = model.generate_voice_clone(text=conv(spoken_text(doc, line)), language=lang, voice_clone_prompt=prompt)
        w = librosa.resample(np.asarray(wavs[0], dtype=np.float32), orig_sr=sr, target_sr=48000)
        sf.write(dst, w, 48000, subtype="PCM_16")
        print(f"[{n}] {speaker_of(doc, line)} seed {base + k}: {len(w) / 48000:.2f}s ({time.monotonic() - t0:.1f}s) {line['text'][:40]}", flush=True)
