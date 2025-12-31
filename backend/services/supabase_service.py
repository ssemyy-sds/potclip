from supabase import create_client, Client
from datetime import datetime
from typing import Optional, List, Dict
import os
from dotenv import load_dotenv

load_dotenv()

class SupabaseService:
    """
    Complete Supabase service untuk YouClip
    """
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY")  # Use service key for backend
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        self.bucket_clips = "video-clips"
        self.bucket_thumbnails = "thumbnails"
    
    # ==================== VIDEO OPERATIONS ====================
    
    def create_video(self, youtube_url: str, youtube_id: str = None) -> str:
        """
        Create new video record
        
        Returns:
            video_id (UUID)
        """
        data = {
            "youtube_url": youtube_url,
            "youtube_id": youtube_id,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = self.client.table("videos").insert(data).execute()
        return result.data[0]["id"]
    
    def update_video(
        self, 
        video_id: str, 
        **kwargs
    ) -> None:
        """
        Update video record
        
        Args:
            video_id: UUID of video
            **kwargs: Fields to update (status, title, duration, transcript, etc)
        """
        kwargs["updated_at"] = datetime.utcnow().isoformat()
        
        self.client.table("videos").update(kwargs).eq("id", video_id).execute()
    
    def get_video(self, video_id: str) -> Optional[Dict]:
        """Get video by ID"""
        result = self.client.table("videos").select("*").eq("id", video_id).execute()
        return result.data[0] if result.data else None
    
    def get_video_by_url(self, youtube_url: str) -> Optional[Dict]:
        """Get video by YouTube URL"""
        result = self.client.table("videos").select("*").eq("youtube_url", youtube_url).execute()
        return result.data[0] if result.data else None
    
    def get_all_videos(self, limit: int = 50, status: str = None) -> List[Dict]:
        """Get all videos with optional status filter"""
        query = self.client.table("videos").select("*")
        
        if status:
            query = query.eq("status", status)
        
        result = query.order("created_at", desc=True).limit(limit).execute()
        return result.data
    
    def delete_video(self, video_id: str) -> None:
        """Delete video and all its clips (CASCADE)"""
        self.client.table("videos").delete().eq("id", video_id).execute()
    
    # ==================== CLIP OPERATIONS ====================
    
    def create_clip(
        self,
        video_id: str,
        title: str,
        start_time: float,
        end_time: float,
        description: str = None,
        score: float = 0.7,
        hook: str = None,
        tags: List[str] = None,
        storage_path: str = None
    ) -> str:
        """
        Create new clip record
        
        Returns:
            clip_id (UUID)
        """
        data = {
            "video_id": video_id,
            "title": title,
            "description": description,
            "start_time": start_time,
            "end_time": end_time,
            "duration": end_time - start_time,
            "score": score,
            "hook": hook,
            "tags": tags or [],
            "storage_path": storage_path,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = self.client.table("clips").insert(data).execute()
        return result.data[0]["id"]
    
    def update_clip(self, clip_id: str, **kwargs) -> None:
        """Update clip record"""
        self.client.table("clips").update(kwargs).eq("id", clip_id).execute()
    
    def get_clip(self, clip_id: str) -> Optional[Dict]:
        """Get clip by ID"""
        result = self.client.table("clips").select("*").eq("id", clip_id).execute()
        return result.data[0] if result.data else None
    
    def get_clips_by_video(self, video_id: str) -> List[Dict]:
        """Get all clips for a video"""
        result = self.client.table("clips").select("*").eq("video_id", video_id).order("score", desc=True).execute()
        return result.data
    
    def increment_clip_downloads(self, clip_id: str) -> None:
        """Increment download count"""
        clip = self.get_clip(clip_id)
        if clip:
            new_count = clip.get("download_count", 0) + 1
            self.update_clip(clip_id, download_count=new_count)
    
    # ==================== STORAGE OPERATIONS ====================
    
    def upload_clip(self, file_path: str, storage_path: str) -> str:
        """
        Upload clip file to Supabase Storage
        
        Args:
            file_path: Local file path
            storage_path: Path in storage (e.g., "video_id/clip_0.mp4")
            
        Returns:
            Public URL
        """
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Upload file
        self.client.storage.from_(self.bucket_clips).upload(
            path=storage_path,
            file=file_data,
            file_options={"content-type": "video/mp4", "upsert": "true"}
        )
        
        # Get public URL
        public_url = self.client.storage.from_(self.bucket_clips).get_public_url(storage_path)
        return public_url
    
    def upload_thumbnail(self, file_path: str, storage_path: str) -> str:
        """Upload thumbnail to storage"""
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        self.client.storage.from_(self.bucket_thumbnails).upload(
            path=storage_path,
            file=file_data,
            file_options={"content-type": "image/jpeg", "upsert": "true"}
        )
        
        return self.client.storage.from_(self.bucket_thumbnails).get_public_url(storage_path)
    
    def get_download_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """
        Get temporary signed URL for download
        
        Args:
            storage_path: Path in storage
            expires_in: Expiry time in seconds (default 1 hour)
            
        Returns:
            Signed URL
        """
        result = self.client.storage.from_(self.bucket_clips).create_signed_url(
            path=storage_path,
            expires_in=expires_in
        )
        return result["signedURL"]
    
    def delete_clip_file(self, storage_path: str) -> None:
        """Delete clip file from storage"""
        self.client.storage.from_(self.bucket_clips).remove([storage_path])
    
    def list_files(self, folder_path: str = "") -> List[Dict]:
        """List all files in a folder"""
        result = self.client.storage.from_(self.bucket_clips).list(folder_path)
        return result
    
    # ==================== ANALYTICS ====================
    
    def get_stats(self) -> Dict:
        """Get overall statistics"""
        videos_count = len(self.client.table("videos").select("id", count="exact").execute().data)
        clips_count = len(self.client.table("clips").select("id", count="exact").execute().data)
        
        completed_videos = len(
            self.client.table("videos")
            .select("id", count="exact")
            .eq("status", "completed")
            .execute().data
        )
        
        return {
            "total_videos": videos_count,
            "total_clips": clips_count,
            "completed_videos": completed_videos,
            "success_rate": (completed_videos / videos_count * 100) if videos_count > 0 else 0
        }
