"""Create trusted source registry."""

import sqlalchemy as sa
from alembic import op

revision: str = "20260716_0001"
down_revision: str | None = None


def upgrade() -> None:
    op.create_table(
        "trusted_sources",
        sa.Column("source_id", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("source_version", sa.Text(), nullable=False),
        sa.Column("source_version_id", sa.String(length=64), nullable=False),
        sa.Column("original_source_name", sa.Text(), nullable=False),
        sa.Column("original_source_path", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("doi", sa.Text(), nullable=True),
        sa.Column("isbn", sa.String(length=32), nullable=True),
        sa.Column("edition", sa.Text(), nullable=True),
        sa.Column("publisher", sa.Text(), nullable=True),
        sa.Column("license", sa.Text(), nullable=True),
        sa.Column("rights", sa.Text(), nullable=True),
        sa.Column("author", sa.Text(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("acquisition_date", sa.Date(), nullable=True),
        sa.Column("evidence_level", sa.String(length=50), nullable=True),
        sa.Column("area", sa.String(length=100), nullable=True),
        sa.Column("population", sa.Text(), nullable=True),
        sa.Column("source_type", sa.String(length=50), nullable=True),
        sa.Column("reviewer", sa.Text(), nullable=False),
        sa.Column("review_date", sa.Date(), nullable=False),
        sa.Column("review_due_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "year IS NULL OR year BETWEEN 1000 AND 9999",
            name="ck_trusted_sources_year_range",
        ),
        sa.CheckConstraint(
            "review_due_date IS NULL OR review_due_date >= review_date",
            name="ck_trusted_sources_review_due_date",
        ),
        sa.PrimaryKeyConstraint("source_id"),
    )


def downgrade() -> None:
    op.drop_table("trusted_sources")
