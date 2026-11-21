import json
import os
import re
import subprocess
import wave
from pathlib import Path

PROJECT = Path("i:/Mark/my-kb/skills/script2film/projects/forklift")
DOC_PATH = PROJECT / "doc.json"
VOICE = "zh-TW-YunJheNeural"
SR = 48000

def get_wav_duration(wav_path):
    with wave.open(str(wav_path), "rb") as wf:
        return wf.getnframes() / wf.getframerate()

def main():
    doc = json.loads(DOC_PATH.read_text(encoding="utf-8"))
    tts_dir = PROJECT / "tts"
    tts_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = PROJECT / "temp_tts"
    temp_dir.mkdir(parents=True, exist_ok=True)

    lines_data = []
    current_time = 0.08
    gap = doc.get("gaps", {}).get("default", 0.5)
    wav_files = []

    print(f"🎙️ 合成 {len(doc['lines'])} 句旁白...")

    for i, line_obj in enumerate(doc["lines"], 1):
        text = line_obj["text"]
        mp3_file = temp_dir / f"line_{i}.mp3"
        vtt_file = temp_dir / f"line_{i}.vtt"
        wav_file = temp_dir / f"line_{i}.wav"

        # 調用 edge-tts 命令列工具
        cmd = [
            "edge-tts",
            "--voice", VOICE,
            "--text", text,
            "--write-media", str(mp3_file),
            "--write-subtitles", str(vtt_file)
        ]
        subprocess.run(cmd, check=True)

        # 轉成 48kHz mono 16-bit WAV
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", str(mp3_file),
            "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le",
            str(wav_file)
        ]
        subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        dur = get_wav_duration(wav_file)
        start_time = round(current_time, 3)
        end_time = round(current_time + dur, 3)

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
        print(f"  [{i}/{len(doc['lines'])}] {text[:16]}... ({dur:.2f}s)")
        current_time = end_time + gap

    # 串接音訊
    concat_list = temp_dir / "concat.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for idx, wf in enumerate(wav_files):
            f.write(f"file '{wf.name}'\n")
            if idx < len(wav_files) - 1:
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

    # 寫入 lines.json
    (tts_dir / "lines.json").write_text(json.dumps(lines_data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"✅ 成功產出 tts/voice.wav 與 tts/lines.json！總長: {current_time:.2f} 秒")

    # 清理
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    main()
