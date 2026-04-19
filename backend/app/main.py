from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import auth, topics, quizzes
from pathlib import Path
import os

app = FastAPI(title="EcoMindUz API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # TODO: restrict pointing to localhost:5173
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect the static files directory to serve uploaded images and videos
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(topics.router, prefix="/api/topics", tags=["topics"])
app.include_router(quizzes.router, prefix="/api", tags=["quizzes"])

@app.get("/")
def read_root():
    return {"message": "Welcome to EcoMindUz API"}
