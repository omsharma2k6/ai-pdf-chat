"""
Module 3 Test Suite: Text Chunking and Google Gemini API Embeddings.

Features:
- Full offline unit test suite using mocked Google GenAI API responses (zero network calls, zero quota consumption).
- Explicit, opt-in live API integration test that only executes when --live flag is passed.
- Security-safe: Never logs, displays, or exposes API keys or authorization headers.
"""

import math
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Ensure backend root is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.chunk_service import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, create_chunks
from app.config import get_google_api_key
from app.embedding_service import create_embeddings
from google.genai import errors


class MockEmbedding:
    """Mock object mimicking google.genai.types.ContentEmbedding."""
    def __init__(self, values: list[float]):
        self.values = values


class MockEmbedContentResponse:
    """Mock object mimicking google.genai.types.EmbedContentResponse."""
    def __init__(self, embeddings: list[MockEmbedding]):
        self.embeddings = embeddings


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Calculate cosine similarity between two numeric vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def run_unit_tests() -> dict:
    print("==================================================")
    print("Module 3 Unit Tests (Chunking & Mocked Embeddings)")
    print("==================================================")
    results = {}

    # Safety Guard: Ensure ordinary unit tests cannot accidentally call the real Google API
    import app.embedding_service
    real_get_genai_client = app.embedding_service.get_genai_client

    def safety_blocked_client(*args, **kwargs):
        raise AssertionError(
            "CRITICAL SAFETY CHECK: Live Google GenAI client instantiation is forbidden during unit tests!"
        )

    app.embedding_service.get_genai_client = safety_blocked_client

    try:
        # ----------------------------------------------------
        # Chunking Tests (1 - 6)
        # ----------------------------------------------------

        # Verify default constants
        assert DEFAULT_CHUNK_SIZE == 1000, f"Expected default chunk size 1000, got {DEFAULT_CHUNK_SIZE}"
        assert DEFAULT_CHUNK_OVERLAP == 150, f"Expected default chunk overlap 150, got {DEFAULT_CHUNK_OVERLAP}"

        # Test 1: Short text produces one chunk
        short_pages = [{"page_number": 1, "text": "This is a brief single-page document."}]
        short_chunks = create_chunks(short_pages)
        assert len(short_chunks) == 1, f"Expected 1 chunk, got {len(short_chunks)}"
        assert short_chunks[0]["text"] == "This is a brief single-page document."
        assert short_chunks[0]["page_number"] == 1
        results["1_short_text_produces_one_chunk"] = "PASS"
        print("1. Short text produces one chunk: PASS")

        # Test 2: Long text creates multiple chunks
        long_text = "Operating systems manage computer hardware and software resources. " * 30
        long_pages = [{"page_number": 1, "text": long_text}]
        long_chunks = create_chunks(long_pages, chunk_size=500, chunk_overlap=100)
        assert len(long_chunks) > 1, f"Expected multiple chunks, got {len(long_chunks)}"
        results["2_long_text_creates_multiple_chunks"] = f"PASS ({len(long_chunks)} chunks)"
        print(f"2. Long text creates multiple chunks: PASS ({len(long_chunks)} chunks)")

        # Test 3: Adjacent chunks have expected overlap under default configuration (1,000 size, 150 overlap)
        # A. Default configuration test (no parameters passed to create_chunks)
        default_text = "".join(f"token_{i:04d}_" for i in range(300))  # ~3,300 chars
        d_pages = [{"page_number": 1, "text": default_text}]
        d_chunks = create_chunks(d_pages)  # Uses default chunk_size=1000, chunk_overlap=150
        assert len(d_chunks) >= 2, "Need at least 2 chunks to verify default overlap"
        assert len(d_chunks[0]["text"]) == 1000, (
            f"Expected default first chunk length 1000, got {len(d_chunks[0]['text'])}"
        )
        d_tail = d_chunks[0]["text"][-150:]
        d_head = d_chunks[1]["text"][:150]
        assert len(d_tail) == 150, f"Expected overlap length 150, got {len(d_tail)}"
        assert d_head == d_tail, f"Expected default 150-char overlap '{d_tail}', got '{d_head}'"

        # B. Default configuration test with natural prose text
        prose_paragraph = (
            "Artificial intelligence is transforming software engineering, education, and research. "
            "Natural language processing allows computers to understand, interpret, and manipulate human language. "
            "Retrieval augmented generation enhances large language models by retrieving authoritative documents. "
            "Vector embeddings translate textual semantics into continuous geometric coordinates in dense vector spaces. "
        ) * 6  # ~2,400 chars
        prose_pages = [{"page_number": 1, "text": prose_paragraph}]
        prose_chunks = create_chunks(prose_pages)  # Default config (1000 size, 150 overlap)
        assert len(prose_chunks) >= 2
        assert len(prose_chunks[0]["text"]) == 1000
        p_tail = prose_chunks[0]["text"][-150:]
        p_head = prose_chunks[1]["text"][:150]
        assert len(p_tail) == 150, f"Expected 150 characters tail, got {len(p_tail)}"
        assert p_head == p_tail, "Prose text default 150-character overlap mismatch"

        # C. Custom configuration test
        continuous_text = "".join(f"item_{i:04d}_" for i in range(200))
        c_pages = [{"page_number": 1, "text": continuous_text}]
        overlap_val = 100
        chunk_size_val = 400
        c_chunks = create_chunks(c_pages, chunk_size=chunk_size_val, chunk_overlap=overlap_val)
        assert len(c_chunks) >= 2, "Need at least 2 chunks to verify custom overlap"
        tail_c0 = c_chunks[0]["text"][-overlap_val:]
        head_c1 = c_chunks[1]["text"][:overlap_val]
        assert head_c1 == tail_c0, f"Expected custom overlap '{tail_c0}', got '{head_c1}'"
        results["3_adjacent_chunks_have_expected_overlap"] = "PASS (default 150-char and custom 100-char verified)"
        print("3. Adjacent chunks have expected overlap (default 150-char & custom verified): PASS")

        # Test 4: Page numbers are preserved
        for c in long_chunks:
            assert c["page_number"] == 1, f"Expected page_number=1, got {c['page_number']}"
        results["4_page_numbers_preserved"] = "PASS"
        print("4. Page numbers are preserved: PASS")

        # Test 5: Different pages remain separate
        diff_pages = [
            {"page_number": 1, "text": "Page one text content."},
            {"page_number": 2, "text": "Page two text content."},
        ]
        diff_chunks = create_chunks(diff_pages)
        assert len(diff_chunks) == 2, f"Expected 2 chunks, got {len(diff_chunks)}"
        assert diff_chunks[0]["page_number"] == 1 and diff_chunks[0]["text"] == "Page one text content."
        assert diff_chunks[1]["page_number"] == 2 and diff_chunks[1]["text"] == "Page two text content."
        results["5_different_pages_remain_separate"] = "PASS"
        print("5. Different pages remain separate: PASS")

        # Test 6: Empty and whitespace-only pages are skipped
        empty_ws_pages = [
            {"page_number": 1, "text": ""},
            {"page_number": 2, "text": "   \n\t  \r  "},
            {"page_number": 3, "text": "Valid page text."},
        ]
        filtered_chunks = create_chunks(empty_ws_pages)
        assert len(filtered_chunks) == 1, f"Expected 1 chunk, got {len(filtered_chunks)}"
        assert filtered_chunks[0]["page_number"] == 3
        results["6_empty_and_whitespace_pages_skipped"] = "PASS"
        print("6. Empty and whitespace-only pages are skipped: PASS")

        # ----------------------------------------------------
        # Mocked Embeddings Tests (7 - 14)
        # ----------------------------------------------------

        # Test 7: Empty input produces no API request
        mock_client = MagicMock()
        empty_result = create_embeddings([], client=mock_client)
        assert empty_result == [], f"Expected [], got {empty_result}"
        mock_client.models.embed_content.assert_not_called()
        results["7_empty_input_produces_no_api_request"] = "PASS"
        print("7. Empty input produces no API request: PASS")

        # Test 8: Mocked embeddings are correctly associated with source chunks
        test_dim = 768
        vector_a = [0.1] * test_dim
        vector_b = [0.2] * test_dim
        mock_client.models.embed_content.return_value = MockEmbedContentResponse([
            MockEmbedding(vector_a),
            MockEmbedding(vector_b),
        ])

        sample_chunks = [
            {"page_number": 1, "text": "First chunk text"},
            {"page_number": 2, "text": "Second chunk text"},
        ]
        embedded_output = create_embeddings(sample_chunks, client=mock_client)
        assert len(embedded_output) == 2, f"Expected 2 outputs, got {len(embedded_output)}"
        assert embedded_output[0]["page_number"] == 1
        assert embedded_output[0]["text"] == "First chunk text"
        assert embedded_output[0]["embedding"] == vector_a
        assert embedded_output[1]["page_number"] == 2
        assert embedded_output[1]["text"] == "Second chunk text"
        assert embedded_output[1]["embedding"] == vector_b
        results["8_mocked_embeddings_correctly_associated"] = "PASS"
        print("8. Mocked embeddings correctly associated with source chunks: PASS")

        # Test 9: All vectors have consistent dimension (dynamically validated without assuming live API dimension)
        for item in embedded_output:
            assert len(item["embedding"]) == test_dim, f"Expected consistent dim {test_dim}, got {len(item['embedding'])}"

        # Cross-batch dimension consistency check
        batch_mismatch_client = MagicMock()
        batch_mismatch_client.models.embed_content.side_effect = [
            MockEmbedContentResponse([MockEmbedding([0.1] * 768)]),
            MockEmbedContentResponse([MockEmbedding([0.1] * 512)]),
        ]
        try:
            create_embeddings(
                [{"page_number": 1, "text": "b1"}, {"page_number": 1, "text": "b2"}],
                client=batch_mismatch_client,
                batch_size=1,
            )
            assert False, "Expected ValueError on cross-batch dimension mismatch"
        except ValueError as dim_err:
            assert "Inconsistent embedding dimensions across batches" in str(dim_err)

        results["9_consistent_dimension"] = "PASS (intra-batch and cross-batch consistency validated)"
        print("9. Vectors have consistent dimensions (intra-batch & cross-batch validated): PASS")

        # Test 10: Vector elements are finite numeric values
        for item in embedded_output:
            assert all(math.isfinite(x) for x in item["embedding"]), "Found non-finite vector element"
        results["10_vector_elements_finite"] = "PASS"
        print("10. Vector elements are finite numeric values: PASS")

        # Test 11: Configuration loading and missing API key handling
        from unittest.mock import patch
        from app.config import ENV_FILE, BACKEND_DIR

        # A. Verify ENV_FILE is strictly absolute and derived from config.py location
        assert ENV_FILE.is_absolute(), f"ENV_FILE must be an absolute path, got {ENV_FILE}"
        assert ENV_FILE == BACKEND_DIR / ".env", f"ENV_FILE must point to backend/.env, got {ENV_FILE}"
        assert ENV_FILE.name == ".env", f"ENV_FILE must be named .env, not .env.example"

        # B. Verify load_environment executes before evaluating os.getenv
        with patch("app.config.load_dotenv") as mock_load_dotenv, patch.dict(os.environ, {"GOOGLE_API_KEY": "dummy_value"}):
            loaded_key = get_google_api_key()
            assert loaded_key == "dummy_value"
            mock_load_dotenv.assert_called_with(dotenv_path=ENV_FILE, override=True)

        # C. Verify missing or empty key raises a clear ValueError
        with patch("app.config.load_environment"), patch.dict(os.environ, {"GOOGLE_API_KEY": ""}):
            try:
                get_google_api_key()
                assert False, "Expected ValueError when GOOGLE_API_KEY is empty"
            except ValueError as err:
                assert "GOOGLE_API_KEY is not configured" in str(err)

        results["11_configuration_loading_and_missing_api_key"] = "PASS"
        print("11. Configuration loading and missing API key validation: PASS")

        # Test 12: Authentication, rate-limit, network and other API errors handled properly
        # Non-retryable authentication error (HTTP 401)
        auth_client = MagicMock()
        auth_error = errors.APIError(401, {"error": {"message": "Invalid API Key"}})
        auth_client.models.embed_content.side_effect = auth_error
        try:
            create_embeddings([{"page_number": 1, "text": "text"}], client=auth_client, initial_backoff=0.001)
            assert False, "Expected RuntimeError on 401"
        except RuntimeError as r_err:
            assert "non-retryable error (401)" in str(r_err)
        assert auth_client.models.embed_content.call_count == 1, "Non-retryable 401 should not be retried"

        # Retryable rate limit error (HTTP 429) that fails after retries
        rate_client = MagicMock()
        rate_error = errors.APIError(429, {"error": {"message": "Resource Exhausted"}})
        rate_client.models.embed_content.side_effect = rate_error
        try:
            create_embeddings([{"page_number": 1, "text": "text"}], client=rate_client, initial_backoff=0.001)
            assert False, "Expected RuntimeError after retries"
        except RuntimeError as r_err:
            assert "failed after 3 attempts" in str(r_err)
        assert rate_client.models.embed_content.call_count == 4, f"Expected 4 attempts, got {rate_client.models.embed_content.call_count}"

        # Transient network error that recovers on second attempt
        net_recover_client = MagicMock()
        net_recover_client.models.embed_content.side_effect = [
            ConnectionResetError("Connection dropped by remote server"),
            MockEmbedContentResponse([MockEmbedding([0.4] * 768)]),
        ]
        net_rec_output = create_embeddings(
            [{"page_number": 1, "text": "network recovery chunk"}],
            client=net_recover_client,
            initial_backoff=0.001,
        )
        assert len(net_rec_output) == 1
        assert net_recover_client.models.embed_content.call_count == 2

        # Persistent network error that exhausts retries
        net_fail_client = MagicMock()
        net_fail_client.models.embed_content.side_effect = ConnectionError("Persistent network outage")
        try:
            create_embeddings(
                [{"page_number": 1, "text": "network failure chunk"}],
                client=net_fail_client,
                initial_backoff=0.001,
            )
            assert False, "Expected RuntimeError on persistent network outage"
        except RuntimeError as net_err:
            assert "failed after 3 attempts" in str(net_err)
        assert net_fail_client.models.embed_content.call_count == 4

        results["12_api_errors_and_retries_handled"] = "PASS"
        print("12. Authentication (fail fast), rate-limit, and network errors (bounded retry) handled: PASS")

        # Test 13: Malformed API responses and mismatched vector counts are rejected
        # Case A: Mismatched vector count
        mismatch_client = MagicMock()
        mismatch_client.models.embed_content.return_value = MockEmbedContentResponse([
            MockEmbedding([0.1, 0.2]),
        ])
        try:
            create_embeddings([
                {"page_number": 1, "text": "chunk1"},
                {"page_number": 1, "text": "chunk2"},
            ], client=mismatch_client)
            assert False, "Expected ValueError on mismatched count"
        except ValueError as v_err:
            assert "Mismatched vector count" in str(v_err)

        # Case B: Non-finite values in vector
        nonfinite_client = MagicMock()
        nonfinite_client.models.embed_content.return_value = MockEmbedContentResponse([
            MockEmbedding([0.1, float("nan")]),
        ])
        try:
            create_embeddings([{"page_number": 1, "text": "chunk1"}], client=nonfinite_client)
            assert False, "Expected ValueError on NaN vector"
        except ValueError as v_err:
            assert "Non-finite or non-numeric" in str(v_err)

        # Case C: Inconsistent dimensions across vectors
        inconsistent_client = MagicMock()
        inconsistent_client.models.embed_content.return_value = MockEmbedContentResponse([
            MockEmbedding([0.1, 0.2, 0.3]),
            MockEmbedding([0.1, 0.2]),
        ])
        try:
            create_embeddings([
                {"page_number": 1, "text": "chunk1"},
                {"page_number": 1, "text": "chunk2"},
            ], client=inconsistent_client)
            assert False, "Expected ValueError on inconsistent dimensions"
        except ValueError as v_err:
            assert "Inconsistent embedding dimensions" in str(v_err)

        results["13_malformed_and_mismatched_responses_rejected"] = "PASS"
        print("13. Malformed API responses and mismatched vector counts rejected: PASS")

        # Test 14: Safety guard confirms ordinary unit tests cannot accidentally call the real Google API
        try:
            create_embeddings([{"page_number": 1, "text": "accidental real call"}])
            assert False, "Expected safety guard to block unmocked client access in unit tests"
        except AssertionError as safety_err:
            assert "Live Google GenAI client instantiation is forbidden during unit tests" in str(safety_err)
        results["14_unit_tests_cannot_call_real_api"] = "PASS"
        print("14. Unit test safety guard (accidental live API call prevention): PASS")

    finally:
        # Restore original client getter
        app.embedding_service.get_genai_client = real_get_genai_client

    print("\nALL 14 MODULE 3 UNIT TESTS PASSED!")
    return results


