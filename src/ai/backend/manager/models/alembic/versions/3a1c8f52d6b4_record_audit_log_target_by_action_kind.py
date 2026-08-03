"""record audit log target by action kind

``entity_id`` carried three meanings at once: an entity id, a scope id, and a
placeholder for actions with no target. ``action_kind`` now records which shape
wrote the row instead of leaving it to be inferred from which columns are filled.

Scopes move to ``audit_log_scopes`` rather than becoming columns: an entity can
belong to several scopes, and columns would either duplicate the audit row per
scope or force an arbitrary pick.

A lookup key is stored as two plain indexed columns rather than JSON so it stays
filterable with the same string conditions as the rest of the audit search.

Purely additive; existing rows keep NULL, which reads as "written before these
columns existed". No backfill.

Revision ID: 3a1c8f52d6b4
Revises: 9fbeda8995ff
Create Date: 2026-08-03 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "3a1c8f52d6b4"
down_revision = "9fbeda8995ff"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_logs", sa.Column("action_kind", sa.String(), nullable=True))
    op.add_column("audit_logs", sa.Column("lookup_kind", sa.String(), nullable=True))
    op.add_column("audit_logs", sa.Column("lookup_key", sa.String(), nullable=True))
    op.create_index("ix_audit_logs_lookup", "audit_logs", ["lookup_kind", "lookup_key"])

    op.create_table(
        "audit_log_scopes",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("audit_log_id", GUID(), nullable=False),
        sa.Column("scope_type", sa.String(), nullable=False),
        sa.Column("scope_id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["audit_log_id"], ["audit_logs.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("audit_log_id", "scope_type", "scope_id", name="uq_audit_log_scope"),
    )
    op.create_index("ix_audit_log_scopes_audit_log_id", "audit_log_scopes", ["audit_log_id"])
    op.create_index("ix_audit_log_scopes_scope", "audit_log_scopes", ["scope_type", "scope_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_log_scopes_scope", table_name="audit_log_scopes")
    op.drop_index("ix_audit_log_scopes_audit_log_id", table_name="audit_log_scopes")
    op.drop_table("audit_log_scopes")
    op.drop_index("ix_audit_logs_lookup", table_name="audit_logs")
    op.drop_column("audit_logs", "lookup_key")
    op.drop_column("audit_logs", "lookup_kind")
    op.drop_column("audit_logs", "action_kind")
