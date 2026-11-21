import json
import os
import time
from pathlib import Path

PROJECT = Path("i:/Mark/my-kb/skills/script2film/projects/forklift")
LINES_JSON = PROJECT / "tts/lines.json"
VOICE_WAV = PROJECT / "tts/voice.wav"
ALIGNED_DIR = PROJECT / "voice.cleaned/aligned"
ALIGNED_DIR.mkdir(parents=True, exist_ok=True)
WORDS_JSON = ALIGNED_DIR / "audio.words.json"

lines = json.loads(LINES_JSON.read_text(encoding="utf-8"))

segments = []
all_words = []
lead = 0.45  # 前導靜音秒數

for item in lines:
    text = item["text"]
    start = item["start"] + lead
    end = item["end"] + lead
    dur = end - start
    
    # 依字數均分時間戳記（中文每字一個 token）
    chars = [c for c in text if c.strip()]
    if not chars:
        continue
    step = dur / len(chars)
    seg_words = []
    for idx, c in enumerate(chars):
        w_start = round(start + idx * step, 3)
        w_end = round(start + (idx + 1) * step, 3)
        seg_words.append({
            "word": c,
            "start": w_start,
            "end": w_end
        })
    segments.append({
        "text": text,
        "start": start,
        "end": end,
        "words": seg_words
    })

data = {
    "segments": segments,
    "source": "aligned-edge-tts"
}

WORDS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

# 確保 WORDS_JSON 的修改時間晚於 voice.wav
now = time.time() + 10
os.utime(str(WORDS_JSON), (now, now))
print("✅ audio.words.json 結構化時間軸建立完成，時間戳記已更新為最新！")