def run_live_integration_test() -> dict:
    """
    Opt-in live integration test that calls Google Gemini API.
    Runs ONLY when explicitly invoked with --live flag.
    Never prints or logs the API key.
    """
    print("\n==================================================")
    print("OPT-IN LIVE INTEGRATION TEST (Google Gemini API)")
    print("==================================================")

    try:
        # Validate that the API key is present in environment without exposing it
        get_google_api_key()
    except ValueError as err:
        print(f"Skipping live test: {err}")
        return {"status": "SKIPPED", "reason": "No API key configured"}

    sentence_a = "Operating systems manage computer hardware and software resources."
    sentence_b = "An operating system controls hardware resources and provides services to applications."
    sentence_c = "Bananas are a type of fruit."

    chunks = [
        {"page_number": 1, "text": sentence_a},
        {"page_number": 1, "text": sentence_b},
        {"page_number": 1, "text": sentence_c},
    ]

    print("Sending live embedding request to Google Gemini API (model: gemini-embedding-001)...")
    results = create_embeddings(chunks)

    assert len(results) == 3, f"Expected 3 embeddings, got {len(results)}"
    dim = len(results[0]["embedding"])
    print(f"Live embedding generated successfully! Output dimension: {dim}")

    vec_a = results[0]["embedding"]
    vec_b = results[1]["embedding"]
    vec_c = results[2]["embedding"]

    sim_ab = cosine_similarity(vec_a, vec_b)
    sim_ac = cosine_similarity(vec_a, vec_c)

    print(f"Cosine Similarity (A, B) [Related]:   {sim_ab:.4f}")
    print(f"Cosine Similarity (A, C) [Unrelated]: {sim_ac:.4f}")

    assert sim_ab > sim_ac, f"Expected similarity(A,B) > similarity(A,C), got {sim_ab:.4f} <= {sim_ac:.4f}"
    print("Semantic similarity verification: PASS (A,B > A,C)")

    return {
        "status": "PASS",
        "dimension": dim,
        "similarity_ab": round(sim_ab, 4),
        "similarity_ac": round(sim_ac, 4),
    }


def main():
    unit_results = run_unit_tests()

    live_results = None
    if "--live" in sys.argv or os.getenv("RUN_LIVE_TEST") == "1":
        live_results = run_live_integration_test()
    else:
        print("\nNote: Live API integration test was not run. Use '--live' to explicitly run it.")

    return {
        "unit_tests": unit_results,
        "live_test": live_results,
    }


if __name__ == "__main__":
    main()
