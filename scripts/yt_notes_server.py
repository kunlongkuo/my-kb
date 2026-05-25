from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from youtube_to_notes import process_youtube_video
from typing import Optional
import os

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In a browser extension context, origins can be tricky, so * is safest for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    url: str
    model: Optional[str] = None

@app.post("/summarize")
async def summarize(request: VideoRequest):
    try:
        markdown_content = process_youtube_video(request.url, request.model)
        return {
            "status": "success", 
            "message": "Note created in Obsidian vault.",
            "content": markdown_content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
