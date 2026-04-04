from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    db_path: str = "data/mediscan.db"

    # Image storage
    image_storage_path: str = "data/prescriptions"

    # AI Server
    ai_server_url: str = "http://localhost:8001"
    ai_model: str = "mlx-community/Qwen3.5-9B-MLX-4bit"
    ai_max_tokens: int = 10000
    ai_timeout: int = 300

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
