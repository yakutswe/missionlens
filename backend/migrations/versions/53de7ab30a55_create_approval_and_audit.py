"""Create local demo approval requests and append-only audit events.

Revision ID: 53de7ab30a55
Revises: 6b20d87c4a11
"""

from alembic import op
import sqlalchemy as sa

revision = "53de7ab30a55"
down_revision = "6b20d87c4a11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "approval_requests",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("case_id", sa.UUID(), sa.ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("action_description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("requested_by", sa.String(60), nullable=False),
        sa.Column("decided_by", sa.String(60), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="ck_approval_status"),
    )
    op.create_index("ix_approval_requests_case_id", "approval_requests", ["case_id"])
    op.create_table(
        "audit_events",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("case_id", sa.UUID(), sa.ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("approval_id", sa.UUID(), sa.ForeignKey("approval_requests.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("actor_id", sa.String(60), nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_events_case_id", "audit_events", ["case_id"])
    op.create_index("ix_audit_events_approval_id", "audit_events", ["approval_id"])
    op.create_index("ix_audit_events_occurred_at", "audit_events", ["occurred_at"])
    op.execute("""
        CREATE FUNCTION prevent_audit_event_changes() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'audit events cannot be updated or deleted';
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER audit_events_append_only
        BEFORE UPDATE OR DELETE ON audit_events
        FOR EACH ROW EXECUTE FUNCTION prevent_audit_event_changes();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER audit_events_append_only ON audit_events")
    op.execute("DROP FUNCTION prevent_audit_event_changes()")
    op.drop_index("ix_audit_events_occurred_at", table_name="audit_events")
    op.drop_index("ix_audit_events_approval_id", table_name="audit_events")
    op.drop_index("ix_audit_events_case_id", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_approval_requests_case_id", table_name="approval_requests")
    op.drop_table("approval_requests")
