import asyncio
import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from app.core.ingestion.provenance import SourceProvenance
from app.models.trusted_source import TrustedSource
from app.services.trusted_source_registry import get_trusted_source, register_trusted_source
from sqlalchemy import delete, event, func, select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

pytestmark = pytest.mark.asyncio
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@pytest_asyncio.fixture
async def postgres_database() -> AsyncIterator[
    tuple[AsyncEngine, async_sessionmaker[AsyncSession]]
]:
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL integration tests")
    engine = create_async_engine(TEST_DATABASE_URL)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.execute(delete(TrustedSource))
    yield engine, factory
    async with engine.begin() as connection:
        await connection.execute(delete(TrustedSource))
    await engine.dispose()


def provenance(version: str, **overrides: object) -> SourceProvenance:
    values = {
        "source_id": "key:concurrent-guide",
        "content_hash": version * 64,
        "source_version": version,
        "source_version_id": version * 64,
        "original_source_name": "Concurrent guide",
        "original_source_path": "knowledge_base/concurrent-guide.md",
        "reviewer": "Lic. Ana Pérez",
        "review_date": "2026-07-16",
    }
    values.update(overrides)
    return SourceProvenance(**values)


async def test_concurrent_first_registration_atomically_updates_one_source(
    postgres_database,
):
    engine, session_factory = postgres_database
    first_registered = asyncio.Event()
    second_insert_started = asyncio.Event()
    allow_first_commit = asyncio.Event()
    insert_count = 0
    first_created_at = None

    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def observe_insert(_connection, _cursor, statement, _parameters, _context, _many):
        nonlocal insert_count
        if "INSERT INTO trusted_sources" in statement:
            insert_count += 1
            if insert_count == 2:
                second_insert_started.set()

    async def register_first(session):
        nonlocal first_created_at
        source = await register_trusted_source(
            session,
            provenance(
                "1",
                url="https://example.org/guide",
                author="Ana Pérez",
                license="CC-BY-4.0",
            ),
        )
        source.is_active = False
        await session.flush()
        first_created_at = source.created_at
        first_registered.set()
        await allow_first_commit.wait()
        await session.commit()

    async def register_second(session):
        await first_registered.wait()
        return await register_trusted_source(session, provenance("2"))

    async with session_factory() as first_session, session_factory() as second_session:
        first_task = asyncio.create_task(register_first(first_session))
        second_task = asyncio.create_task(register_second(second_session))
        try:
            await asyncio.wait_for(first_registered.wait(), timeout=5)
            await asyncio.wait_for(second_insert_started.wait(), timeout=5)
            assert not second_task.done()
            allow_first_commit.set()
            await first_task
            await second_task
            await second_session.commit()
        finally:
            allow_first_commit.set()
            first_task.cancel()
            second_task.cancel()
            await asyncio.gather(first_task, second_task, return_exceptions=True)

    async with session_factory() as session:
        stored = await get_trusted_source(session, "key:concurrent-guide")
        count = await session.scalar(select(func.count()).select_from(TrustedSource))

    assert stored is not None
    assert count == 1
    assert stored.source_version == "2"
    assert stored.url == "https://example.org/guide"
    assert stored.author == "Ana Pérez"
    assert stored.license == "CC-BY-4.0"
    assert stored.is_active is False
    assert stored.created_at == first_created_at
