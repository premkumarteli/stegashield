"""001_initial_schema: create initial StegaShield tables

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-11-16 10:30:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. operations table
    op.create_table(
        "operations",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("operation_type", sa.String(length=32), nullable=False),
        sa.Column("cover_filename", sa.String(length=255), nullable=True),
        sa.Column("stego_filename", sa.String(length=255), nullable=True),
        sa.Column("payload_type", sa.String(length=32), nullable=True),
        sa.Column("method", sa.String(length=32), nullable=True),
        sa.Column("mse", sa.Float(), nullable=True),
        sa.Column("psnr", sa.Float(), nullable=True),
        sa.Column("ssim", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_operations_session_id", "operations", ["session_id"])

    # 2. detections table
    op.create_table(
        "detections",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("operation_id", sa.String(length=36), sa.ForeignKey("operations.id", ondelete="CASCADE"), nullable=True),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("chi2_stat", sa.Float(), nullable=False),
        sa.Column("p_value", sa.Float(), nullable=False),
        sa.Column("rs_payload_ratio", sa.Float(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_detections_session_id", "detections", ["session_id"])

    # 3. temp_files table
    op.create_table(
        "temp_files",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_temp_files_session_id", "temp_files", ["session_id"])

    # 4. experiments table
    op.create_table(
        "experiments",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("config_json", sa.Text(), nullable=False),
        sa.Column("summary_json", sa.Text(), nullable=True),
        sa.Column("csv_data", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_experiments_session_id", "experiments", ["session_id"])

    # 5. experiment_items table
    op.create_table(
        "experiment_items",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("experiment_id", sa.String(length=36), sa.ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cover_name", sa.String(length=255), nullable=False),
        sa.Column("method", sa.String(length=32), nullable=False),
        sa.Column("ratio", sa.Float(), nullable=False),
        sa.Column("detector", sa.String(length=32), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("verdict", sa.String(length=32), nullable=False),
        sa.Column("execution_time_ms", sa.Float(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("experiment_items")
    op.drop_table("experiments")
    op.drop_index("ix_temp_files_session_id", table_name="temp_files")
    op.drop_table("temp_files")
    op.drop_index("ix_detections_session_id", table_name="detections")
    op.drop_table("detections")
    op.drop_index("ix_operations_session_id", table_name="operations")
    op.drop_table("operations")
