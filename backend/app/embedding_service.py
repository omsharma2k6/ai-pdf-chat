"""
Embedding service for AI PDF Chat System.

Generates dense vector embeddings using the Google Gemini Embeddings API
(model: gemini-embedding-001) via the official google-genai SDK.
"""

import math
import time
from typing import Any
from google import genai
from google.genai import errors

try:
    from app.config import EMBEDDING_MODEL, get_google_api_key
except ImportError:
    from config import EMBEDDING_MODEL, get_google_api_key

MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0
BACKOFF_FACTOR = 2.0
MAX_BATCH_SIZE = 32


def get_genai_client(api_key: str | None = None) -> genai.Client:
    """
    Initialize and return a Google GenAI Client.
    Uses the provided api_key or fetches GOOGLE_API_KEY from environment.
    """
    if api_key is None:
        api_key = get_google_api_key()
    return genai.Client(api_key=api_key)


def _embed_batch_with_retry(
    client: genai.Client,
    texts: list[str],
    model: str = EMBEDDING_MODEL,
    max_retries: int = MAX_RETRIES,
    initial_backoff: float = INITIAL_BACKOFF,
) -> list[list[float]]:
    """
    Call Google Gemini embed_content API for a batch of texts with bounded retry and backoff.

    Validates:
    - Successful response structure
    - Exact matching vector count
    - Non-empty, finite numeric values
    - Consistent embedding dimensions
    """
    attempt = 0
    backoff = initial_backoff

    while attempt <= max_retries:
        try:
            response = client.models.embed_content(
                model=model,
                contents=texts,
            )

            if not response or not hasattr(response, "embeddings") or response.embeddings is None:
                raise ValueError("Malformed response: missing embeddings field from Google API.")

            raw_embeddings = response.embeddings
            if len(raw_embeddings) != len(texts):
                raise ValueError(
                    f"Mismatched vector count from Google API: expected {len(texts)}, received {len(raw_embeddings)}."
                )

            vectors: list[list[float]] = []
            for idx, item in enumerate(raw_embeddings):
                values = getattr(item, "values", None)
                if values is None and isinstance(item, dict):
                    values = item.get("values")

                if values is None or not isinstance(values, (list, tuple)) or len(values) == 0:
                    raise ValueError(f"Malformed or missing embedding vector at index {idx}.")

                if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values):
                    raise ValueError(f"Non-finite or non-numeric values found in embedding vector at index {idx}.")

                vectors.append([float(v) for v in values])

            # Verify dimension consistency across all vectors in batch
            first_dim = len(vectors[0])
            for idx, vec in enumerate(vectors):
                if len(vec) != first_dim:
                    raise ValueError(
                        f"Inconsistent embedding dimensions: vector 0 has {first_dim}, but vector {idx} has {len(vec)}."
                    )

            return vectors

        except (errors.APIError, Exception) as exc:
            # Fatal/Non-retryable HTTP errors (400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found)
            status_code = getattr(exc, "code", None)
            if status_code in (400, 401, 403, 404):
                raise RuntimeError(f"Google Gemini API non-retryable error ({status_code}): {exc}") from exc

            # Validation errors (malformed API response or mismatched count) should fail fast
            if isinstance(exc, ValueError):
                raise

            attempt += 1
            if attempt > max_retries:
                raise RuntimeError(
                    f"Google Gemini API request failed after {max_retries} attempts: {exc}"
                ) from exc

            time.sleep(backoff)
            backoff *= BACKOFF_FACTOR

    raise RuntimeError("Unexpected failure in embedding retry loop.")


def create_embeddings(
    chunks: list[dict],
    client: genai.Client | None = None,
    batch_size: int = MAX_BATCH_SIZE,
    initial_backoff: float = INITIAL_BACKOFF,
) -> list[dict]:
    """
    Generate dense embeddings for a list of text chunks using Google Gemini API.

    Args:
        chunks: List of chunk dictionaries with 'page_number' and 'text'.
                Example: [{"page_number": 1, "text": "Content..."}]
        client: Optional pre-configured genai.Client (useful for unit testing/mocking).
        batch_size: Number of chunks per API request (bounded by API limits, default 32).
        initial_backoff: Initial seconds to wait on transient errors.

    Returns:
        List of dictionaries with 'page_number', 'text', and 'embedding' (list of floats).
    """
    # 1. Handle empty input without making any API request
    if not chunks:
        return []

    # 2. Initialize client if not provided (validates GOOGLE_API_KEY)
    if client is None:
        client = get_genai_client()

    results: list[dict] = []
    expected_dim: int | None = None

    # 3. Process chunks in bounded batches
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        batch_texts = [c["text"] for c in batch]

        vectors = _embed_batch_with_retry(
            client=client,
            texts=batch_texts,
            model=EMBEDDING_MODEL,
            initial_backoff=initial_backoff,
        )

        batch_dim = len(vectors[0])
        if expected_dim is None:
            expected_dim = batch_dim
        elif batch_dim != expected_dim:
            raise ValueError(
                f"Inconsistent embedding dimensions across batches: initial batch had {expected_dim}, "
                f"but subsequent batch has {batch_dim}."
            )

        for chunk, vector in zip(batch, vectors):
            results.append({
                "page_number": chunk["page_number"],
                "text": chunk["text"],
                "embedding": vector,
            })

    return results
