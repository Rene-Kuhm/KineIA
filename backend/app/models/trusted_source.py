from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Integer, String, Text, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class TrustedSource(Base):
    __tablename__ = "trusted_sources"
    __table_args__ = (
        CheckConstraint(
            "year IS NULL OR year BETWEEN 1000 AND 9999",
            name="ck_trusted_sources_year_range",
        ),
        CheckConstraint(
            "review_due_date IS NULL OR review_due_date >= review_date",
            name="ck_trusted_sources_review_due_date",
        ),
    )

    source_id: Mapped[str] = mapped_column(Text, primary_key=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_version: Mapped[str] = mapped_column(Text, nullable=False)
    source_version_id: Mapped[str] = mapped_column(String(64), nullable=False)
    original_source_name: Mapped[str] = mapped_column(Text, nullable=False)
    original_source_path: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str | None] = mapped_column(Text)
    doi: Mapped[str | None] = mapped_column(Text)
    isbn: Mapped[str | None] = mapped_column(String(32))
    edition: Mapped[str | None] = mapped_column(Text)
    publisher: Mapped[str | None] = mapped_column(Text)
    license: Mapped[str | None] = mapped_column(Text)
    rights: Mapped[str | None] = mapped_column(Text)
    author: Mapped[str | None] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(Integer)
    publication_date: Mapped[date | None] = mapped_column(Date)
    acquisition_date: Mapped[date | None] = mapped_column(Date)
    evidence_level: Mapped[str | None] = mapped_column(String(50))
    area: Mapped[str | None] = mapped_column(String(100))
    population: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str | None] = mapped_column(String(50))
    reviewer: Mapped[str] = mapped_column(Text, nullable=False)
    review_date: Mapped[date] = mapped_column(Date, nullable=False)
    review_due_date: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default=true(), default=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
