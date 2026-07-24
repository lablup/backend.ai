"""add scheduling history read permissions to roles that can read the scoped entity

Revision ID: c8e2f41a67d5
Revises: 5405ee0d8eed
Create Date: 2026-07-20 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c8e2f41a67d5"
down_revision = "5405ee0d8eed"
branch_labels = None
depends_on = None

# (scope entity that already carries a READ grant, history entity to mirror it onto)
_HISTORY_GRANTS = [
    ("session", "session:history"),
    ("model_deployment", "deployment:history"),
    ("routing", "route:history"),
]


def upgrade() -> None:
    conn = op.get_bind()

    # Reading an entity carries reading its scheduling history, so mirror every
    # existing READ grant onto the history entity within the same scope.
    # ON CONFLICT DO NOTHING keeps this idempotent for release-branch backports.
    for scope_entity, history_entity in _HISTORY_GRANTS:
        conn.execute(
            sa.text("""
                INSERT INTO permissions (role_id, scope_type, scope_id, entity_type, operation)
                SELECT DISTINCT p.role_id, p.scope_type, p.scope_id, :history_entity, 'read'
                FROM permissions p
                WHERE p.entity_type = :scope_entity
                  AND p.operation = 'read'
                ON CONFLICT DO NOTHING
            """),
            {"scope_entity": scope_entity, "history_entity": history_entity},
        )


def downgrade() -> None:
    conn = op.get_bind()

    for _, history_entity in _HISTORY_GRANTS:
        conn.execute(
            sa.text("""
                DELETE FROM permissions
                WHERE entity_type = :history_entity
                  AND operation = 'read'
            """),
            {"history_entity": history_entity},
        )
