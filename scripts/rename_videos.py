import os
import re
import sys
import json
import time
import argparse
from dotenv import load_dotenv
from google import genai

# Load configuration
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY is not set in .env")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

TARGET_DIR = r"i:\Mark\知識\繩結"
MAP_FILE = os.path.join(os.path.dirname(__file__), "rename_map.json")

def get_all_video_files():
    """Return a list of all .mp4 files in TARGET_DIR."""
    if not os.path.exists(TARGET_DIR):
        print(f"Error: Target directory does not exist: {TARGET_DIR}")
        return []
    files = os.listdir(TARGET_DIR)
    return [f for f in files if f.lower().endswith('.mp4')]


def sanitize_filename(name):
    """Sanitize the proposed filename for Windows OS compatibility."""
    # Remove quotes, brackets, and invalid Windows characters \ / : * ? " < > |
    name = re.sub(r'[\'\"\[\]\{\}\(\)\\/\:\*\?\"\<\>\|]', '', name)
    name = name.strip()
    # Remove words like "繩結", "教學", "檔名" if they are just fillers
    # But keep them if they are part of a specific term like "稱人結"
    # We will let the LLM handle the core naming, and just do minimal cleanup here
    name = re.sub(r'^(檔名：|檔名:|建議檔名：|建議檔名:)', '', name)
    name = name.strip()
    return name

def analyze_video(file_path):
    """Uploads a video to Gemini File API, analyzes its content, and suggests a Chinese filename."""
    print(f"\nProcessing: {os.path.basename(file_path)}")
    print("Uploading to Gemini File API...")
    
    try:
        uploaded_file = client.files.upload(file=file_path)
        print(f"Upload complete. File Name: {uploaded_file.name}")
        
        # Wait for processing
        print("Waiting for video processing to complete...")
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(3)
            uploaded_file = client.files.get(uploaded_file.name)
            print(".", end="", flush=True)
        print("")
        
        if uploaded_file.state.name == "FAILED":
            raise Exception("Gemini video processing failed.")
            
        print("Analyzing video content...")
        
        
        prompt = """
        這是一個關於繩結技巧/生活實用繩結的短影片。
        請仔細觀看影片內容，並分析影片中主要示範的繩結種類、捆綁技巧或其具體用途。
        請直接為該影片取一個最貼切、具體、實用的繁體中文檔名。
        
        【命名規則】
        1. 長度限制在 12 個字以內。
        2. 請使用繁體中文。
        3. 請只回傳檔名本身，不要有副檔名（如 .mp4）、不要有任何引號（如「」或 ""）、不要有任何多餘的說明文字（如「建議檔名：」、「這是一個...」）。
        4. 名稱要具體好懂，例如：
           - 「露營張力鎖定結」
           - 「布角結」
           - 「二根樹枝十字固定」
           - 「雙繩對接簡易法」
           - 「機車單繩綁物」
           - 「木材安全掛結」
           - 「萬用活結」
        5. 不要回傳像「實用繩結技巧」這種太過籠統的名稱，請精準描述影片中的動作或結的名稱。
        
        請只回傳最適合的檔名字串：
        """
        
        response = client.models.generate_content(model=GEMINI_MODEL, contents=[prompt, uploaded_file])
        suggested_name = response.text.strip()
        print(f"Suggested name from API: {suggested_name}")
        
        # Delete from Gemini File API to keep space clean
        try:
            client.files.delete(uploaded_file.name)
            print("Successfully deleted temporary file from Gemini storage.")
        except Exception as delete_err:
            print(f"Warning: Failed to delete temporary file: {delete_err}")
            
        cleaned_name = sanitize_filename(suggested_name)
        if not cleaned_name:
            cleaned_name = "未命名繩結技巧"
            
        return cleaned_name
        
    except Exception as e:
        print(f"Error processing video {os.path.basename(file_path)}: {e}")
        return None

def run_review():
    """Analyze all videos and generate a JSON report of suggested names that differ from current names."""
    def safe_print(msg):
        try:
            print(msg)
        except UnicodeEncodeError:
            print(msg.encode('utf-8', 'ignore').decode('utf-8'))

    all_files = get_all_video_files()
    if not all_files:
        print("No video files found for review.")
        return

    print(f"Found {len(all_files)} video files to review.")

    review_map = {}
    for i, filename in enumerate(all_files, 1):
        safe_print(f"\n[{i}/{len(all_files)}] Reviewing: {filename}")
        file_path = os.path.join(TARGET_DIR, filename)
        suggested_name = analyze_video(file_path)
        if not suggested_name:
            print(f"Failed to analyze {filename}")
            continue
        # Compare with existing name (without extension)
        base_current = os.path.splitext(filename)[0]
        base_suggested = suggested_name
        if base_current != base_suggested:
            review_map[filename] = base_suggested + ".mp4"
            safe_print(f"Suggestion differs: {filename} => {base_suggested}.mp4")
        else:
            print("No change needed.")

    # Write review map to JSON file
    review_path = os.path.join(os.path.dirname(__file__), "rename_review.json")
    with open(review_path, "w", encoding="utf-8") as f:
        json.dump(review_map, f, ensure_ascii=False, indent=2)
    print(f"\nReview report saved to: {review_path}")
    if review_map:
        print("Files needing renaming:")
        for old, new in review_map.items():
            print(f"  {old}  =>  {new}")
    else:
        print("All files already have appropriate names.")


