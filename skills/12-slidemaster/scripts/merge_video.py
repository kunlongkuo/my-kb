import os
import argparse
import subprocess
import glob
import re

def get_sorted_files(directory, extensions):
    unique_files = set()
    for ext in extensions:
        ext_lower = ext.lower()
        for f in glob.glob(os.path.join(directory, "*")):
            if f.lower().endswith(ext_lower):
                unique_files.add(f)
    
    files = list(unique_files)
    
    # 數字自然排序，如 slide1, slide2, slide10
    def natural_sort_key(s):
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]
    
    files.sort(key=natural_sort_key)
    return files

def find_ffmpeg():
    # 1. 檢查腳本上三層目錄下的 bin/ffmpeg 或 bin/ffmpeg.exe
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
    local_ffmpeg = os.path.join(project_root, "bin", "ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg
    # 2. 如果不存在，使用系統 path 中的 ffmpeg
    return "ffmpeg"

def run_command(cmd):
    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"Error executing command: {result.stderr}")
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description="SlideMaster: Merge slides and audios into a video.")
    parser.add_argument("--slides-dir", required=True, help="Directory containing slide images")
    parser.add_argument("--audio-dir", required=True, help="Directory containing audios")
    parser.add_argument("--output", default="output.mp4", help="Output path of the final video")
    parser.add_argument("--temp-dir", default="temp_workdir", help="Temporary working directory")
    args = parser.parse_args()

    slides = get_sorted_files(args.slides_dir, [".png", ".jpg", ".jpeg"])
    audios = get_sorted_files(args.audio_dir, [".mp3", ".wav"])

    if not slides:
        print("Error: No slide images found.")
        return
    if not audios:
        print("Error: No audio files found.")
        return

    if len(slides) != len(audios):
        print(f"Warning: Number of slides ({len(slides)}) and audios ({len(audios)}) do not match.")
        limit = min(len(slides), len(audios))
        slides = slides[:limit]
        audios = audios[:limit]
        print(f"Only processing the first {limit} pairs.")

    os.makedirs(args.temp_dir, exist_ok=True)
    temp_videos = []
    ffmpeg_path = find_ffmpeg()

    try:
        # Step 1: Merge each slide with its corresponding audio
        for i, (slide, audio) in enumerate(zip(slides, audios)):
            temp_video_path = os.path.join(args.temp_dir, f"segment_{i:04d}.mp4")
            # FFmpeg command to merge 1 image and 1 audio
            cmd = [
                ffmpeg_path, "-y",
                "-loop", "1", "-i", slide,
                "-i", audio,
                "-c:v", "libx264",
                "-tune", "stillimage",
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-shortest",
                temp_video_path
            ]
            if run_command(cmd):
                temp_videos.append(temp_video_path)
            else:
                print(f"Failed to generate video segment for index {i}")
                return

        if not temp_videos:
            print("Error: No temporary videos generated.")
            return

        # Step 2: Create concat list file
        list_file_path = os.path.join(args.temp_dir, "file_list.txt")
        with open(list_file_path, "w", encoding="utf-8") as f:
            for video in temp_videos:
                # ffmpeg requires path to be forward slash or escaped
                safe_path = os.path.abspath(video).replace("\\", "/")
                f.write(f"file '{safe_path}'\n")

        # Step 3: Concat all segments into the final video
        concat_cmd = [
            ffmpeg_path, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file_path,
            "-c", "copy",
            args.output
        ]
        if run_command(concat_cmd):
            print(f"Success! Final video generated at: {args.output}")
        else:
            print("Failed to concatenate video segments.")

    finally:
        # Cleanup
        print("Cleaning up temporary segments...")
        for video in temp_videos:
            if os.path.exists(video):
                try:
                    os.remove(video)
                except Exception as e:
                    print(f"Failed to delete {video}: {e}")
        
        list_file_path = os.path.join(args.temp_dir, "file_list.txt")
        if os.path.exists(list_file_path):
            try:
                os.remove(list_file_path)
            except Exception as e:
                print(f"Failed to delete {list_file_path}: {e}")
        
        try:
            os.rmdir(args.temp_dir)
        except Exception as e:
            pass

if __name__ == "__main__":
    main()
