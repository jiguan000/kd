from sqlalchemy.orm import Session

from app import models, schemas


def create_document(db: Session, document: schemas.DocumentCreate) -> models.Document:
    db_doc = models.Document(**document.model_dump())
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc


def list_documents(db: Session, domain: str | None = None) -> list[models.Document]:
    query = db.query(models.Document)
    if domain:
        query = query.filter(models.Document.domain == domain)
    return query.order_by(models.Document.created_at.desc()).all()


def get_document(db: Session, document_id: int) -> models.Document | None:
    return db.query(models.Document).filter(models.Document.id == document_id).first()
