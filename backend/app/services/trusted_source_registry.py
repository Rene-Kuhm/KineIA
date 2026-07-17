from datetime import date

from app.core.ingestion.provenance import SourceProvenance
from app.models.trusted_source import TrustedSource
from sqlalchemy import func, or_
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.ext.asyncio import AsyncSession

_DATE_FIELDS = ("publication_date", "acquisition_date", "review_due_date")
_OPTIONAL_FIELDS = (
    "url",
    "doi",
    "isbn",
    "edition",
    "publisher",
    "license",
    "rights",
    "author",
    "year",
    "evidence_level",
    "area",
    "population",
    "source_type",
)
_REQUIRED_UPDATE_FIELDS = (
    "content_hash",
    "source_version",
    "source_version_id",
    "original_source_name",
    "original_source_path",
    "reviewer",
    "review_date",
)


def _optional_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value is not None else None


async def _upsert_postgresql(
    session: AsyncSession, source_id: str, values: dict[str, object]
) -> TrustedSource:
    statement = postgresql_insert(TrustedSource).values(source_id=source_id, **values)
    excluded = statement.excluded
    updates = {field: getattr(excluded, field) for field in _REQUIRED_UPDATE_FIELDS}
    updates.update(
        {
            field: func.coalesce(getattr(excluded, field), getattr(TrustedSource, field))
            for field in (*_OPTIONAL_FIELDS, *_DATE_FIELDS)
        }
    )
    effective_due_date = func.coalesce(excluded.review_due_date, TrustedSource.review_due_date)
    statement = statement.on_conflict_do_update(
        index_elements=[TrustedSource.source_id],
        set_={**updates, "updated_at": func.now()},
        where=or_(effective_due_date.is_(None), effective_due_date >= excluded.review_date),
    ).returning(TrustedSource)
    result = await session.execute(statement.execution_options(populate_existing=True))
    source = result.scalar_one_or_none()
    if source is None:
        raise ValueError("review_due_date cannot precede review_date")
    return source


async def register_trusted_source(
    session: AsyncSession, provenance: SourceProvenance
) -> TrustedSource:
    if not provenance.reviewer or not provenance.reviewer.strip():
        raise ValueError("reviewer is required")
    if not provenance.review_date:
        raise ValueError("review_date is required")
    review_date = date.fromisoformat(provenance.review_date)
    optional_values = {
        field: value
        for field in _OPTIONAL_FIELDS
        if (value := getattr(provenance, field)) is not None
    }
    parsed_dates = {
        field: parsed
        for field in _DATE_FIELDS
        if (parsed := _optional_date(getattr(provenance, field))) is not None
    }
    review_due_date = parsed_dates.get("review_due_date")
    if review_due_date is not None and review_due_date < review_date:
        raise ValueError("review_due_date cannot precede review_date")
    optional_values.update(parsed_dates)
    source = await get_trusted_source(session, provenance.source_id)
    if (
        source is not None
        and review_due_date is None
        and source.review_due_date is not None
        and source.review_due_date < review_date
    ):
        raise ValueError("review_due_date cannot precede review_date")
    values = {
        "content_hash": provenance.content_hash,
        "source_version": provenance.source_version,
        "source_version_id": provenance.source_version_id,
        "original_source_name": provenance.original_source_name,
        "original_source_path": provenance.original_source_path,
        "reviewer": provenance.reviewer,
        "review_date": review_date,
        **optional_values,
    }
    if session.get_bind().dialect.name == "postgresql":
        return await _upsert_postgresql(session, provenance.source_id, values)
    if source is None:
        source = TrustedSource(source_id=provenance.source_id, **values)
        session.add(source)
    else:
        for field, value in values.items():
            setattr(source, field, value)
    await session.flush()
    return source


async def get_trusted_source(session: AsyncSession, source_id: str) -> TrustedSource | None:
    return await session.get(TrustedSource, source_id)
