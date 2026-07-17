"""Create source ingestion run ledger."""

import sqlalchemy as sa
from alembic import op

revision: str = "20260716_0002"
down_revision: str | None = "20260716_0001"


def upgrade() -> None:
    op.create_table(
        "source_ingestion_runs",
        sa.Column("source_version_id", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("error_stage", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'succeeded', 'failed')",
            name="ck_source_ingestion_runs_status",
        ),
        sa.PrimaryKeyConstraint("source_version_id"),
    )
    op.create_index(
        "ix_source_ingestion_runs_source_id",
        "source_ingestion_runs",
        ["source_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_source_ingestion_runs_source_id", table_name="source_ingestion_runs")
    op.drop_table("source_ingestion_runs")
