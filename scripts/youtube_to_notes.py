import os
import re
import datetime
from typing import Optional, List, Dict
import time
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import openai
from dotenv import load_dotenv
import subprocess

# Load configuration
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WIKI_PATH = os.getenv("WIKI_PATH", "wiki/youtube-notes")
LOG_FILE = os.getenv("LOG_FILE", "log.md")
INDEX_FILE = os.getenv("INDEX_FILE", "index.md")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

openai_client = None
if OPENAI_API_KEY:
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

def get_video_id(url: str) -> Optional[str]:
    """Extract video ID from YouTube URL."""
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
        r"embed\/([0-9A-Za-z_-]{11})"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def fetch_transcript(video_id: str) -> Optional[str]:
    """Fetch transcript using youtube-transcript-api."""
    try:
        api = YouTubeTranscriptApi()
        # Try to get manually created transcripts first, then auto-generated
        transcript_list = api.list(video_id)
        
        # Prefer manual, then auto-generated
        # Try to get any available transcript
        transcript = transcript_list.find_transcript(['zh-TW', 'zh-CN', 'en', 'zh', 'ja', 'ko'])
        # If still not found, just get the first one available
        if not transcript:
            transcript = next(iter(transcript_list))
            
        data = transcript.fetch()
        return " ".join([d.text for d in data])
    except Exception as e:
        print(f"Transcript fetch failed: {e}")
        return None

def _generate_with_gemini(text: Optional[str], prompt: str, model_name: str, audio_file: Optional[str] = None) -> str:
    model = genai.GenerativeModel(model_name)
    if text:
        content = [prompt, f"TRANSCRIPT:\n{text[:100000]}"]
    elif audio_file:
        print(f"Uploading audio file to Gemini: {audio_file}")
        audio_data = genai.upload_file(path=audio_file)
        # Wait for processing
        while audio_data.state.name == "PROCESSING":
            time.sleep(2)
            audio_data = genai.get_file(audio_data.name)
        content = [prompt, audio_data]
    else:
        return "Error: No content to summarize."
    
    response = model.generate_content(content)
    return response.text

def _generate_with_openai(text: Optional[str], prompt: str, model_name: str, audio_file: Optional[str] = None) -> str:
    if not openai_client:
        return "Error: OPENAI_API_KEY is not set."
    
    # If no text but audio exists, transcribe using Whisper first
    if not text and audio_file:
        print(f"Transcribing audio file with Whisper: {audio_file}")
        with open(audio_file, "rb") as audio:
            transcript_response = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio
            )
        text = transcript_response.text
        
    if not text:
        return "Error: No content to summarize."
        
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"TRANSCRIPT:\n{text[:100000]}"}
    ]
    
    response = openai_client.chat.completions.create(
        model=model_name,
        messages=messages
    )
    return response.choices[0].message.content

def generate_summary(text: Optional[str], video_url: str, title: str = "Video Summary", audio_file: Optional[str] = None, model_name: Optional[str] = None) -> str:
    """Generate summary using Gemini or OpenAI API. Handles both text and audio input."""
    target_model = model_name or GEMINI_MODEL
    print(f"Using model: {target_model}")
    
    prompt = f"""
    You are an expert knowledge curator. Summarize the following YouTube video into a high-quality Markdown note for Obsidian.
    
    VIDEO TITLE: {title}
    VIDEO URL: {video_url}
    
    ### FORMAT REQUIREMENTS:
    1. **Summary Tag**: Start with exactly 4 Chinese characters in brackets (e.g., [核心精華] or [技術要點]).
    2. **One-Sentence Overview**: A single, powerful sentence summarizing the main takeaway.
    3. **No Meta-Talk**: Do not include any introductory sentences or descriptions about the note itself (e.g., "這是一份針對..." or "這份筆記整理了..."). Start directly with the content.
    4. **Language**:
       - If the content is English, provide a bilingual (Traditional Chinese and English) summary.
       - If the content is Chinese, provide a Traditional Chinese summary.
    5. **Detailed Notes**: Use bullet points and headers. Group by key concepts. Use timestamps if you can infer them.
    6. **Tone**: Professional, insightful, and concise.
    7. **Markdown**: Use semantic Markdown.
    """
    
    if target_model.startswith("gpt-") or target_model.startswith("o1-"):
        return _generate_with_openai(text, prompt, target_model, audio_file)
    else:
        return _generate_with_gemini(text, prompt, target_model, audio_file)

