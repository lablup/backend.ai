"""record the action name on audit rows

A row carried only ``entity_type``/``operation``/``action_kind``, so two
different operations on the same entity (listing files vs. searching sessions)
became indistinguishable once recorded. ``action_name`` records the name the
action class declares.

Rows written before the column existed are backfilled with the same
``entity_type:operation`` spec type the legacy monitor writes, so the column
is NOT NULL and readers never handle a missing name.

Revision ID: 37d711158a8c
Revises: 3ebcf2c3c959
Create Date: 2026-08-08 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "37d711158a8c"
down_revision = "3ebcf2c3c959"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_logs", sa.Column("action_name", sa.String(), nullable=True))
    op.execute("UPDATE audit_logs SET action_name = entity_type || ':' || operation")
    op.alter_column("audit_logs", "action_name", nullable=False)
    op.create_index("ix_audit_logs_action_name", "audit_logs", ["action_name"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_action_name", table_name="audit_logs")
    op.drop_column("audit_logs", "action_name")
