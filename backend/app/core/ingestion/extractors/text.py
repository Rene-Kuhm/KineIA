from pathlib import Path


def extract_text(file_path: str) -> dict:
    """Extract text from a plain text file."""
    path = Path(file_path)
    content = path.read_text(encoding="utf-8")

    return {
        "text": content.strip(),
        "metadata": {},
        "source_file": str(path),
        "file_name": path.name,
    }
