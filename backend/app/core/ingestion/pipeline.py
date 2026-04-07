import uuid
from pathlib import Path

from qdrant_client.models import PointStruct

from app.config import settings
from app.core.ingestion.chunker import chunk_text
from app.core.ingestion.embedder import generate_embeddings
from app.core.ingestion.extractors.markdown import extract_markdown
from app.core.ingestion.extractors.pdf import extract_pdf
from app.core.ingestion.extractors.text import extract_text
from app.db.qdrant import qdrant_client

EXTRACTORS = {
    ".md": extract_markdown,
    ".markdown": extract_markdown,
    ".pdf": extract_pdf,
    ".txt": extract_text,
}


def ingest_file(file_path: str, metadata_override: dict | None = None) -> dict:
    """Full ingestion pipeline: extract → chunk → embed → upsert to Qdrant."""
    path = Path(file_path)

    # 1. Extract
    extractor = EXTRACTORS.get(path.suffix.lower())
    if not extractor:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    extracted = extractor(file_path)
    text = extracted["text"]
    file_metadata = extracted["metadata"]

    if metadata_override:
        file_metadata.update(metadata_override)

    # 2. Chunk
    chunks = chunk_text(
        text,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    if not chunks:
        return {"status": "empty", "chunks": 0, "file": file_path}

    # 3. Embed
    chunk_texts = [c["text"] for c in chunks]
    embeddings = generate_embeddings(chunk_texts)

    # 4. Build points for Qdrant
    points = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        point_id = str(uuid.uuid4())
        payload = {
            "text": chunk["text"],
            "header": chunk.get("header", ""),
            "chunk_index": i,
            "source_file": str(path),
            "file_name": path.name,
            "title": file_metadata.get("title", path.stem),
            "source_type": file_metadata.get("source_type", "notes"),
            "area": file_metadata.get("area", "general"),
            "university": file_metadata.get("university", ""),
            "author": file_metadata.get("author", ""),
            "year": file_metadata.get("year", 0),
            "evidence_level": file_metadata.get("evidence_level", "notes"),
        }
        points.append(PointStruct(id=point_id, vector=embedding, payload=payload))

    # 5. Upsert to Qdrant
    qdrant_client.upsert(
        collection_name=settings.qdrant_collection,
        points=points,
    )

    return {
        "status": "success",
        "chunks": len(chunks),
        "file": file_path,
        "title": file_metadata.get("title", path.stem),
    }


def ingest_directory(directory: str, recursive: bool = True) -> list[dict]:
    """Ingest all supported files from a directory."""
    path = Path(directory)
    results = []

    glob_pattern = "**/*" if recursive else "*"
    for file_path in sorted(path.glob(glob_pattern)):
        if file_path.suffix.lower() in EXTRACTORS and file_path.is_file():
            try:
                result = ingest_file(str(file_path))
                results.append(result)
                print(f"✅ {result['title']}: {result['chunks']} chunks")
            except Exception as e:
                results.append({
                    "status": "error",
                    "file": str(file_path),
                    "error": str(e),
                })
                print(f"❌ {file_path.name}: {e}")

    return results
