from pathlib import Path

APP_TITLE = "AI PDF Chat"
APP_DESCRIPTION = "Ask questions about your PDF documents."
APP_VERSION = "0.2.0"

# Allowed origins for CORS (React + Vite development server)
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Directory for storing uploaded PDFs
BASE_DIR = Path(__file__).resolve().parent.parent
PDF_STORAGE_DIR = BASE_DIR / "storage" / "pdfs"
PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
