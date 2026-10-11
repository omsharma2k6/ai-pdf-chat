import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR

# Absolute path to backend/.env derived strictly from this file's location
ENV_FILE = BACKEND_DIR / ".env"


def load_environment(override: bool = False) -> None:
    """
    Load environment variables from backend/.env using an absolute path
    derived from config.py's location, independent of the current working directory.
    Never reads from .env.example or fallback directories.
    """
    if ENV_FILE.is_file():
        load_dotenv(dotenv_path=ENV_FILE, override=override)


# Initial load when config module is imported
load_environment()

APP_TITLE = "AI PDF Chat"
APP_DESCRIPTION = "Ask questions about your PDF documents."
APP_VERSION = "0.3.0"

# Allowed origins for CORS (React + Vite development server)
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Directory for storing uploaded PDFs
PDF_STORAGE_DIR = BASE_DIR / "storage" / "pdfs"
PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Embedding Configuration
EMBEDDING_MODEL = "gemini-embedding-001"


def get_google_api_key() -> str:
    """
    Retrieve GOOGLE_API_KEY from environment.
    Ensures load_dotenv() executes before os.getenv("GOOGLE_API_KEY") is evaluated.
    Raises ValueError with a clear actionable message if missing or empty.
    Never prints, logs, or exposes the actual key value.
    """
    # Ensure load_dotenv() executes before evaluating os.getenv("GOOGLE_API_KEY")
    load_environment(override=True)
    key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "GOOGLE_API_KEY is not configured. Please set GOOGLE_API_KEY in backend/.env "
            "to generate embeddings via Google Gemini API."
        )
    return key
