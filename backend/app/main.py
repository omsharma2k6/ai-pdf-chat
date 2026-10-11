import gc
import os
from pathlib import Path
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

try:
    from app.config import (
        ALLOWED_ORIGINS,
        APP_DESCRIPTION,
        APP_TITLE,
        APP_VERSION,
        PDF_STORAGE_DIR,
    )
    from app.pdf_service import extract_pdf_pages
    from app.schemas import UploadResponse
except ImportError:
    from config import (
        ALLOWED_ORIGINS,
        APP_DESCRIPTION,
        APP_TITLE,
        APP_VERSION,
        PDF_STORAGE_DIR,
    )
    from pdf_service import extract_pdf_pages
    from schemas import UploadResponse

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
)

# Configure CORS to allow the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "AI PDF Chat API is running",
    }


@app.post("/documents/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    # 1. Validate file presence and filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Prevent directory traversal by extracting strictly the basename
    safe_filename = os.path.basename(file.filename)

    # 2. Validate PDF file extension
    if not safe_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files are allowed.",
        )

    # 3. Read uploaded file content
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="The uploaded PDF file is empty.",
        )

    # 4. Save file to storage
    file_path = PDF_STORAGE_DIR / safe_filename
    with open(file_path, "wb") as f:
        f.write(content)

    # 5. Extract text page-by-page using PyMuPDF
    try:
        pages = extract_pdf_pages(str(file_path))
    except Exception:
        gc.collect()
        try:
            if file_path.exists():
                file_path.unlink()
        except OSError:
            pass
        raise HTTPException(
            status_code=400,
            detail="Invalid or corrupted PDF file.",
        )

    # 6. Validate extracted pages
    if len(pages) == 0:
        gc.collect()
        try:
            if file_path.exists():
                file_path.unlink()
        except OSError:
            pass
        raise HTTPException(
            status_code=400,
            detail="The uploaded PDF contains no pages.",
        )

    return UploadResponse(
        filename=safe_filename,
        page_count=len(pages),
        pages=pages,
    )
