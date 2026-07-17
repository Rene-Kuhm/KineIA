import asyncio
import os
import sqlite3
from collections.abc import AsyncIterator
from threading import Event, get_ident
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from app.core.ingestion import pipeline
from app.core.ingestion.provenance import SourceProvenance
from app.models.source_ingestion_run import SourceIngestionRun
from app.models.trusted_source import TrustedSource
from app.services import source_ingestion
from app.services.source_ingestion import (
    InactiveSourceError,
    IngestionFailureError,
    ingest_trusted_file,
)
from app.services.trusted_source_registry import register_trusted_source
from qdrant_client.models import (
    Distance,
    Modifier,
    PayloadIndexInfo,
    PayloadSchemaType,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)
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
def enable_dual(case, monkeypatch):
    from app.core.rag import sparse_encoder

    monkeypatch.setattr(pipeline.settings, "qdrant_write_mode", "dual")
    params = SimpleNamespace(vectors={"dense": VectorParams(size=1024, distance=Distance.COSINE)},
                             sparse_vectors={"sparse": SparseVectorParams(modifier=Modifier.IDF)})
    payload = {field: PayloadIndexInfo(data_type=PayloadSchemaType.KEYWORD, points=0)
               for field in ("area", "evidence_level", "source_id")}
    case.client.collection_exists.return_value = True
    case.client.get_collection.return_value = SimpleNamespace(
        config=SimpleNamespace(params=params), payload_schema=payload)
    encoder = MagicMock()
    encoder.encode.return_value = SparseVector(indices=[7], values=[0.7])
    monkeypatch.setattr(sparse_encoder, "SpanishBm25Encoder", lambda: encoder)
    return encoder
async def test_dual_mode_writes_identical_ids_and_payloads_with_named_vectors(case, monkeypatch):
    encoder = enable_dual(case, monkeypatch)
    async with case.factory() as session:
        await ingest_trusted_file(session, str(case.document), case.metadata)
    legacy, hybrid = [call.kwargs for call in case.client.upsert.call_args_list]
    legacy_point, hybrid_point = legacy["points"][0], hybrid["points"][0]
    collections = [pipeline.settings.qdrant_collection, pipeline.settings.qdrant_hybrid_collection]
    assert [legacy["collection_name"], hybrid["collection_name"]] == collections
    assert (legacy_point.id, legacy_point.payload) == (hybrid_point.id, hybrid_point.payload)
    assert hybrid_point.vector == {"dense": legacy_point.vector,
                                   "sparse": SparseVector(indices=[7], values=[0.7])}
    encoder.encode.assert_called_once_with("Evidence.")
    deleted = [call.kwargs["collection_name"] for call in case.client.delete.call_args_list]
    assert deleted == collections
async def test_legacy_mode_never_loads_sparse_encoder_or_calls_hybrid(case, monkeypatch):
    from app.core.rag import sparse_encoder

    constructor = MagicMock(side_effect=AssertionError("sparse encoder loaded"))
    monkeypatch.setattr(sparse_encoder, "SpanishBm25Encoder", constructor)
    monkeypatch.setattr(pipeline.settings, "qdrant_write_mode", "legacy")
    async with case.factory() as session:
        await ingest_trusted_file(session, str(case.document), case.metadata)

    constructor.assert_not_called()
    case.client.collection_exists.assert_not_called()
    case.client.get_collection.assert_not_called()
    collection = pipeline.settings.qdrant_collection
    assert case.client.upsert.call_count == case.client.delete.call_count == 1
    assert case.client.upsert.call_args.kwargs["collection_name"] == collection
    assert case.client.delete.call_args.kwargs["collection_name"] == collection
    assert isinstance(case.client.upsert.call_args.kwargs["points"][0].vector, list)
async def test_empty_cleanup_failure_is_audited_and_never_reports_success(case, monkeypatch):
    case.document.write_text("", encoding="utf-8")
    identity = SourceProvenance.from_content("", case.metadata)
    case.client.delete.side_effect = RuntimeError("cleanup failed")
    async with case.factory() as session:
        with pytest.raises(IngestionFailureError) as failure:
            await ingest_trusted_file(session, str(case.document), case.metadata)
    async with case.factory() as session:
        run = await session.get(SourceIngestionRun, identity.source_version_id)
    condition = case.client.delete.call_args.kwargs["points_selector"].filter.must[0]
    assert failure.value.stage == run.error_stage == "legacy_cleanup"
    assert run.status == "failed" and condition.key == "source_id"
    assert condition.match.value == identity.source_id
    case.client.upsert.assert_not_called()
@pytest.mark.parametrize(
    ("method", "effects", "stage", "upserts", "deletes"),
    [
        ("collection_exists", [False], "hybrid_validate", 0, 0),
        ("upsert", [RuntimeError("legacy")], "legacy_upsert", 1, 0),
        ("delete", [RuntimeError("legacy")], "legacy_cleanup", 1, 1),
        ("upsert", [None, RuntimeError("hybrid")], "hybrid_upsert", 2, 1),
        ("delete", [None, RuntimeError("hybrid")], "hybrid_cleanup", 2, 2),
    ],
)
async def test_dual_stages_fail_independently(
    case, monkeypatch, method, effects, stage, upserts, deletes
):
    enable_dual(case, monkeypatch)
    getattr(case.client, method).side_effect = effects
    async with case.factory() as session:
        with pytest.raises(IngestionFailureError) as failure:
            await ingest_trusted_file(session, str(case.document), case.metadata)
    _source, run = await stored(case)
    assert failure.value.stage == run.error_stage == stage and run.status == "failed"
    assert case.client.upsert.call_count == upserts
    assert case.client.delete.call_count == deletes
