from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    groq_api_key: str = Field(..., alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")
    huggingface_api_key: str = Field(..., alias="HUGGINGFACE_API_KEY")
    hf_background_model: str = Field(default="stabilityai/stable-diffusion-xl-base-1.0", alias="HF_BACKGROUND_MODEL")
    hf_character_model: str = Field(default="stabilityai/stable-diffusion-xl-base-1.0", alias="HF_CHARACTER_MODEL")
    hf_segmentation_model: str = Field(default="briaai/RMBG-1.4", alias="HF_SEGMENTATION_MODEL")
    tts_model_name: str = Field(default="tts_models/en/vctk/vits", alias="TTS_MODEL_NAME")
    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    frontend_origin: str = Field(default="http://localhost:5173", alias="FRONTEND_ORIGIN")
    data_root: str = Field(default="data", alias="DATA_ROOT")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    if Path(".env").exists():
        load_dotenv(".env")
    return Settings()
