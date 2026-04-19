import os
import shutil
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException

# Resolve path cleanly using pathlib (4 levels up from upload.py lands in EcoMindUz root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".webm"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB limit for MVP

def save_upload_file(upload_file: UploadFile) -> dict:
    """
    Saves the file to the local uploads directory safely.
    Includes type and size validation. Returns the dictionary data for content_blocks.
    """
    ext = Path(upload_file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File extension {ext} not allowed. Allowed: {ALLOWED_EXTENSIONS}"
        )
        
    # Check physical size manually
    upload_file.file.seek(0, 2)
    file_size = upload_file.file.tell()
    upload_file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 50MB.")

    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
        
    return {"url": f"/uploads/{unique_filename}", "filename": upload_file.filename}
