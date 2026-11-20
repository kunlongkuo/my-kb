"""用 Qwen3-TTS VoiceDesign 依文字描述「設計」角色音色，每個角色只設計一次，輸出一段參考音給 clone_lines.py 克隆。

為什麼每個角色只設計一次：VoiceDesign 每次呼叫都會重新設計聲音，同一段描述每句都是不同的人；
所以流程是「設計一次參考音 → Base 模型照它克隆每句」（Qwen3-TTS README 建議的做法）。

用法（先 source env.sh）：
  $S2F_QWEN_TTS_DIR/.venv/bin/python tools/tts/design_voices.py cast.json <輸出資料夾>/
cast.json：{"voices": {"<角色>": {"instruct": "...", "ref_text": "...", "seed": 7, "lang": "zh"}}}
"lang"：這個角色說的語言，"zh"（不寫就是它）或 "en"；英文的描述與參考句都用英文寫
輸出：<輸出資料夾>/<角色>.wav ＋ <角色>.txt（ref_text，克隆時要一起給）
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/tts"))
import qwen_python; qwen_python.ensure()   # 系統的 python3 也能跑：自己轉交給配音環境的 Python
import json, sys, time
from pathlib import Path
import torch, soundfile as sf
from qwen_tts import Qwen3TTSModel
from opencc import OpenCC

from qwen_paths import model, voice_language
# 送進模型前一律轉簡體（只逐字轉，不換詞）：實測同一指令，繁體輸入唸成方言腔，簡體輸入才正常；字幕與畫面照樣用繁體
TO_SIMP = OpenCC("t2s").convert
USAGE = """Design each character's voice once from a text description (Qwen3-TTS VoiceDesign) and write a reference clip
for clone_lines.py to clone.

Why once per character: VoiceDesign designs a new voice on every call, so the same description gives a different person
on every line; the flow is "design a reference clip once → the Base model clones every line from it" (what the
Qwen3-TTS README recommends).

Usage (source env.sh first):
  $S2F_QWEN_TTS_DIR/.venv/bin/python tools/tts/design_voices.py cast.json <output folder>/
cast.json: {"voices": {"<character>": {"instruct": "...", "ref_text": "...", "seed": 7, "lang": "zh"}}}
"lang": the language this character speaks, "zh" (the default) or "en"; for English write the description and the reference line in English
Output: <output folder>/<character>.wav + <character>.txt (ref_text, to be given together when cloning)"""

if len(sys.argv) != 3 or sys.argv[1] in ("-h", "--help"):   # no argparse here: print the usage instead of a traceback
    print(USAGE)
    sys.exit(0 if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help") else 2)
MODEL = model("Qwen3-TTS-12Hz-1.7B-VoiceDesign")
cast = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
device = "mps" if torch.backends.mps.is_available() else "cpu"
t0 = time.monotonic()
model = Qwen3TTSModel.from_pretrained(str(MODEL), device_map=device, dtype=torch.float32)
print(f"loaded in {time.monotonic() - t0:.1f}s | {device}", flush=True)
for name, v in cast["voices"].items():
    if not v.get("instruct"):
        continue
    torch.manual_seed(int(v.get("seed", 7)))
    t1 = time.monotonic()
    language, simp = voice_language(v.get("lang"))
    conv = TO_SIMP if simp else (lambda s: s)
    wavs, sr = model.generate_voice_design(text=conv(v["ref_text"]), language=language, instruct=conv(v["instruct"]))
    sf.write(out / f"{name}.wav", wavs[0], sr)
    (out / f"{name}.txt").write_text(v["ref_text"], encoding="utf-8")
    print(f"{name}: {len(wavs[0]) / sr:.2f}s ({time.monotonic() - t1:.1f}s)", flush=True)
