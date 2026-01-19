from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel
import os


load_dotenv()


class Settings(BaseModel):
    database_url: str = os.getenv("DATABASE_URL", "")
    storage_dir: Path = Path(os.getenv("STORAGE_DIR", "./storage"))
    allowed_origins: list[str] = os.getenv("ALLOWED_ORIGINS", "").split(",")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    return settings
