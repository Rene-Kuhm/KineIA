import hashlib
import uuid
from dataclasses import dataclass
from pathlib import Path

from qdrant_client.models import (
    FieldCondition,
    Filter,
    FilterSelector,
    HasIdCondition,
    MatchValue,
    PointStruct,
)

from app.config import settings
from app.core.ingestion.chunker import chunk_text
from app.core.ingestion.embedder import generate_embeddings
from app.core.ingestion.extractors.markdown import extract_markdown
from app.core.ingestion.extractors.pdf import extract_pdf
from app.core.ingestion.extractors.text import extract_text
from app.core.ingestion.provenance import SourceProvenance
from app.db.qdrant import qdrant_client

EXTRACTORS = {
    ".md": extract_markdown,
    ".markdown": extract_markdown,
    ".pdf": extract_pdf,
    ".txt": extract_text,
}


@dataclass(frozen=True)
class PreparedIngestion:
    points: list[PointStruct]
    provenance: SourceProvenance
    result: dict


def _original_source_path(path: Path) -> str:
    resolved = path.resolve()
    repository = next((parent for parent in resolved.parents if (parent / ".git").exists()), None)
    return resolved.relative_to(repository).as_posix() if repository else str(path)


def prepare_ingestion(
    file_path: str, metadata_override: dict | None = None
) -> PreparedIngestion | dict:
    """Extract, chunk, and embed a file without mutating Qdrant."""
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

    file_metadata.setdefault("original_source_name", extracted.get("file_name", path.name))
    file_metadata.setdefault("original_source_path", _original_source_path(path))
    provenance = SourceProvenance.from_content(text, file_metadata)

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
        chunk_hash = hashlib.sha256(chunk["text"].encode("utf-8")).hexdigest()
        point_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"kineia:{provenance.source_version_id}:{i}:{chunk_hash}",
            )
        )
        payload = provenance.payload() | {
            "text": chunk["text"],
            "header": chunk.get("header", ""),
            "chunk_index": i,
            "source_file": provenance.original_source_path,
            "file_name": provenance.original_source_name,
            "title": file_metadata.get("title", path.stem),
        }
        if file_metadata.get("university"):
            payload["university"] = file_metadata["university"]
        points.append(PointStruct(id=point_id, vector=embedding, payload=payload))

    result = {
        "status": "success",
        "chunks": len(chunks),
        "file": provenance.original_source_path,
        "title": file_metadata.get("title", path.stem),
        "source_id": provenance.source_id,
        "source_version": provenance.source_version,
        "source_version_id": provenance.source_version_id,
        "content_hash": provenance.content_hash,
    }
    return PreparedIngestion(points=points, provenance=provenance, result=result)


def upsert_ingestion(prepared: PreparedIngestion) -> None:
    qdrant_client.upsert(
        collection_name=settings.qdrant_collection,
        points=prepared.points,
        wait=True,
    )


def cleanup_ingestion(prepared: PreparedIngestion) -> None:
    qdrant_client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="source_id",
                        match=MatchValue(value=prepared.provenance.source_id),
                    )
                ],
                must_not=[
                    HasIdCondition(has_id=[point.id for point in prepared.points])
                ],
            )
        ),
        wait=True,
    )


def ingest_file(file_path: str, metadata_override: dict | None = None) -> dict:
    """Full ingestion pipeline: extract → chunk → embed → upsert to Qdrant."""
    prepared = prepare_ingestion(file_path, metadata_override)
    if isinstance(prepared, dict):
        return prepared
    upsert_ingestion(prepared)
    cleanup_ingestion(prepared)
    return prepared.result


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
