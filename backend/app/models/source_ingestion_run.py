from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class SourceIngestionRun(Base):
    __tablename__ = "source_ingestion_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'succeeded', 'failed')",
            name="ck_source_ingestion_runs_status",
        ),
    )

    source_version_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    error_stage: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
