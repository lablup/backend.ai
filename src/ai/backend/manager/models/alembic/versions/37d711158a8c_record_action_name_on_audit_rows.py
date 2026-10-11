"""record the action name on audit rows

A row carried only ``entity_type``/``operation``/``action_kind``, so two
different operations on the same entity (listing files vs. searching sessions)
became indistinguishable once recorded. ``action_name`` records the name the
action class declares.

Rows written before the column existed are backfilled with the same
``entity_type:operation`` spec type the legacy monitor writes, so the column
is NOT NULL and readers never handle a missing name. The backfill rebuilds the table
(``AuditLogRebuild``) instead of updating every row.

Revision ID: 37d711158a8c
Revises: 3ebcf2c3c959
Create Date: 2026-08-08 10:00:00.000000

"""

from alembic import op

from ai.backend.manager.models.alembic.audit_log_rebuild import AuditLogRebuild

# revision identifiers, used by Alembic.
revision = "37d711158a8c"
down_revision = "3ebcf2c3c959"
# Part of: 26.9.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    rebuild = AuditLogRebuild(op.get_bind())
    if "action_name" not in rebuild.columns():
        rebuild.run()


def downgrade() -> None:
    op.drop_index("ix_audit_logs_action_name", table_name="audit_logs")
    op.drop_column("audit_logs", "action_name")
