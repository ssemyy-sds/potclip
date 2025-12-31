import httpx
from typing import Optional, Dict, List
from urllib.parse import quote
import json
import re

class GrokAPIService:
    """
    Service untuk Grok Mini AI API (api.gimita.id)
    Support untuk transcription dan text analysis
    """
    
    def __init__(self):
        self.base_url = "https://api.gimita.id/api/ai/heckai"
        self.timeout = 90.0  # Grok might be slower
        
        # Available models
        self.models = {
            "grok-mini": "x-ai/grok-3-mini-beta",
            "grok-2": "x-ai/grok-2",  # if available
        }
        
        self.default_model = self.models["grok-mini"]
    
    async def chat(
        self, 
        prompt: str, 
        model: str = "grok-mini"
    ) -> str:
        """
        Send prompt to Grok AI
        
        Args:
            prompt: User prompt/question
            model: Model to use (grok-mini, grok-2)
            
        Returns:
            AI response text
        """
        model_id = self.models.get(model, self.default_model)
        
        params = {
            "model": model_id,
            "prompt": prompt
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
            return (
                data.get("response") or 
                data.get("text") or 
                data.get("message") or 
                data.get("content") or 
                str(data)
            )
    
    async def transcribe_audio_url(self, audio_url: str) -> str:
        """
        Transcribe audio from URL using Grok
        
        Args:
            audio_url: Direct URL to audio file
            
        Returns:
            Transcription text
        """
        prompt = f"""
Please transcribe the audio from this URL: {audio_url}

Provide a clean, accurate transcription with proper punctuation and formatting.
Include timestamps if possible in format [MM:SS].
"""
        
        response = await self.chat(prompt)
        return response
    
    async def analyze_transcript_for_clips(
        self, 
        transcript: str, 
        video_duration: int,
        max_clips: int = 5
    ) -> List[Dict]:
        """
        Analyze transcript to find viral moments using Grok
        
        Args:
            transcript: Video transcript
            video_duration: Duration in seconds
            max_clips: Maximum number of clips to generate
            
        Returns:
            List of viral moment objects
        """
        prompt = f"""
Analyze this YouTube video transcript and identify the {max_clips} most viral moments suitable for short-form content (TikTok/Reels/Shorts).

**Video Information:**
- Total Duration: {video_duration} seconds
- Target Format: 9:16 vertical video (30-60 seconds each)
- Platform: TikTok, Instagram Reels, YouTube Shorts

**Transcript:**
{transcript}

**Viral Moment Criteria:**
1. Strong hook in first 3 seconds
2. Ideal duration: 30-60 seconds
3. Clear punchline or conclusion
4. Standalone content (no context needed)
5. Engaging for 18-35 age demographic
6. Vertical format compatible

**IMPORTANT: Return ONLY a valid JSON array in this exact format:**
```json
[
  {{
    "start_time": 10.5,
    "end_time": 45.2,
    "title": "Catchy Hook Title",
    "description": "Why this is viral",
    "score": 0.95,
    "hook": "Opening line that grabs attention",
    "tags": ["motivation", "tips", "viral"]
  }}
]
