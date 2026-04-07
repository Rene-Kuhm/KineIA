from pathlib import Path


def extract_pdf(file_path: str) -> dict:
    """Extract text from a PDF file."""
    path = Path(file_path)

    try:
        import fitz  # PyMuPDF

        doc = fitz.open(str(path))
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        text = "\n\n".join(text_parts)
    except ImportError:
        raise ImportError(
            "PyMuPDF (fitz) is required for PDF extraction. "
            "Install with: pip install PyMuPDF"
        )

    return {
        "text": text.strip(),
        "metadata": {},
        "source_file": str(path),
        "file_name": path.name,
    }
