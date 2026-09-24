"""Create cases and ordered report evidence links.

Revision ID: 6b20d87c4a11
Revises: 70eaec27bd75
"""

from alembic import op
import sqlalchemy as sa

revision = "6b20d87c4a11"
down_revision = "70eaec27bd75"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cases",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "case_reports",
        sa.Column("case_id", sa.UUID(), sa.ForeignKey("cases.id", ondelete="CASCADE"), primary_key=True, nullable=False),
        sa.Column("report_id", sa.UUID(), sa.ForeignKey("reports.id", ondelete="RESTRICT"), primary_key=True, nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
    )
    op.create_index("ix_case_reports_report_id", "case_reports", ["report_id"])


def downgrade() -> None:
    op.drop_index("ix_case_reports_report_id", table_name="case_reports")
    op.drop_table("case_reports")
    op.drop_table("cases")
