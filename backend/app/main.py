from pathlib import Path

from fastapi import FastAPI, Depends, UploadFile, Form, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from config import get_settings
from db import Base, engine, get_db
import schemas, crud
from storage import save_upload, save_text_content
from wechat import fetch_wechat_article


settings = get_settings()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Knowledge Base API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin for origin in settings.allowed_origins if origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/documents", response_model=list[schemas.DocumentRead])
def list_documents(domain: str | None = None, db: Session = Depends(get_db)):
    return crud.list_documents(db, domain)


@app.get("/documents/{document_id}", response_model=schemas.DocumentRead)
def get_document(document_id: int, db: Session = Depends(get_db)):
    doc = crud.get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@app.post("/documents/upload", response_model=schemas.DocumentRead)
def upload_document(
    title: str = Form(...),  # 明确指定为表单字段
    domain: str = Form(...),  # 明确指定为表单字段
    description: str | None = Form(None),  # 可选的表单字段
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    file_path, file_type = save_upload(file)
    doc = schemas.DocumentCreate(
        title=title,
        domain=domain,
        description=description,
        file_path=file_path,
        file_type=file_type,
    )
    return crud.create_document(db, doc)


@app.delete("/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """
    删除文档及其关联的文件
    """
    # 先获取文档信息
    doc = crud.get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 删除数据库记录
    deleted = crud.delete_document(db, document_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete document from database")

    # 删除物理文件
    try:
        file_path = Path(doc.file_path)
        if file_path.exists():
            file_path.unlink()  # 删除文件
    except Exception as e:
        # 记录错误但不要中断操作（因为数据库记录已删除）
        print(f"Warning: Failed to delete file {doc.file_path}: {e}")

    return {"message": "Document deleted successfully", "document_id": document_id}


from fastapi import Form, Depends, HTTPException, Response
from sqlalchemy.orm import Session

# 你已有的导入保持不变，只需要确保 wechat.py 里有这两个函数
from wechat import fetch_wechat_article, fetch_wechat_image_bytes


@app.post("/documents/wechat", response_model=schemas.DocumentRead)
def ingest_wechat(
        url: str = Form(...),
        domain: str = Form(...),
        description: str | None = Form(None),
        db: Session = Depends(get_db)
):
    try:
        #  关键：把图片 src 改写为你后端代理接口
        article = fetch_wechat_article(url, image_proxy_path="/wechat/image")

        if not article.content_html:
            raise HTTPException(
                status_code=400,
                detail="无法提取文章内容，可能文章已被删除或访问受限"
            )

        file_path, file_type = save_text_content(article.content_html, "html")
        doc = schemas.DocumentCreate(
            title=article.title,
            domain=domain,
            description=description,
            file_path=file_path,
            file_type=file_type,
            source_url=url,
        )
        return crud.create_document(db, doc)

    except ValueError as e:
        raise HTTPException(
            status_code=403,
            detail=f"微信反爬虫限制: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"处理微信文章失败: {str(e)}"
        )

@app.get("/wechat/image")
def wechat_image(u: str):
    """
    图片代理：前端请求 /wechat/image?u=<原始微信图片URL>
    后端带正确 Referer 去请求微信 CDN，再把图片流返回给前端
    """
    try:
        img_bytes, content_type = fetch_wechat_image_bytes(u)
        return Response(content=img_bytes, media_type=content_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"微信图片代理失败: {str(e)}")


@app.get("/files/{document_id}")
def get_file(document_id: int, db: Session = Depends(get_db)):
    doc = crud.get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    path = Path(doc.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File missing")
    return FileResponse(path)
