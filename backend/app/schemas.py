from datetime import datetime
from pydantic import BaseModel


class DocumentBase(BaseModel):
    title: str
    domain: str
    description: str | None = None
    file_type: str
    source_url: str | None = None


class DocumentCreate(DocumentBase):
    file_path: str


class DocumentRead(DocumentBase):
    id: int
    file_path: str
    created_at: datetime

    class Config:
        from_attributes = True
