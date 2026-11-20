"""角色台詞直接由 Qwen3-TTS VoiceDesign 唸（同一角色固定 instruct；每句出 N 個 seed 候選，由下游用 ASR 挑最好的）。

已被 clone_lines.py 取代：VoiceDesign 每句重新設計聲音，同一角色前後會變成不同人（實測句間相似度 0.57、0.33）。
這支留作快速試聽單句用。

用法（先 source env.sh）：$S2F_QWEN_TTS_DIR/.venv/bin/python tools/tts/speak_lines.py <cast.json> <輸出資料夾> [--n 3]
輸出：<輸出>/<句號>_<seed>.wav（48kHz）；只處理 cast.voices 裡有 instruct 的角色
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/tts"))
import qwen_python; qwen_python.ensure()   # 系統的 python3 也能跑：自己轉交給配音環境的 Python
import argparse, json, time
from pathlib import Path
import numpy as np, soundfile as sf, torch, librosa
from qwen_tts import Qwen3TTSModel
from opencc import OpenCC

from qwen_paths import model
# 送進模型前一律轉簡體（只逐字轉，不換詞）：實測同一指令，繁體輸入唸成方言腔，簡體輸入才正常；字幕與畫面照樣用繁體
TO_SIMP = OpenCC("t2s").convert

ap = argparse.ArgumentParser(); ap.add_argument("cast", type=Path); ap.add_argument("out", type=Path); ap.add_argument("--n", type=int, default=3)
a = ap.parse_args()
MODEL = model("Qwen3-TTS-12Hz-1.7B-VoiceDesign")
cast = json.loads(a.cast.read_text(encoding="utf-8")); a.out.mkdir(parents=True, exist_ok=True)
device = "mps" if torch.backends.mps.is_available() else "cpu"
model = Qwen3TTSModel.from_pretrained(str(MODEL), device_map=device, dtype=torch.float32)
for n, line in enumerate(cast["lines"], 1):
    v = cast["voices"].get(line["speaker"], {})
    if not v.get("instruct"):
        continue
    base = int(v.get("seed", 7))
    for k in range(a.n):
        torch.manual_seed(base + k); t0 = time.monotonic()
        wavs, sr = model.generate_voice_design(text=TO_SIMP(line["text"]), language="Chinese", instruct=TO_SIMP(v["instruct"]))
        w = librosa.resample(np.asarray(wavs[0], dtype=np.float32), orig_sr=sr, target_sr=48000)
        sf.write(a.out / f"{n:02d}_{base + k}.wav", w, 48000, subtype="PCM_16")
        print(f"[{n}] {line['speaker']} seed {base + k}: {len(w) / 48000:.2f}s ({time.monotonic() - t0:.1f}s) | {line['text'][:20]}", flush=True)
