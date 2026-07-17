import os
import tempfile
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.api.deps import get_database
from app.config import settings
from app.core.auth.dependencies import require_role
from app.db.qdrant import qdrant_client
from app.models.user import User
from app.services.source_ingestion import (
    InactiveSourceError,
    ingest_trusted_file,
)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class IngestResponse(BaseModel):
    status: str
    chunks: int
    file: str
    title: str


def _save_upload(content: bytes, suffix: str) -> str:
    with tempfile.NamedTemporaryFile(suffix=suffix, prefix="kineia_ingest_", delete=False) as tmp:
        tmp.write(content)
        return tmp.name


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
    reviewer: str = Form(..., min_length=1, pattern=r".*\S.*"),
    review_date: date = Form(...),
    area: str | None = Form(None),
    source_type: str | None = Form(None),
    evidence_level: str | None = Form(None),
    title: str | None = Form(None),
    university: str | None = Form(None),
    author: str | None = Form(None),
    year: int | None = Form(None),
    source_key: str | None = Form(None),
    database: AsyncSession = Depends(get_database),
    current_user: User = Depends(require_role(["admin"])),
):
    """Ingest a document file into the knowledge base.

    Accepts: .pdf, .txt, .md
    Protected: admin role required.
    """
    # Validate file extension
    allowed_extensions = {".pdf", ".txt", ".md", ".markdown"}
    original_filename = (file.filename or "unknown").replace("\\", "/").rsplit("/", 1)[-1]
    suffix = Path(original_filename).suffix.lower()
    if suffix not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Tipo de archivo no soportado: {suffix}. "
                f"Usar: {', '.join(sorted(allowed_extensions))}"
            ),
        )

    # Save uploaded file to a temp location
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Archivo vacío",
        )

    tmp_path = await run_in_threadpool(_save_upload, content, suffix)

    try:
        # Build metadata override
        metadata = {
            "original_source_name": original_filename,
            "original_source_path": original_filename,
            "identity_scope": "upload",
            "reviewer": reviewer.strip(),
            "review_date": review_date.isoformat(),
        }
        if source_key:
            metadata["source_key"] = source_key
        if source_type:
            metadata["source_type"] = source_type
        if area:
            metadata["area"] = area
        if evidence_level:
            metadata["evidence_level"] = evidence_level
        if title:
            metadata["title"] = title
        if university:
            metadata["university"] = university
        if author:
            metadata["author"] = author
        if year:
            metadata["year"] = year

        result = await ingest_trusted_file(database, tmp_path, metadata)
        result["file"] = original_filename

        return {"status": "success", "data": result}
    except InactiveSourceError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Source is inactive",
        ) from None
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid source metadata",
        ) from None
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document ingestion could not be completed",
        ) from None
    finally:
        # Clean up temp file
        try:
            await run_in_threadpool(os.unlink, tmp_path)
        except OSError:
            pass
