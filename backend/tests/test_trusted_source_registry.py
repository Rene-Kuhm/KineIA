from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from app.core.ingestion.provenance import SourceProvenance
from app.models.trusted_source import TrustedSource
from app.services.trusted_source_registry import get_trusted_source, register_trusted_source
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as connection:
        await connection.run_sync(TrustedSource.__table__.create)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


def reviewed_provenance(**overrides: object) -> SourceProvenance:
    values = {
        "source_id": "key:trusted-guide",
        "content_hash": "a" * 64,
        "source_version": "1",
        "source_version_id": "b" * 64,
        "original_source_name": "Trusted guide",
        "original_source_path": "knowledge_base/trusted-guide.md",
        "reviewer": "Lic. Ana Pérez",
        "review_date": "2026-07-16",
    }
    values.update(overrides)
    return SourceProvenance(**values)


async def test_registers_reviewed_source_for_later_lookup(session_factory):
    async with session_factory() as session:
        registered = await register_trusted_source(session, reviewed_provenance())
        await session.commit()

    async with session_factory() as session:
        stored = await get_trusted_source(session, registered.source_id)

    assert stored is not None
    assert stored.source_version_id == "b" * 64
    assert stored.reviewer == "Lic. Ana Pérez"
    assert stored.review_date.isoformat() == "2026-07-16"
    assert stored.url is None


async def test_reregistration_replaces_the_current_source_version(session_factory):
    async with session_factory() as session:
        await register_trusted_source(session, reviewed_provenance())
        await session.commit()

    async with session_factory() as session:
        await register_trusted_source(
            session,
            reviewed_provenance(
                content_hash="c" * 64,
                source_version="2",
                source_version_id="d" * 64,
                reviewer="Lic. Bruno Díaz",
                review_date="2026-07-17",
            ),
        )
        await session.commit()

    async with session_factory() as session:
        stored = await get_trusted_source(session, "key:trusted-guide")

    assert stored is not None
    assert stored.content_hash == "c" * 64
    assert stored.source_version == "2"
    assert stored.source_version_id == "d" * 64
    assert stored.reviewer == "Lic. Bruno Díaz"


async def test_sparse_reregistration_preserves_curated_state(session_factory):
    async with session_factory() as session:
        first = await register_trusted_source(
            session,
            reviewed_provenance(
                url="https://example.org/guide",
                author="Ana Pérez",
                license="CC-BY-4.0",
                area="traumatology",
            ),
        )
        first.is_active = False
        await session.commit()
        created_at = first.created_at

    async with session_factory() as session:
        updated = await register_trusted_source(
            session,
            reviewed_provenance(
                content_hash="c" * 64,
                source_version="2",
                source_version_id="d" * 64,
                reviewer="Lic. Bruno Díaz",
                review_date="2026-07-17",
            ),
        )
        await session.commit()

    assert updated.url == "https://example.org/guide"
    assert updated.author == "Ana Pérez"
    assert updated.license == "CC-BY-4.0"
    assert updated.area == "traumatology"
    assert updated.is_active is False
    assert updated.created_at == created_at


async def test_rejects_missing_reviewer_before_database_mutation(session_factory):
    async with session_factory() as session:
        with pytest.raises(ValueError, match="reviewer is required"):
            await register_trusted_source(session, reviewed_provenance(reviewer=None))

        assert await get_trusted_source(session, "key:trusted-guide") is None


async def test_rejects_missing_review_date_before_database_mutation(session_factory):
    async with session_factory() as session:
        with pytest.raises(ValueError, match="review_date is required"):
            await register_trusted_source(session, reviewed_provenance(review_date=None))

        assert await get_trusted_source(session, "key:trusted-guide") is None


async def test_rejects_review_due_date_before_review_before_database_mutation(session_factory):
    async with session_factory() as session:
        with pytest.raises(ValueError, match="review_due_date cannot precede review_date"):
            await register_trusted_source(
                session,
                reviewed_provenance(review_due_date="2026-07-15"),
            )

        assert await get_trusted_source(session, "key:trusted-guide") is None


async def test_rejects_new_review_date_after_preserved_due_date_before_mutation(session_factory):
    async with session_factory() as session:
        await register_trusted_source(
            session,
            reviewed_provenance(review_due_date="2026-07-20"),
        )
        await session.commit()

        with pytest.raises(ValueError, match="review_due_date cannot precede review_date"):
            await register_trusted_source(
                session,
                reviewed_provenance(
                    source_version="2",
                    source_version_id="d" * 64,
                    review_date="2026-07-21",
                ),
            )

        stored = await get_trusted_source(session, "key:trusted-guide")

    assert stored is not None
    assert stored.source_version == "1"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("publication_date", "not-a-date"),
        ("acquisition_date", "2026-02-30"),
        ("review_date", "16/07/2026"),
        ("review_due_date", "tomorrow"),
    ],
)
async def test_rejects_malformed_dates_before_database_mutation(session_factory, field, value):
    async with session_factory() as session:
        with pytest.raises(ValueError):
            await register_trusted_source(session, reviewed_provenance(**{field: value}))

        assert await get_trusted_source(session, "key:trusted-guide") is None


async def test_registration_does_not_commit_the_caller_transaction(session_factory):
    async with session_factory() as session:
        await register_trusted_source(session, reviewed_provenance())
        await session.rollback()

    async with session_factory() as session:
        assert await get_trusted_source(session, "key:trusted-guide") is None
