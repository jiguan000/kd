from pathlib import Path
import shutil
import uuid

from fastapi import UploadFile

from config import get_settings


def save_upload(file: UploadFile) -> tuple[str, str]:
    settings = get_settings()
    suffix = Path(file.filename or "").suffix
    filename = f"{uuid.uuid4().hex}{suffix}"
    destination = settings.storage_dir / filename
    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    file_type = suffix.lstrip(".").lower() or "bin"
    return str(destination), file_type


def save_text_content(content: str, extension: str = "html") -> tuple[str, str]:
    settings = get_settings()
    filename = f"{uuid.uuid4().hex}.{extension}"
    destination = settings.storage_dir / filename
    destination.write_text(content, encoding="utf-8")
    return str(destination), extension
