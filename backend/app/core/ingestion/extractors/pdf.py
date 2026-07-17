from pathlib import Path


def extract_pdf(file_path: str) -> dict:
    """Extract text from a PDF file."""
    path = Path(file_path)

    try:
        import fitz  # PyMuPDF

        with fitz.open(str(path)) as doc:
            pages = [
                {"page_number": number, "text": page.get_text()}
                for number, page in enumerate(doc, start=1)
            ]
        text = "\n\n".join(page["text"] for page in pages)
    except ImportError:
        raise ImportError(
            "PyMuPDF (fitz) is required for PDF extraction. "
            "Install with: pip install PyMuPDF"
        )

    return {
        "text": text.strip(),
        "pages": pages,
        "metadata": {},
        "source_file": str(path),
        "file_name": path.name,
    }