def run_dry_run():
    """Phase 1: Run dry-run analysis and save the mappings to a JSON file."""
    english_files = get_all_video_files()
    if not english_files:
        print("No English/downloader video files found to rename.")
        return
        
    print(f"Found {len(english_files)} files to analyze.")
    
    # Load existing map if any, to resume or skip already processed files
    existing_map = {}
    if os.path.exists(MAP_FILE):
        try:
            with open(MAP_FILE, "r", encoding="utf-8") as f:
                existing_map = json.load(f)
            print(f"Loaded existing map with {len(existing_map)} entries.")
        except Exception as e:
            print(f"Warning: Failed to load existing map file: {e}")
            
    mapping = existing_map.copy()
    
    for i, filename in enumerate(english_files, 1):
        print(f"\n[{i}/{len(english_files)}] File: {filename}")
        if filename in mapping and mapping[filename]:
            print(f"Already analyzed. Suggested name: {mapping[filename]}")
            continue
            
        file_path = os.path.join(TARGET_DIR, filename)
        suggested_name = analyze_video(file_path)
        
        if suggested_name:
            mapping[filename] = suggested_name + ".mp4"
            # Save progress iteratively
            with open(MAP_FILE, "w", encoding="utf-8") as f:
                json.dump(mapping, f, ensure_ascii=False, indent=2)
            # Sleep slightly to avoid rate limit
            time.sleep(2)
        else:
            print(f"Failed to analyze {filename}")
            
    print("\n--- Dry Run Completed ---")
    print(f"Mapping saved to: {MAP_FILE}")
    print("\nProposed Renames:")
    for old_name, new_name in sorted(mapping.items()):
        print(f"  {old_name}  ==>  {new_name}")

def apply_rename():
    """Phase 2: Read the JSON file and perform actual renames safely."""
    if not os.path.exists(MAP_FILE):
        print(f"Error: Mapping file {MAP_FILE} does not exist. Please run dry-run first.")
        return
        
    with open(MAP_FILE, "r", encoding="utf-8") as f:
        mapping = json.load(f)
        
    if not mapping:
        print("No mapping entries found in rename_map.json.")
        return
        
    print(f"Applying renames for {len(mapping)} files...")
    
    success_count = 0
    fail_count = 0
    
    for old_name, new_name in sorted(mapping.items()):
        old_path = os.path.join(TARGET_DIR, old_name)
        
        if not os.path.exists(old_path):
            print(f"Warning: Original file {old_name} not found, skipping.")
            continue
            
        # Clean new name just in case
        new_name_clean = sanitize_filename(os.path.splitext(new_name)[0]) + ".mp4"
        new_path = os.path.join(TARGET_DIR, new_name_clean)
        
        # Prevent collision/overwriting
        if os.path.exists(new_path) and old_path != new_path:
            base, ext = os.path.splitext(new_name_clean)
            counter = 2
            while True:
                candidate_name = f"{base}_{counter}{ext}"
                candidate_path = os.path.join(TARGET_DIR, candidate_name)
                if not os.path.exists(candidate_path):
                    new_name_clean = candidate_name
                    new_path = candidate_path
                    break
                counter += 1
                
        print(f"Renaming: {old_name}  ==>  {new_name_clean}")
        try:
            os.rename(old_path, new_path)
            success_count += 1
        except Exception as e:
            print(f"Failed to rename {old_name}: {e}")
            fail_count += 1
            
    print(f"\n--- Renaming Complete ---")
    print(f"Successfully renamed: {success_count} files")
    print(f"Failed to rename: {fail_count} files")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rename knot videos using Gemini API.")
    parser.add_argument("--apply", action="store_true", help="Apply the renames from rename_map.json.")
    parser.add_argument("--review", action="store_true", help="Generate a review report for all videos without renaming.")
    args = parser.parse_args()
    
    if args.apply:
        apply_rename()
    elif args.review:
        run_review()
    else:
        run_dry_run()

