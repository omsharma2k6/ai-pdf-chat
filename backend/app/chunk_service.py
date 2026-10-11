"""
Text chunking service for AI PDF Chat System.

Splits extracted PDF pages into manageable character-based chunks with overlap,
preserving page metadata.

Note on Chunking Strategy:
Character-based chunking is a simple baseline implementation for this module.
Character counts are not equivalent to model tokens (in English, 1 token is roughly
4 characters). This character-based sliding window approach provides a transparent,
dependency-free foundation before token-aware chunking or semantic splitting is introduced.
"""

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 150


def create_chunks(
    pages: list[dict],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[dict]:
    """
    Split a list of page objects into text chunks.

    Args:
        pages: List of dictionaries with 'page_number' and 'text'.
               Example: [{"page_number": 1, "text": "..."}]
        chunk_size: Number of characters per chunk (default 1000).
        chunk_overlap: Number of overlapping characters between adjacent chunks (default 150).

    Returns:
        List of chunk dictionaries with 'page_number' and 'text'.
        Example: [{"page_number": 1, "text": "..."}, ...]

    Raises:
        ValueError: If chunk_size <= 0, chunk_overlap < 0, or chunk_overlap >= chunk_size.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be non-negative")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be strictly less than chunk_size")

    chunks = []
    step = chunk_size - chunk_overlap

    for page in pages:
        page_number = page.get("page_number", 1)
        raw_text = page.get("text", "")

        # Skip empty or whitespace-only pages
        if not raw_text or not raw_text.strip():
            continue

        text = raw_text.strip()
        text_length = len(text)

        # For pages with text shorter than or equal to chunk_size, create a single chunk
        if text_length <= chunk_size:
            chunks.append({
                "page_number": page_number,
                "text": text,
            })
            continue

        # For pages longer than chunk_size, apply a sliding window with overlap
        start = 0
        while start < text_length:
            end = min(start + chunk_size, text_length)
            chunk_slice = text[start:end]

            # Avoid chunks that contain only whitespace
            if chunk_slice.strip():
                chunks.append({
                    "page_number": page_number,
                    "text": chunk_slice,
                })

            if end >= text_length:
                break

            # The loop always advances because step = chunk_size - chunk_overlap > 0
            start += step

    return chunks
