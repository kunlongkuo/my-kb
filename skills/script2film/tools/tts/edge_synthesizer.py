import asyncio
import json
import math
import os
import re
import subprocess
import wave
from pathlib import Path
import edge_tts

PROJECT = Path("i:/Mark/my-kb/skills/script2film/projects/forklift")
DOC_PATH = PROJECT / "doc.json"
VOICE = "zh-TW-YunJheNeural"  # 台灣國語沉穩男聲，VOX 紀錄片首選
RATE = "+0%"
VOLUME = "+0%"
SR = 48000

async def synth_line(text, mp3_path):
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, volume=VOLUME)
    submaker = edge_tts.SubMaker()
    with open(mp3_path, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)
    return submaker

def mp3_to_wav(mp3_path, wav_path):
    cmd = [
        "ffmpeg", "-y", "-i", str(mp3_path),
        "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le",
        str(wav_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def get_wav_duration(wav_path):
    with wave.open(str(wav_path), "rb") as wf:
        return wf.getnframes() / wf.getframerate()

async def main():
    doc = json.loads(DOC_PATH.read_text(encoding="utf-8"))
    tts_dir = PROJECT / "tts"
    tts_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = PROJECT / "temp_tts"
    temp_dir.mkdir(parents=True, exist_ok=True)

    lines_data = []
    current_time = 0.08  # 起始 padding
    gap = doc.get("gaps", {}).get("default", 0.5)

    all_word_timings = []
    wav_files = []

    print("🎙️ 開始使用 Edge-TTS 合成高品質台灣繁中旁白 (zh-TW-YunJheNeural)...")

    for i, line_obj in enumerate(doc["lines"], 1):
        text = line_obj["text"]
        mp3_file = temp_dir / f"line_{i}.mp3"
        wav_file = temp_dir / f"line_{i}.wav"

        submaker = await synth_line(text, mp3_file)
        mp3_to_wav(mp3_file, wav_file)
        dur = get_wav_duration(wav_file)

        start_time = round(current_time, 3)
        end_time = round(current_time + dur, 3)

        # 整理單詞時間戳記（偏移加上 current_time 及 lead 0.45s）
        lead_offset = 0.45
        for cue in submaker.cues:
            # cue: start, end in timedelta
            w_start = round(cue.start.total_seconds() + start_time + lead_offset, 3)
            w_end = round(cue.end.total_seconds() + start_time + lead_offset, 3)
            all_word_timings.append({
                "word": cue.content.strip(),
                "start": w_start,
                "end": w_end
            })

        lines_data.append({
            "n": i,
            "speaker": doc.get("speaker", "旁白"),
            "text": text,
            "start": start_time,
            "end": end_time,
            "pick": f"line_{i}.wav",
            "score": 1.0,
            "heard": text,
            "pauses": [],
            "atempo": None
        })
        wav_files.append(wav_file)
        print(f"  Line {i}: {text[:15]}... ({dur:.2f}s, start: {start_time:.2f}s, end: {end_time:.2f}s)")
        current_time = end_time + gap

    # 串接所有 wav 成 voice.wav
    concat_list = temp_dir / "concat.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for idx, wf in enumerate(wav_files):
            f.write(f"file '{wf.name}'\n")
            if idx < len(wav_files) - 1:
                # 建立安靜 gap
                gap_wav = temp_dir / f"gap_{idx}.wav"
                subprocess.run([
                    "ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=mono",
                    "-t", str(gap), "-c:a", "pcm_s16le", str(gap_wav)
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                f.write(f"file '{gap_wav.name}'\n")

    out_voice_wav = tts_dir / "voice.wav"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c:a", "pcm_s16le", str(out_voice_wav)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"✅ voice.wav 輸出完成: {out_voice_wav}")

    # 寫入 lines.json
    (tts_dir / "lines.json").write_text(json.dumps(lines_data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"✅ lines.json 寫入完成")

    # 產生 voice.cleaned/audio.m4a (前面加 0.45s 靜音)
    cleaned_dir = PROJECT / "voice.cleaned"
    aligned_dir = cleaned_dir / "aligned"
    aligned_dir.mkdir(parents=True, exist_ok=True)

    audio_m4a = cleaned_dir / "audio.m4a"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=mono", "-t", "0.45",
        "-i", str(out_voice_wav),
        "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1[out]",
        "-map", "[out]", "-c:a", "aac", "-b:a", "192k", str(audio_m4a)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"✅ voice.cleaned/audio.m4a 輸出完成")

    # 寫入 aligned/audio.words.json
    words_json_path = aligned_dir / "audio.words.json"
    words_json_path.write_text(json.dumps({
        "words": all_word_timings,
        "source": "edge-tts zh-TW-YunJheNeural"
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"✅ aligned/audio.words.json 寫入完成 (共 {len(all_word_timings)} 個時間標記)")

    # 清理 temp_tts
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    asyncio.run(main())
