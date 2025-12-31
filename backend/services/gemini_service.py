import httpx
from typing import Optional, Dict
from urllib.parse import quote

class GeminiAPIService:
    """
    Service untuk Gemini AI API (api.gimita.id)
    """
    
    def __init__(self):
        self.base_url = "https://api.gimita.id/api/ai/gemini"
        self.timeout = 60.0
        
        # System prompts yang tersedia
        self.system_modes = {
            "thinking": "thinking",      # Mode analisis mendalam
            "creative": "creative",      # Mode kreatif
            "precise": "precise",        # Mode presisi
            "default": "thinking"
        }
    
    async def chat(
        self, 
        message: str, 
        system: str = "thinking"
    ) -> str:
        """
        Kirim message ke Gemini AI
        
        Args:
            message: Pesan/prompt untuk Gemini
            system: Mode system (thinking/creative/precise)
            
        Returns:
            Response text dari Gemini
        """
        params = {
            "message": message,
            "system": system
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
            
            # Extract response text
            return data.get("response") or data.get("text") or data.get("message") or str(data)
    
    async def analyze_transcript_for_clips(
        self, 
        transcript: str, 
        video_duration: int,
        max_clips: int = 5
    ) -> list:
        """
        Analisis transkrip untuk menemukan momen viral
        
        Args:
            transcript: Transkrip video
            video_duration: Durasi video dalam detik
            max_clips: Maksimal jumlah clip yang dihasilkan
            
        Returns:
            List of viral moments dengan timestamp
        """
        prompt = f"""
Analisis transkrip video YouTube berikut dan temukan {max_clips} momen paling viral untuk dijadikan video shorts (format 9:16).

**Informasi Video:**
- Durasi total: {video_duration} detik
- Target format: TikTok/Reels/Shorts (30-60 detik per clip)

**Transkrip:**
{transcript}

**Kriteria Momen Viral:**
1. Hook kuat di 3 detik pertama
2. Durasi ideal 30-60 detik
3. Ada punchline/kesimpulan yang jelas
4. Bisa standalone tanpa konteks video utuh
5. Topik menarik untuk audience muda (18-35 tahun)
6. Cocok untuk format vertical

**PENTING: Berikan response dalam format JSON array yang VALID seperti ini:**
```json
[
  {{
    "start_time": 10.5,
    "end_time": 45.2,
    "title": "Judul Hook Menarik",
    "description": "Deskripsi kenapa ini viral",
    "score": 0.95,
    "hook": "Kalimat pembuka yang menarik"
  }},
  {{
    "start_time": 120.0,
    "end_time": 165.5,
    "title": "Judul Hook Kedua",
    "description": "Alasan viralitas",
    "score": 0.88,
    "hook": "Hook kedua"
  }}
]
