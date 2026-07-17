import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from hashlib import blake2b
from threading import Lock
from weakref import WeakValueDictionary

from app.core.ingestion.pipeline import (
    ingestion_operations,
    prepare_ingestion,
)
from app.models.source_ingestion_run import SourceIngestionRun
from app.services.trusted_source_registry import register_trusted_source
from asyncpg import connect as postgres_connect
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)
_LOCAL_LOCKS: WeakValueDictionary[int, asyncio.Lock] = WeakValueDictionary()
_LOCAL_LOCKS_GUARD = Lock()

class InactiveSourceError(ValueError):
    pass


class IngestionFailureError(RuntimeError):
    def __init__(self, stage: str):
        self.stage = stage
        super().__init__("Document ingestion could not be completed")


def _lock_key(source_id: str) -> int:
    return int.from_bytes(blake2b(source_id.encode(), digest_size=8).digest(), "big", signed=True)


def _local_lock(key: int) -> asyncio.Lock:
    with _LOCAL_LOCKS_GUARD:
        return _LOCAL_LOCKS.setdefault(key, asyncio.Lock())


async def _close_postgres_lock(connection) -> None:
    try:
        await connection.close(timeout=2)
    except BaseException:
        try:
            connection.terminate()
        except Exception:
            logger.error("Could not terminate ingestion coordination connection")
        logger.error("Could not close ingestion coordination connection")


@asynccontextmanager
async def _source_lock(session: AsyncSession, source_id: str):
    key = _lock_key(source_id)
    if session.get_bind().dialect.name != "postgresql":
        async with _local_lock(key):
            yield
        return
    connection = None
    try:
        url = session.get_bind().url.set(drivername="postgresql")
        connection = await postgres_connect(
            url.render_as_string(hide_password=False),
            server_settings={"application_name": "kineia-source-ingestion-lock"},
        )
        await connection.execute("SELECT pg_advisory_lock($1)", key)
    except BaseException as error:
        if connection is not None:
            await asyncio.shield(_close_postgres_lock(connection))
        if isinstance(error, Exception):
            logger.error("Could not acquire ingestion coordination lock")
            raise IngestionFailureError("source_lock") from None
        raise
    try:
        yield
    finally:
        await asyncio.shield(_close_postgres_lock(connection))


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
    async with _source_lock(session, prepared.provenance.source_id):
        return await _ingest_prepared(session, prepared)


async def _ingest_prepared(session: AsyncSession, prepared) -> dict:
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

    for stage, operation in ingestion_operations(prepared):
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
