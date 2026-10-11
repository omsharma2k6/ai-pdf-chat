import { useState, useEffect } from "react";
import "./App.css";

function App() {
  const [backendStatus, setBackendStatus] = useState("Checking...");
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("idle"); // idle | uploading | success | error
  const [uploadMessage, setUploadMessage] = useState("");
  const [uploadResult, setUploadResult] = useState(null);

  const checkBackendHealth = async () => {
    try {
      const response = await fetch("http://localhost:8000/health");
      if (response.ok) {
        const data = await response.json();
        if (data.status === "ok") {
          setBackendStatus("Connected");
          return;
        }
      }
      setBackendStatus("Disconnected");
    } catch {
      setBackendStatus("Disconnected");
    }
  };

  useEffect(() => {
    checkBackendHealth();
    const interval = setInterval(checkBackendHealth, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setUploadStatus("idle");
      setUploadMessage("");
      setUploadResult(null);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setUploadStatus("error");
      setUploadMessage("Please select a PDF file first.");
      return;
    }

    if (!selectedFile.name.toLowerCase().endsWith(".pdf")) {
      setUploadStatus("error");
      setUploadMessage("Only PDF files are supported.");
      return;
    }

    setUploadStatus("uploading");
    setUploadMessage("Uploading and extracting text...");

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch("http://localhost:8000/documents/upload", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setUploadStatus("success");
        setUploadMessage("PDF uploaded successfully");
        setUploadResult({
          filename: data.filename,
          page_count: data.page_count,
        });
      } else {
        setUploadStatus("error");
        setUploadMessage(data.detail || "Upload failed.");
      }
    } catch {
      setUploadStatus("error");
      setUploadMessage("Failed to connect to the backend server.");
    }
  };

  return (
    <main className="app-container">
      <div className="card">
        <h1 className="title">AI PDF Chat</h1>
        <p className="description">Ask questions about your PDF documents.</p>

        <div className="status-container">
          <div className="status-badge">
            <span
              className={`status-indicator ${
                backendStatus === "Connected"
                  ? "indicator-connected"
                  : backendStatus === "Disconnected"
                  ? "indicator-disconnected"
                  : "indicator-checking"
              }`}
            ></span>
            <span id="backend-status" className="status-text">
              Backend Status: {backendStatus}
            </span>
          </div>
        </div>

        <section className="upload-section">
          <h2 className="section-title">Upload PDF</h2>

          <form onSubmit={handleUpload} className="upload-form">
            <div className="file-input-wrapper">
              <label htmlFor="pdf-file-input" className="file-input-label">
                Choose PDF
              </label>
              <input
                id="pdf-file-input"
                type="file"
                accept=".pdf,application/pdf"
                onChange={handleFileChange}
                className="file-input-hidden"
              />
              <span className="selected-filename">
                {selectedFile ? selectedFile.name : "No file chosen"}
              </span>
            </div>

            <button
              type="submit"
              disabled={!selectedFile || uploadStatus === "uploading"}
              className="upload-button"
            >
              {uploadStatus === "uploading" ? "Uploading..." : "Upload PDF"}
            </button>
          </form>

          {uploadStatus === "uploading" && (
            <p className="status-message uploading-message">{uploadMessage}</p>
          )}

          {uploadStatus === "error" && (
            <p className="status-message error-message">{uploadMessage}</p>
          )}

          {uploadStatus === "success" && uploadResult && (
            <div className="result-card">
              <p className="success-heading">PDF uploaded successfully</p>
              <div className="result-details">
                <p>
                  <strong>File:</strong> {uploadResult.filename}
                </p>
                <p>
                  <strong>Pages:</strong> {uploadResult.page_count}
                </p>
              </div>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}

export default App;
