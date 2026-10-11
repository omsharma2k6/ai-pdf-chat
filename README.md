# AI PDF Chat

## Project Purpose
AI PDF Chat is a college project designed to allow users to ask questions and have conversational interactions with their PDF documents.

> **Current Status**:
> - **Module 1 — Project Foundation**: Completed
> - **Module 2 — PDF Upload + Text Extraction**: Completed
> - **Module 3+ — Embeddings, Vector Storage, RAG / Chat**: Not started (pending review)

---

## Technology Stack

### Backend
- **Language**: Python 3.11
- **Framework**: FastAPI
- **Server**: Uvicorn
- **Validation / Schemas**: Pydantic
- **PDF Processing**: PyMuPDF (`pymupdf`)
- **Multipart Form Support**: `python-multipart`

### Frontend
- **Library**: React 19
- **Build Tool**: Vite
- **Language**: JavaScript
- **Styling**: Vanilla CSS

---

## Project Structure

```text
ai-pdf-chat/
    frontend/
        src/
            App.css
            App.jsx
            index.css
            main.jsx
        index.html
        package.json
        vite.config.js
    backend/
        app/
            __init__.py
            config.py
            main.py
            pdf_service.py
            schemas.py
        storage/
            pdfs/
                .gitkeep
        tests/
            test_module2.py
        requirements.txt
        venv/
    .gitignore
    README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Health check endpoint returning API operational status |
| `POST` | `/documents/upload` | Upload a PDF file, save to storage, and extract text page-by-page |

---

## How to Run the Backend

1. Open a terminal and navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Activate the Python 3.11 virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (CMD)**:
     ```cmd
     .\venv\Scripts\activate.bat
     ```
   - **Linux / macOS**:
     ```bash
     source venv/bin/activate
     ```

3. (If not already installed) Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

5. The API will be available at:
   - Health endpoint: [http://localhost:8000/health](http://localhost:8000/health)
   - Interactive Swagger docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## How to Run the Frontend

1. Open a new terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```

2. (If not already installed) Install dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```

4. Open the frontend in your browser:
   - [http://localhost:5173](http://localhost:5173)

---

## Module Status
- **Module 1**: Project Foundation — Completed (FastAPI backend with `/health` check, CORS configuration, React + Vite frontend with live status checking).
- **Module 2**: PDF Upload + Text Extraction — Completed (File upload, safe storage in `backend/storage/pdfs/`, page-by-page text extraction with 1-based indexing using PyMuPDF, upload UI with file selection, status, and page count display).
- **Module 3+**: Embeddings, Vector Database, RAG / Chat Integration — Not started (pending review).
