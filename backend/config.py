from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Third-Party APIs
    youtube_downloader_api_key: str
    youtube_downloader_api_host: str
    
    # AI APIs
    groq_api_key: str
    gemini_api_key: str
    openai_api_key: str = ""
    
    # Supabase
    supabase_url: str
    supabase_key: str
    
    # App Config
    environment: str = "development"
    max_video_duration: int = 3600
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
