from sqlalchemy import Column, Integer, String, Text, DateTime, func

from app.db import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    domain = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False)
    source_url = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
