"""角色一致性：每個角色只用 VoiceDesign 設計一次參考音（design_voices.py），之後每句台詞都用 Base 模型照那段參考音克隆。

為什麼：VoiceDesign 每句重新設計，同一段描述每次都是不同的人。實測一個角色 4 句之間 ECAPA 相似度平均 0.57、
另一個角色 3 句只有 0.33（同一個聲音約 0.89）。這是 Qwen3-TTS README 建議的做法。

用法（先 source env.sh）：$S2F_QWEN_TTS_DIR/.venv/bin/python tools/tts/clone_lines.py <cast.json> <參考音資料夾> <輸出資料夾> [--n 3]
參考音資料夾：design_voices.py 的輸出（<角色>.wav＋<角色>.txt）
輸出：<輸出>/<句號>_<seed>.wav（48 kHz）；cast.lines 裡每個有參考音的角色都處理
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
# 送進模型前一律轉簡體（只逐字轉）：繁體輸入會唸成方言腔
TO_SIMP = OpenCC("t2s").convert

ap = argparse.ArgumentParser(); ap.add_argument("cast", type=Path); ap.add_argument("refs", type=Path); ap.add_argument("out", type=Path); ap.add_argument("--n", type=int, default=3)
a = ap.parse_args()
MODEL = model("Qwen3-TTS-12Hz-1.7B-Base")
cast = json.loads(a.cast.read_text(encoding="utf-8")); a.out.mkdir(parents=True, exist_ok=True)
device = "mps" if torch.backends.mps.is_available() else "cpu"
model = Qwen3TTSModel.from_pretrained(str(MODEL), device_map=device, dtype=torch.float32)
prompts = {}
for n, line in enumerate(cast["lines"], 1):
    spk = line["speaker"]; ref = a.refs / f"{spk}.wav"
    if not ref.exists():
        continue
    if spk not in prompts:
        prompts[spk] = model.create_voice_clone_prompt(ref_audio=str(ref), ref_text=TO_SIMP((a.refs / f"{spk}.txt").read_text(encoding="utf-8").strip()))
    base = int(cast["voices"].get(spk, {}).get("seed", 7))
    for k in range(a.n):
        torch.manual_seed(base + k); t0 = time.monotonic()
        wavs, sr = model.generate_voice_clone(text=TO_SIMP(line["text"]), language="Chinese", voice_clone_prompt=prompts[spk])
        w = librosa.resample(np.asarray(wavs[0], dtype=np.float32), orig_sr=sr, target_sr=48000)
        sf.write(a.out / f"{n:02d}_{base + k}.wav", w, 48000, subtype="PCM_16")
        print(f"[{n}] {spk} seed {base + k}: {len(w) / 48000:.2f}s ({time.monotonic() - t0:.1f}s) | {line['text'][:20]}", flush=True)
