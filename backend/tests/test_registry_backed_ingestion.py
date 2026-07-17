import sqlite3
from collections.abc import AsyncIterator
from threading import get_ident
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from app.core.ingestion import pipeline
from app.core.ingestion.provenance import SourceProvenance
from app.models.source_ingestion_run import SourceIngestionRun
from app.models.trusted_source import TrustedSource
from app.services.source_ingestion import (
    InactiveSourceError,
    IngestionFailureError,
    ingest_trusted_file,
)
from app.services.trusted_source_registry import register_trusted_source
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def case(tmp_path, monkeypatch) -> AsyncIterator[SimpleNamespace]:
    database = tmp_path / "runs.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{database}")
    async with engine.begin() as connection:
        await connection.run_sync(TrustedSource.__table__.create)
        await connection.run_sync(SourceIngestionRun.__table__.create)
    client = MagicMock()
    monkeypatch.setattr(pipeline, "qdrant_client", client)
    monkeypatch.setattr(pipeline, "generate_embeddings", lambda texts: [[0.1] for _ in texts])
    document = tmp_path / "guide.md"
    document.write_text("Evidence.", encoding="utf-8")
    metadata = {
        "source_key": "uploads/guide",
        "original_source_name": "guide.md",
        "original_source_path": "guide.md",
        "reviewer": "Lic. Ana Pérez",
        "review_date": "2026-07-16",
    }
    yield SimpleNamespace(
        factory=async_sessionmaker(engine, expire_on_commit=False),
        database=database,
        client=client,
        document=document,
        metadata=metadata,
        identity=SourceProvenance.from_content("Evidence.", metadata),
    )
    await engine.dispose()


def control_commits(session, fail_on: int | None = None, failure="forced SQL failure") -> list[int]:
    successful = [0]
    original = session.commit
    async def commit():
        if successful[0] + 1 == fail_on:
            raise RuntimeError(failure)
        await original()
        successful[0] += 1

    session.commit = commit
    return successful


async def stored(case):
    async with case.factory() as session:
        source = await session.get(TrustedSource, case.identity.source_id)
        run = await session.get(SourceIngestionRun, case.identity.source_version_id)
    return source, run


async def test_pending_is_durable_before_blocking_stages_run_off_loop(case, monkeypatch):
    main_thread = get_ident()
    worker_threads = []

    def embedding(texts):
        worker_threads.append(get_ident())
        return [[0.1] for _ in texts]

    def qdrant_stage(**_kwargs):
        assert commits == [1]
        with sqlite3.connect(case.database) as database:
            assert database.execute("SELECT status FROM source_ingestion_runs").fetchone() == (
                "pending",
            )
        worker_threads.append(get_ident())

    monkeypatch.setattr(pipeline, "generate_embeddings", embedding)
    case.client.upsert.side_effect = qdrant_stage
    case.client.delete.side_effect = qdrant_stage
    async with case.factory() as session:
        commits = control_commits(session)
        result = await ingest_trusted_file(session, str(case.document), case.metadata)

    source, run = await stored(case)
    assert result["source_version_id"] == case.identity.source_version_id
    assert source is not None and run.status == "succeeded"
    assert commits == [2]
    assert len(worker_threads) == 3 and all(thread != main_thread for thread in worker_threads)


async def test_initial_sql_failure_blocks_qdrant(case):
    async with case.factory() as session:
        control_commits(session, fail_on=1)
        with pytest.raises(IngestionFailureError, match="could not be completed") as failure:
            await ingest_trusted_file(session, str(case.document), case.metadata)
    source, run = await stored(case)
    assert failure.value.stage == "sql_prepare"
    assert source is None and run is None
    case.client.upsert.assert_not_called()
    case.client.delete.assert_not_called()


async def test_upsert_failure_is_sanitized_and_skips_cleanup(case):
    case.client.upsert.side_effect = RuntimeError("password=secret")
    async with case.factory() as session:
        with pytest.raises(IngestionFailureError) as failure:
            await ingest_trusted_file(session, str(case.document), case.metadata)
    source, run = await stored(case)
    assert failure.value.stage == "qdrant_upsert"
    assert source is not None and run.status == "failed"
    assert run.error_stage == "qdrant_upsert" and "secret" not in run.error_stage
    case.client.delete.assert_not_called()


async def test_cleanup_failure_is_auditable_and_retry_converges(case):
    case.client.delete.side_effect = [RuntimeError("cleanup failed"), None]
    async with case.factory() as session:
        with pytest.raises(IngestionFailureError):
            await ingest_trusted_file(session, str(case.document), case.metadata)
    _source, failed = await stored(case)
    async with case.factory() as session:
        result = await ingest_trusted_file(session, str(case.document), case.metadata)
    _source, retried = await stored(case)

    assert failed.status == "failed" and failed.error_stage == "qdrant_cleanup"
    assert result["source_version_id"] == case.identity.source_version_id
    assert retried.status == "succeeded" and retried.attempt_count == 2
    assert retried.error_stage is None
    assert case.client.upsert.call_count == case.client.delete.call_count == 2


async def test_final_sql_failure_leaves_pending_without_success(case):
    async with case.factory() as session:
        control_commits(session, fail_on=2)
        with pytest.raises(IngestionFailureError) as failure:
            await ingest_trusted_file(session, str(case.document), case.metadata)

    source, run = await stored(case)
    assert failure.value.stage == "sql_finalize" and source is not None
    assert run.status == "pending" and run.completed_at is None
    case.client.upsert.assert_called_once()
    case.client.delete.assert_called_once()


async def test_failure_state_commit_failure_preserves_original_stage(case, caplog):
    case.client.upsert.side_effect = RuntimeError("password=q-secret")
    async with case.factory() as session:
        control_commits(session, 2, "password=c-secret")
        session.rollback = AsyncMock(side_effect=RuntimeError("password=r-secret"))
        with pytest.raises(IngestionFailureError) as failure:
            await ingest_trusted_file(session, str(case.document), case.metadata)
    _source, run = await stored(case)
    exposed = caplog.text + str(failure.value)
    assert failure.value.stage == "qdrant_upsert" and "qdrant_upsert" in caplog.text
    assert all(secret not in exposed for secret in ("q-secret", "c-secret", "r-secret"))
    assert run.status == "pending" and run.error_stage is None and session.rollback.await_count == 1


async def test_inactive_source_blocks_qdrant(case):
    async with case.factory() as session:
        source = await register_trusted_source(session, case.identity)
        source.is_active = False
        await session.commit()
    case.client.reset_mock()

    async with case.factory() as session:
        with pytest.raises(InactiveSourceError):
            await ingest_trusted_file(session, str(case.document), case.metadata)

    source, run = await stored(case)
    assert source.is_active is False and run is None
    case.client.upsert.assert_not_called()
    case.client.delete.assert_not_called()
