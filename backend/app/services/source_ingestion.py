import logging
from datetime import datetime, timezone

from app.core.ingestion.pipeline import (
    cleanup_ingestion,
    prepare_ingestion,
    upsert_ingestion,
)
from app.models.source_ingestion_run import SourceIngestionRun
from app.services.trusted_source_registry import register_trusted_source
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

class InactiveSourceError(ValueError):
    pass


class IngestionFailureError(RuntimeError):
    def __init__(self, stage: str):
        self.stage = stage
        super().__init__("Document ingestion could not be completed")


async def _rollback_safely(session: AsyncSession) -> None:
    try:
        await session.rollback()
    except Exception:
        logger.error("Could not roll back ingestion transaction")


async def _mark_failed(session: AsyncSession, run: SourceIngestionRun, stage: str) -> None:
    run.status, run.error_stage = "failed", stage
    run.completed_at = datetime.now(timezone.utc)
    try:
        await session.commit()
    except Exception:
        await _rollback_safely(session)
        logger.error("Could not persist ingestion failure state for stage %s", stage)


async def ingest_trusted_file(session: AsyncSession, file_path: str, metadata: dict) -> dict:
    prepared = await run_in_threadpool(prepare_ingestion, file_path, metadata)
    if isinstance(prepared, dict):
        return prepared
    try:
        source = await register_trusted_source(session, prepared.provenance)
        if not source.is_active:
            raise InactiveSourceError("Inactive sources cannot be ingested")
        run = await session.get(SourceIngestionRun, prepared.provenance.source_version_id)
        if run is None:
            run = SourceIngestionRun(
                source_version_id=prepared.provenance.source_version_id,
                source_id=prepared.provenance.source_id,
                status="pending",
            )
            session.add(run)
        else:
            run.status = "pending"
            run.attempt_count += 1
            run.error_stage = None
            run.completed_at = None
        await session.commit()
    except Exception as error:
        await _rollback_safely(session)
        if isinstance(error, ValueError):
            raise
        raise IngestionFailureError("sql_prepare") from None

    operations = (("qdrant_upsert", upsert_ingestion), ("qdrant_cleanup", cleanup_ingestion))
    for stage, operation in operations:
        try:
            await run_in_threadpool(operation, prepared)
        except Exception:
            logger.error("Ingestion failed during %s", stage)
            await _mark_failed(session, run, stage)
            raise IngestionFailureError(stage) from None

    run.status, run.completed_at = "succeeded", datetime.now(timezone.utc)
    try:
        await session.commit()
    except Exception:
        await _rollback_safely(session)
        raise IngestionFailureError("sql_finalize") from None
    return prepared.result
