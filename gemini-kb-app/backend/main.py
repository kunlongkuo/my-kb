import os
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import shutil
import uuid
from processors import process_file, IMAGE_EXTENSIONS
from vector_store import VectorDB
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db = VectorDB()

@app.on_event("startup")
async def startup_event():
    # Pre-load the models in a background thread so it doesn't block startup
    import threading
    print("Starting background model pre-loading...")
    threading.Thread(target=db.get_models, daemon=True).start()

# Gemini is now optional for the final answer generation
ai_client = None
gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    try:
        ai_client = genai.Client(api_key=gemini_key)
        print("Gemini API client initialized.")
    except Exception as e:
        print(f"Failed to initialize Gemini client: {e}")
else:
    print("No GEMINI_API_KEY found. Running in search-only mode.")

class QueryRequest(BaseModel):
    prompt: str

class FolderRequest(BaseModel):
    path: str

indexing_status = {"status": "idle", "processed": 0, "total": 0, "current_file": "", "doc_count": 0}

def format_gemini_error(error: Exception) -> str:
    error_text = str(error)
    if "RESOURCE_EXHAUSTED" in error_text or "429" in error_text or "quota" in error_text.lower():
        return (
            "Gemini API 額度已用完，以下是為您找到的相關參考資料。"
        )
    return f"生成 AI 回答時發生錯誤，以下是搜尋結果：\n({error_text})"

def index_folder_task(folder_path: str):
    global indexing_status
    indexing_status["status"] = "indexing"
    files_to_index = []
    
    print(f"--- 開始掃描資料夾: {folder_path} ---")
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            files_to_index.append(os.path.join(root, file))
    
    total_files = len(files_to_index)
    indexing_status["total"] = total_files
    indexing_status["processed"] = 0
    print(f"找到 {total_files} 個檔案，準備開始索引...")
    
    for i, file_path in enumerate(files_to_index):
        filename = os.path.basename(file_path)
        indexing_status["current_file"] = filename
        indexing_status["processed"] = i + 1
        
        # 每 10 個檔案印一次進度，或者圖片檔必印
        if (i + 1) % 10 == 0 or i == 0 or i == total_files - 1:
            print(f"[{i+1}/{total_files}] 正在處理: {filename}")
        
        try:
            content, file_type = process_file(file_path)
            
            if file_type == 'image':
                db.add_image_document(
                    image_path=file_path,
                    metadata={"source": file_path, "filename": filename, "type": "image"},
                    doc_id=str(uuid.uuid4())
                )
                print(f"  -> [圖片] {filename} 索引成功")
            elif content and len(content.strip()) > 0:
                db.add_document(
                    text=content,
                    metadata={"source": file_path, "filename": filename, "type": file_type},
                    doc_id=str(uuid.uuid4())
                )
                # print(f"  -> [文件] {filename} 索引成功")
            elif file_type in ['media', 'unsupported']:
                # 對於影片、音樂或未知檔案，至少索引其檔名
                db.add_document(
                    text=f"檔案名稱: {filename}",
                    metadata={"source": file_path, "filename": filename, "type": file_type},
                    doc_id=str(uuid.uuid4())
                )
                print(f"  -> [其他] {filename} 已記錄檔名")
            # 不支援或空檔案不報錯，直接跳過
        except Exception as e:
            print(f"  !! 處理失敗 {filename}: {e}")
            continue
    
    indexing_status["status"] = "idle"
    indexing_status["current_file"] = ""
    indexing_status["doc_count"] = db.get_doc_count()
    print(f"--- 索引完成！總計筆數: {indexing_status['doc_count']} ---")

@app.post("/index-folder")
async def index_folder(request: FolderRequest, background_tasks: BackgroundTasks):
    if not os.path.exists(request.path):
        raise HTTPException(status_code=400, detail="Path does not exist")
    background_tasks.add_task(index_folder_task, request.path)
    return {"message": "Indexing started"}