def download_audio(video_url: str) -> Optional[str]:
    """Download audio using yt-dlp."""
    print("Downloading audio...")
    output_tmpl = "temp_audio.%(ext)s"
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "128K",
        "-o", output_tmpl,
        video_url
    ]
    try:
        subprocess.run(cmd, check=True)
        # yt-dlp adds extension, find the resulting file
        for f in os.listdir("."):
            if f.startswith("temp_audio."):
                return f
        return None
    except Exception as e:
        print(f"Audio download failed: {e}")
        return None

def update_vault_metadata(file_path: str, title: str):
    """Update log.md and index.md."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    relative_path = os.path.relpath(file_path, start=os.getcwd())
    
    # Update log.md
    log_entry = f"- {now}: Ingested YouTube summary [{title}]({relative_path})\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)
        
    # Update index.md
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    section_header = "### YouTube 內容摘要 (YouTube Summaries)"
    entry = f"- [{title}]({relative_path})\n"
    
    if section_header in content:
        # Insert after the header
        new_content = content.replace(section_header, f"{section_header}\n{entry}")
    else:
        # Create the section under Entities (after line 38)
        new_content = content.replace("### AI 工具 (AI Tools)", f"{section_header}\n{entry}\n\n### AI 工具 (AI Tools)")
    
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)

def get_video_info(video_url: str) -> dict:
    """Get video title and other info using yt-dlp."""
    print("Fetching video info...")
    import json
    cmd = ["yt-dlp", "--no-playlist", "--dump-json", video_url]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        return {"title": data.get("title", "YouTube Video"), "id": data.get("id")}
    except Exception as e:
        print(f"yt-dlp info fetch failed: {e}")
        return {"title": "YouTube Video", "id": get_video_id(video_url)}

def process_youtube_video(url: str, model_name: Optional[str] = None):
    """Main workflow."""
    try:
        info = get_video_info(url)
        video_id = info["id"]
        title = info["title"]
        
        if not video_id:
            return "Error: Invalid YouTube URL"
        
        print(f"Processing: {title} ({video_id})")
        
        text = fetch_transcript(video_id)
        audio_file = None
        
        if not text:
            print("No transcript found. Falling back to audio transcription...")
            audio_file = download_audio(url)
            if not audio_file:
                return "Error: Could not retrieve transcript or download audio."
        
        print("Generating summary...")
        summary_md = generate_summary(text, url, title, audio_file, model_name)
        
        # Prepend description and video URL to the content
        header = f"這是一份針對 YouTube 影片 **《{title}》** 所整理的 Obsidian 高品質筆記。\n\n"
        header += f"🔗 **影片網址**：[{url}]({url})\n\n---\n\n"
        summary_md = header + summary_md
        
        # Cleanup audio
        if audio_file and os.path.exists(audio_file):
            os.remove(audio_file)
        
        # Ensure directory exists
        os.makedirs(WIKI_PATH, exist_ok=True)
        
        # Clean title for filename
        clean_title = re.sub(r'[\\/*?:"<>|]', "", title)[:50]
        filename = f"{clean_title}_{video_id}.md"
        file_path = os.path.join(WIKI_PATH, filename)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(summary_md)
            
        update_vault_metadata(file_path, title)
        print(f"Saved to {file_path}")
        return summary_md
    except Exception as e:
        print(f"Process failed: {e}")
        return f"Error during processing: {str(e)}"

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        process_youtube_video(sys.argv[1])
    else:
        print("Usage: python youtube_to_notes.py <youtube_url>")
