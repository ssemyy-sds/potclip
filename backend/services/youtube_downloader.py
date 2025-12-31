import httpx
from typing import Optional, Dict, List
from urllib.parse import quote
import asyncio

class YouTubeDownloaderAPI:
    """
    Service untuk YouTube Downloader API (api.gimita.id)
    """
    
    def __init__(self):
        self.base_url = "https://api.gimita.id/api/downloader/ytdown"
        self.timeout = 60.0
        
        # Format IDs yang tersedia
        self.formats = {
            "1080p": "137+140",  # Video 1080p + Audio
            "720p": "22",         # Video 720p + Audio
            "480p": "135+140",    # Video 480p + Audio
            "360p": "18",         # Video 360p + Audio (default)
            "audio": "140"        # Audio only (untuk transcription)
        }
    
    async def get_video_info(self, youtube_url: str) -> Dict:
        """
        Dapatkan informasi video YouTube
        
        Args:
            youtube_url: URL video YouTube
            
        Returns:
            Dict dengan info video (title, duration, thumbnail, dll)
        """
        params = {
            "type": "video",
            "url": youtube_url
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                self.base_url,
                params=params,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_download_url(
        self, 
        youtube_url: str, 
        quality: str = "720p"
    ) -> str:
        """
        Dapatkan URL download video
        
        Args:
            youtube_url: URL video YouTube
            quality: Kualitas video (1080p, 720p, 480p, 360p, audio)
            
        Returns:
            Direct download URL
        """
        format_id = self.formats.get(quality, self.formats["720p"])
        
        params = {
            "format_id": format_id,
            "type": "video",
            "url": youtube_url
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                self.base_url,
                params=params,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            
            # Return download URL
            return data.get("download_url") or data.get("url") or data.get("link")
    
    async def download_video_file(
        self, 
        youtube_url: str, 
        output_path: str,
        quality: str = "720p"
    ) -> str:
        """
        Download video file ke disk
        
        Args:
            youtube_url: URL video YouTube
            output_path: Path untuk menyimpan file
            quality: Kualitas video
            
        Returns:
            Path file yang sudah didownload
        """
        download_url = await self.get_download_url(youtube_url, quality)
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("GET", download_url) as response:
                response.raise_for_status()
                
                with open(output_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
        
        return output_path
    
    async def get_audio_url(self, youtube_url: str) -> str:
        """
        Dapatkan URL audio untuk transcription
        
        Args:
            youtube_url: URL video YouTube
            
        Returns:
            Direct audio download URL
        """
        return await self.get_download_url(youtube_url, quality="audio")
