"""make audit_logs.entity_type nullable

A relation operation names two scopes and no entity type: what it writes is a row
linking two entities, which is neither of them. The audit row it leaves therefore has
scopes but no entity kind, and the column has to admit that.

Existing rows all carry a kind, so nothing is migrated.

Revision ID: c8e4b1a09d37
Revises: 3f7a2c1e9b04
Create Date: 2026-08-26

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c8e4b1a09d37"
down_revision = "3f7a2c1e9b04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("audit_logs", "entity_type", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    # A row written by a relation operation has no kind to restore, so the column can
    # only go back to NOT NULL once those rows are gone.
    op.execute("DELETE FROM audit_logs WHERE entity_type IS NULL")
    op.alter_column("audit_logs", "entity_type", existing_type=sa.String(), nullable=False)