@app.post("/upload")
async def upload_files(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    global indexing_status
    print(f"Received {len(files)} files for upload")
    indexing_status["status"] = "indexing"
    indexing_status["total"] = len(files)
    indexing_status["processed"] = 0
    
    temp_dir = "./temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        media_dir = "./indexed_media"
        os.makedirs(media_dir, exist_ok=True)
        
        for file in files:
            safe_name = os.path.basename(file.filename)
            print(f"Processing: {safe_name}")
            indexing_status["current_file"] = safe_name
            
            # Use temp for initial processing
            temp_path = os.path.join(temp_dir, safe_name)
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            try:
                content, file_type = process_file(temp_path)
                
                if file_type == 'image':
                    # Move images to a permanent location for previews
                    final_path = os.path.abspath(os.path.join(media_dir, str(uuid.uuid4()) + "_" + safe_name))
                    shutil.move(temp_path, final_path)
                    
                    db.add_image_document(
                        image_path=final_path,
                        metadata={"source": final_path, "filename": safe_name, "type": "image"},
                        doc_id=str(uuid.uuid4())
                    )
                    print(f"  -> Image indexed locally")
                elif content and len(content.strip()) > 0:
                    db.add_document(
                        text=content,
                        metadata={"source": file.filename, "filename": safe_name, "type": file_type},
                        doc_id=str(uuid.uuid4())
                    )
                    print(f"  -> Text indexed locally")
                    if os.path.exists(temp_path): os.remove(temp_path)
                else:
                    print(f"  -> Skipped (unsupported: {file_type})")
                    if os.path.exists(temp_path): os.remove(temp_path)
            except Exception as e:
                print(f"  -> Error processing {safe_name}: {e}")
                if os.path.exists(temp_path): os.remove(temp_path)
            
            indexing_status["processed"] += 1
    except Exception as e:
        print(f"Upload error: {e}")
        indexing_status["status"] = "idle"
        raise HTTPException(status_code=500, detail=str(e))
        
    indexing_status["status"] = "idle"
    indexing_status["current_file"] = ""
    indexing_status["doc_count"] = db.get_doc_count()
    return {"message": "Upload and indexing complete"}

@app.get("/status")
async def get_status():
    indexing_status["doc_count"] = db.get_doc_count()
    return indexing_status

@app.post("/clear")
async def clear_db():
    db.clear()
    return {"message": "Database cleared", "doc_count": 0}

@app.get("/files")
async def get_file(path: str):
    import urllib.parse
    # Decode URL-encoded path
    decoded_path = urllib.parse.unquote(path)
    
    # Normalize path
    normalized_path = os.path.normpath(decoded_path)
    
    # For Windows absolute paths (e.g., J:\...), normpath is usually enough
    # but we should check if it exists
    if not os.path.exists(normalized_path):
        # Handle cases where it might be relative to project root
        alt_path = os.path.abspath(normalized_path)
        if os.path.exists(alt_path):
            normalized_path = alt_path
        else:
            print(f"File not found: {normalized_path}")
            raise HTTPException(status_code=404, detail=f"File not found: {decoded_path}")
            
    if not os.path.isfile(normalized_path):
        raise HTTPException(status_code=400, detail="Not a file")
        
    return FileResponse(normalized_path)

class OpenFileRequest(BaseModel):
    path: str

@app.post("/open-file")
async def open_file(request: OpenFileRequest):
    normalized_path = os.path.normpath(request.path)
    if not os.path.exists(normalized_path):
        raise HTTPException(status_code=404, detail=f"檔案不存在：{request.path}")
    if not os.path.isfile(normalized_path):
        raise HTTPException(status_code=400, detail="路徑必須是檔案")
        
    try:
        import platform
        import subprocess
        
        system = platform.system()
        if system == 'Windows':
            os.startfile(normalized_path)
        elif system == 'Darwin':  # macOS
            subprocess.call(['open', normalized_path])
        else:  # Linux
            subprocess.call(['xdg-open', normalized_path])
            
        return {"message": "檔案已成功在本地開啟"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"系統開啟檔案失敗：{str(e)}")

@app.post("/query")
async def query_kb(request: QueryRequest):
    if not db.is_ready:
        return {
            "answer": "本地 AI 模型正在載入中（第一次使用需下載約 500MB），請稍候 1-2 分鐘再試一次。",
            "sources": []
        }
    
    doc_count = db.get_doc_count()
    if doc_count == 0:
        return {
            "answer": "資料庫目前是空的，請先選擇資料夾或上傳檔案來建立索引。",
            "sources": []
        }
    
    # 1. Local Vector Search (No API)
    # Increase n_results to find more variety (images vs text)
    results = db.query(request.prompt, n_results=50)
    
    if not results['documents'] or not results['documents'][0]:
        return {
            "answer": "找不到相關資料，請嘗試不同的問法。",
            "sources": []
        }
    
    # 2. Extract Sources and Build context
    sources = []
    seen_paths = set()
    context_list = []
    
    for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
        f_type = meta.get('type', 'unknown')
        f_name = meta.get('filename', 'unknown')
        f_path = meta.get('source', '')
        
        # Add to sources list if unique
        if f_path and f_path not in seen_paths:
            # Check if file locally exists
            normalized_path = os.path.normpath(f_path)
            local_exists = os.path.exists(normalized_path) and os.path.isfile(normalized_path)
            
            # Extract excerpt snippet
            snippet = doc[:300] + "..." if doc and len(doc) > 300 else doc
            
            sources.append({
                "filename": f_name,
                "type": f_type,
                "path": f_path,
                "snippet": snippet,
                "local_exists": local_exists
            })
            seen_paths.add(f_path)
            
        # Add to context list for Gemini
        if f_type == 'image':
            context_list.append(f"[檔案類型: 圖片] [檔案名稱: {f_name}]\n(這是一張圖片，內容與搜尋詞相關)")
        else:
            context_list.append(f"[檔案類型: {f_type}] [檔案名稱: {f_name}]\n{doc}")
            
    context = "\n\n---\n\n".join(context_list)
    
    # 3. Try Gemini RAG (Optional)
    if ai_client:
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        prompt = f"""你是一個知識庫助手。請根據以下提供的上下文資料來回答使用者的問題。
規則：
1. 只根據提供的上下文來回答
2. 如果上下文中沒有足夠資訊，請明確說明
3. 回答時請引用來源檔名
4. 使用繁體中文回答

上下文資料：
{context}

使用者問題：
{request.prompt}
"""
        try:
            response = ai_client.models.generate_content(
                model=model_name,
                contents=[prompt],
            )
            return {
                "answer": response.text,
                "sources": sources
            }
        except Exception as e:
            print(f"Gemini generation failed: {e}")
            answer = format_gemini_error(e)
            return {
                "answer": answer,
                "sources": sources
            }
    else:
        # Fallback to direct search results if no AI client
        return {
            "answer": "已完成本地搜尋，找到以下相關檔案內容：",
            "sources": sources
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
