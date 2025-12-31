from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase_client import SupabaseManager
from video_processor import VideoProcessor

app = FastAPI(title="YouClip Clone API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

supabase = SupabaseManager()
processor = VideoProcessor(supabase)

class VideoRequest(BaseModel):
    youtube_url: str

@app.post("/api/process")
async def process_video(request: VideoRequest, background_tasks: BackgroundTasks):
    """Process YouTube video"""
    video_id = supabase.create_video_record(
        youtube_url=request.youtube_url,
        title="Processing...",
        duration=0
    )
    
    background_tasks.add_task(processor.process_video_pipeline, video_id, request.youtube_url)
    
    return {
        "video_id": video_id,
        "status": "processing",
        "message": "Check /api/status/{video_id}"
    }

@app.get("/api/status/{video_id}")
async def get_status(video_id: str):
    """Get processing status"""
    video = supabase.get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    clips = supabase.get_clips_by_video(video_id)
    
    return {
        "video_id": video_id,
        "status": video["status"],
        "title": video["title"],
        "clips": clips
    }

@app.get("/api/download/{clip_id}")
async def download_clip(clip_id: str):
    """Get download URL"""
    clip = supabase.client.table("clips").select("storage_path").eq("id", clip_id).execute()
    if not clip.data:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    download_url = supabase.get_clip_download_url(clip.data[0]["storage_path"])
    return {"download_url": download_url}

@app.get("/health")
async def health():
    return {"status": "healthy"}
