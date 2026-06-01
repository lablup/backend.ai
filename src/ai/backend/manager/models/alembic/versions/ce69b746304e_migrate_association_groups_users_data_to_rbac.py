"""migrate association_groups_users data to rbac

Revision ID: ce69b746304e
Revises: c2d3e4f5a6b7
Create Date: 2026-04-24 21:34:36.543864

"""

# Part of: 26.5.0

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ce69b746304e"
down_revision = "c2d3e4f5a6b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Backfill association_scopes_entities with PROJECT/USER rows derived
    from association_groups_users. Idempotent via ON CONFLICT.
    """
    op.execute(
        sa.text(
            """
            INSERT INTO association_scopes_entities
                (scope_type, scope_id, entity_type, entity_id, relation_type)
            SELECT
                'project',
                CAST(group_id AS text),
                'user',
                CAST(user_id AS text),
                'auto'
            FROM association_groups_users
            ON CONFLICT (scope_type, scope_id, entity_id) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    """No-op: rows inserted here are indistinguishable from auto-synced rows."""
