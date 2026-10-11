import io
import json
import urllib.request
import urllib.error
from pathlib import Path
import pymupdf

BASE_URL = "http://127.0.0.1:8000"
STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage" / "pdfs"

def create_multipart_body(filename: str, file_bytes: bytes, field_name: str = "file") -> tuple[bytes, str]:
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = io.BytesIO()
    body.write(f"--{boundary}\r\n".encode("utf-8"))
    body.write(f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode("utf-8"))
    body.write(b"Content-Type: application/pdf\r\n\r\n")
    body.write(file_bytes)
    body.write(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    content_type = f"multipart/form-data; boundary={boundary}"
    return body.getvalue(), content_type

def post_file(filename: str, file_bytes: bytes):
    data, content_type = create_multipart_body(filename, file_bytes)
    req = urllib.request.Request(f"{BASE_URL}/documents/upload", data=data, method="POST")
    req.add_header("Content-Type", content_type)
    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            body = json.loads(resp.read().decode("utf-8"))
            return status, body
    except urllib.error.HTTPError as e:
        status = e.code
        try:
            body = json.loads(e.read().decode("utf-8"))
        except Exception:
            body = {"detail": str(e)}
        return status, body

def run_tests():
    print("=== STARTING MODULE 2 BACKEND ACCEPTANCE TESTS ===")
    results = {}

    # Create a 3-page test PDF
    doc = pymupdf.open()
    p1 = doc.new_page()
    p1.insert_text((50, 72), "Operating Systems concepts - Page 1")
    p2 = doc.new_page()
    p2.insert_text((50, 72), "Memory Management and Paging - Page 2")
    p3 = doc.new_page()
    p3.insert_text((50, 72), "Virtual Memory and File Systems - Page 3")
    pdf_bytes = doc.tobytes()
    doc.close()

    # Test 1 & 2: Upload a valid PDF & Verify HTTP success (200)
    status, body = post_file("sample_os.pdf", pdf_bytes)
    print(f"Test 1 & 2 [Valid PDF Upload & HTTP 200]: Status={status}, Body={body}")
    assert status == 200, f"Expected 200, got {status}"
    results["test_1_and_2"] = "PASS"

    # Test 3: Verify PDF is saved in backend/storage/pdfs/
    saved_file = STORAGE_DIR / "sample_os.pdf"
    assert saved_file.exists(), f"File was not saved at {saved_file}"
    assert saved_file.stat().st_size > 0, "Saved file is empty"
    print(f"Test 3 [PDF Saved to Storage]: Exists at {saved_file} with {saved_file.stat().st_size} bytes")
    results["test_3"] = "PASS"

    # Test 4: Verify page count
    page_count = body.get("page_count")
    assert page_count == 3, f"Expected page_count=3, got {page_count}"
    print(f"Test 4 [Page Count]: {page_count} pages")
    results["test_4"] = "PASS"

    # Test 5: Verify page numbers start at 1
    pages = body.get("pages", [])
    assert len(pages) == 3, f"Expected 3 pages, got {len(pages)}"
    assert pages[0]["page_number"] == 1, f"Expected page 1, got {pages[0]['page_number']}"
    assert pages[1]["page_number"] == 2, f"Expected page 2, got {pages[1]['page_number']}"
    assert pages[2]["page_number"] == 3, f"Expected page 3, got {pages[2]['page_number']}"
    print("Test 5 [Page Numbers Start at 1]: Verified [1, 2, 3]")
    results["test_5"] = "PASS"

    # Test 6: Verify extracted text is returned
    assert "Operating Systems concepts" in pages[0]["text"], "Page 1 text missing expected content"
    print(f"Test 6 [Extracted Text Returned]: Page 1 snippet: '{pages[0]['text'].strip()}'")
    results["test_6"] = "PASS"

    # Test 7: Verify multiple pages are extracted correctly
    assert "Memory Management" in pages[1]["text"], "Page 2 text missing"
    assert "Virtual Memory" in pages[2]["text"], "Page 3 text missing"
    print("Test 7 [Multiple Pages Correctly Extracted]: Pages 1, 2, 3 content verified")
    results["test_7"] = "PASS"

    # Test 8: Verify non-PDF upload is rejected (HTTP 400)
    non_pdf_status, non_pdf_body = post_file("notes.txt", b"This is a text file, not a PDF.")
    print(f"Test 8 [Non-PDF Rejected]: Status={non_pdf_status}, Body={non_pdf_body}")
    assert non_pdf_status == 400, f"Expected 400, got {non_pdf_status}"
    results["test_8"] = "PASS"

    # Test 9: Verify invalid / corrupted PDF is handled (HTTP 400)
    corrupt_status, corrupt_body = post_file("corrupt.pdf", b"%PDF-1.4 but corrupted content here...")
    print(f"Test 9 [Invalid PDF Handled]: Status={corrupt_status}, Body={corrupt_body}")
    assert corrupt_status == 400, f"Expected 400, got {corrupt_status}"
    results["test_9"] = "PASS"

    # Test 10: Verify empty PDF behavior (HTTP 400)
    empty_status, empty_body = post_file("empty.pdf", b"")
    print(f"Test 10 [Empty PDF Handled]: Status={empty_status}, Body={empty_body}")
    assert empty_status == 400, f"Expected 400, got {empty_status}"
    results["test_10"] = "PASS"

    # Additional Validation: Scanned / empty-text PDF handling
    doc_empty = pymupdf.open()
    doc_empty.new_page()
    scanned_bytes = doc_empty.tobytes()
    doc_empty.close()
    scanned_status, scanned_body = post_file("scanned_empty.pdf", scanned_bytes)
    print(f"Test 11 [Scanned PDF with No Text]: Status={scanned_status}, Body={scanned_body}")
    assert scanned_status == 200, f"Expected 200, got {scanned_status}"
    assert scanned_body["page_count"] == 1
    assert scanned_body["pages"][0]["text"].strip() == ""
    results["test_11_scanned_pdf"] = "PASS"

    print("\nALL BACKEND ACCEPTANCE TESTS PASSED!")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    run_tests()
