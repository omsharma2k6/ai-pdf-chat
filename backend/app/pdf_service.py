import pymupdf


def extract_pdf_pages(pdf_path: str) -> list[dict]:
    """
    Open a PDF file, extract text from each page, and return
    a list of page dictionaries with 1-based page numbers.
    """
    pdf = pymupdf.open(pdf_path)
    pages = []

    try:
        for page_index in range(len(pdf)):
            page = pdf[page_index]
            text = page.get_text()
            pages.append({
                "page_number": page_index + 1,
                "text": text,
            })
    finally:
        pdf.close()

    return pages
