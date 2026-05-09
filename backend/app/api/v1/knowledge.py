import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.core.auth.dependencies import require_role
from app.core.ingestion.pipeline import ingest_file
from app.db.qdrant import qdrant_client
from app.config import settings
from app.models.user import User

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class IngestResponse(BaseModel):
    status: str
    chunks: int
    file: str
    title: str


@router.get("/stats")
async def knowledge_stats(
    current_user: User = Depends(require_role(["admin"])),
):
    """Return Qdrant collection stats: total points, breakdown by area and evidence_level."""

    collection_name = settings.qdrant_collection

    try:
        collection_info = qdrant_client.get_collection(collection_name)
        total_points = collection_info.points_count or 0
    except Exception:
        total_points = 0

    # Aggregate by area and evidence_level using scroll + payload fields
    by_area: dict[str, int] = {}
    by_evidence_level: dict[str, int] = {}

    if total_points > 0:
        offset = None
        while True:
            records, offset = qdrant_client.scroll(
                collection_name=collection_name,
                with_payload=["area", "evidence_level"],
                limit=1000,
                offset=offset,
            )

            for point in records:
                if point.payload:
                    area = point.payload.get("area", "unknown")
                    evidence_level = point.payload.get("evidence_level", "unknown")

                    by_area[area] = by_area.get(area, 0) + 1
                    by_evidence_level[evidence_level] = by_evidence_level.get(evidence_level, 0) + 1

            if offset is None:
                break

    return {
        "status": "success",
        "data": {
            "collection": collection_name,
            "total_points": total_points,
            "by_area": by_area,
            "by_evidence_level": by_evidence_level,
        },
    }


@router.post("/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    area: str = "general",
    source_type: str = "notes",
    evidence_level: str = "notes",
    title: str | None = None,
    university: str | None = None,
    author: str | None = None,
    year: int | None = None,
    current_user: User = Depends(require_role(["admin"])),
):
    """Ingest a document file into the knowledge base.

    Accepts: .pdf, .txt, .md
    Protected: admin role required.
    """
    # Validate file extension
    allowed_extensions = {".pdf", ".txt", ".md", ".markdown"}
    suffix = Path(file.filename or "unknown").suffix.lower()
    if suffix not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no soportado: {suffix}. Usar: {', '.join(sorted(allowed_extensions))}",
        )

    # Save uploaded file to a temp location
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Archivo vacío",
        )

    with tempfile.NamedTemporaryFile(
        suffix=suffix,
        prefix="kineia_ingest_",
        delete=False,
    ) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Build metadata override
        metadata = {
            "source_type": source_type,
            "area": area,
            "evidence_level": evidence_level,
        }
        if title:
            metadata["title"] = title
        if university:
            metadata["university"] = university
        if author:
            metadata["author"] = author
        if year:
            metadata["year"] = year

        result = ingest_file(tmp_path, metadata_override=metadata)

        return {"status": "success", "data": result}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en la ingesta: {str(e)}",
        )
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