@pytest.mark.parametrize(
    ("method", "effects"),
    [
        ("upsert", [None, RuntimeError("hybrid"), None, None]),
        ("delete", [None, RuntimeError("hybrid"), None, None]),
    ],
)
async def test_dual_retry_idempotently_repairs_either_side(case, monkeypatch, method, effects):
    enable_dual(case, monkeypatch)
    getattr(case.client, method).side_effect = effects
    async with case.factory() as session:
        with pytest.raises(IngestionFailureError):
            await ingest_trusted_file(session, str(case.document), case.metadata)
    async with case.factory() as session:
        await ingest_trusted_file(session, str(case.document), case.metadata)
    _source, run = await stored(case)
    ids = [call.kwargs["points"][0].id for call in case.client.upsert.call_args_list]
    assert run.status == "succeeded" and run.attempt_count == 2 and run.error_stage is None
    assert len(set(ids)) == 1

async def test_sqlite_fallback_serializes_without_leaking_locks(case):
    async with case.factory() as first_session, case.factory() as second_session:
        first = source_ingestion._source_lock(first_session, "same-source")
        second = source_ingestion._source_lock(second_session, "same-source")
        async with first:
            waiter = asyncio.create_task(second.__aenter__())
            await asyncio.sleep(0)
            assert not waiter.done()
        await waiter
        await second.__aexit__(None, None, None)
    assert not source_ingestion._LOCAL_LOCKS
@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="PostgreSQL is required")
async def test_postgres_lock_isolated_serializes_and_survives_close_failure(
    case, tmp_path, monkeypatch, caplog,
):
    dsn = os.environ["TEST_DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")
    engine = create_async_engine(os.environ["TEST_DATABASE_URL"], pool_size=1, max_overflow=0)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    enable_dual(case, monkeypatch)
    updated = tmp_path / "updated.md"
    updated.write_text("Updated evidence.", encoding="utf-8")
    entered, release, seen, state = Event(), Event(), [], {}
    def upsert(**kwargs):
        points, collection = kwargs["points"], kwargs["collection_name"]
        text_value = points[0].payload["text"]
        seen.append(text_value)
        if text_value == "Evidence.":
            entered.set()
            release.wait(3)
        state.setdefault(collection, {}).update({point.id: point for point in points})
    def delete(**kwargs):
        collection = kwargs["collection_name"]
        keep = set(kwargs["points_selector"].filter.must_not[0].has_id)
        state[collection] = {key: point for key, point in state[collection].items() if key in keep}
    async def ingest(path, metadata=case.metadata):
        async with factory() as session:
            return await ingest_trusted_file(session, str(path), metadata)
    case.client.upsert.side_effect, case.client.delete.side_effect = upsert, delete
    monitor = await source_ingestion.postgres_connect(dsn)
    first = asyncio.create_task(ingest(case.document))
    assert await asyncio.to_thread(entered.wait, 3)
    second = asyncio.create_task(ingest(updated))
    async with asyncio.timeout(3):
        while True:
            rows = await monitor.fetch("""SELECT l.granted FROM pg_locks l JOIN pg_stat_activity a
                ON a.pid=l.pid WHERE l.locktype='advisory'
                AND a.application_name='kineia-source-ingestion-lock'""")
            if sorted(row["granted"] for row in rows) == [False, True]:
                break
            await asyncio.sleep(0.01)
    first_hash = await monitor.fetchval(
        "SELECT content_hash FROM trusted_sources WHERE source_id=$1", case.identity.source_id
    )
    assert first_hash == case.identity.content_hash and seen == ["Evidence."]
    release.set()
    await asyncio.gather(first, second)
    assert all(len(points) == 1 for points in state.values())
    texts = {next(iter(value.values())).payload["text"] for value in state.values()}
    assert texts == {"Updated evidence."}
    arrived, unblock, pool_seen = Event(), Event(), []
    def block_distinct(**kwargs):
        if kwargs["collection_name"] == pipeline.settings.qdrant_collection:
            pool_seen.append(kwargs["points"][0].payload["source_id"])
            if len(pool_seen) == 2:
                arrived.set()
            unblock.wait(3)
    case.client.upsert.side_effect, case.client.delete.side_effect = block_distinct, None
    tasks = [asyncio.create_task(ingest(case.document, case.metadata | {"source_key": key}))
             for key in ("pool/a", "pool/b")]
    assert await asyncio.to_thread(arrived.wait, 3)
    unblock.set()
    await asyncio.gather(*tasks)
    assert len(set(pool_seen)) == 2
    original, raw = source_ingestion.postgres_connect, await source_ingestion.postgres_connect(dsn)
    class BrokenClose:
        async def execute(self, *args):
            return await raw.execute(*args)
        async def close(self, **_kwargs):
            raise RuntimeError("close-secret")
        def terminate(self):
            raw.terminate()
    broken = BrokenClose()
    async def connect_broken(*_args, **_kwargs):
        return broken
    monkeypatch.setattr(source_ingestion, "postgres_connect", connect_broken)
    async with factory() as session:
        async with source_ingestion._source_lock(session, case.identity.source_id):
            pass
    key = source_ingestion._lock_key(case.identity.source_id)
    assert await monitor.fetchval("SELECT pg_try_advisory_lock($1)", key)
    assert "close-secret" not in caplog.text and case.identity.source_id not in caplog.text
    await monitor.close()
    monkeypatch.setattr(source_ingestion, "postgres_connect", original)
    await engine.dispose()

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
    assert failure.value.stage == "legacy_upsert"
    assert source is not None and run.status == "failed"
    assert run.error_stage == "legacy_upsert" and "secret" not in run.error_stage
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

    assert failed.status == "failed" and failed.error_stage == "legacy_cleanup"
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
    assert failure.value.stage == "legacy_upsert" and "legacy_upsert" in caplog.text
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
