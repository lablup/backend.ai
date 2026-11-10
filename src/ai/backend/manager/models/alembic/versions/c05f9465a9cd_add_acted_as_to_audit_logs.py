"""add acted_as to audit_logs

Split the audit actor record into the trigger identity (``triggered_by``) and the
effective identity it actually ran as (``acted_as``). ``acted_as`` is nullable,
mirroring ``triggered_by`` (both are absent for system-triggered actions).

Existing rows are backfilled from ``triggered_by`` (historically the caller equals
the effective user); rows where ``triggered_by`` is NULL stay NULL. The backfill rebuilds
the table (``AuditLogRebuild``) instead of updating every row.

Revision ID: c05f9465a9cd
Revises: 7f2b9c4d1a83
Create Date: 2026-07-09

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.alembic.audit_log_rebuild import AuditLogRebuild

# revision identifiers, used by Alembic.
revision = "c05f9465a9cd"
down_revision = "7f2b9c4d1a83"
# Part of: 26.8.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    rebuild = AuditLogRebuild(op.get_bind())
    if "acted_as" not in rebuild.columns():
        rebuild.run()


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("audit_logs")}
    if "acted_as" in cols:
        op.drop_column("audit_logs", "acted_as")
