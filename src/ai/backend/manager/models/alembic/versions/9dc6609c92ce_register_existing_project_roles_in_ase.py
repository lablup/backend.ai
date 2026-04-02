"""register existing project roles in association_scopes_entities

Revision ID: 9dc6609c92ce
Revises: bbcc151ec870
Create Date: 2026-04-01

"""

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "9dc6609c92ce"
down_revision = "bbcc151ec870"
branch_labels = None
depends_on = None

BATCH_SIZE = 1000


def upgrade() -> None:
    conn = op.get_bind()

    rows = conn.execute(
        text(
            "SELECT DISTINCT role_id::text, scope_id FROM permissions WHERE scope_type = 'project'"
        )
    ).all()

    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        values = ", ".join(
            f"('project', '{row.scope_id}', 'role', '{row.role_id}')" for row in batch
        )
        conn.execute(
            text(
                "INSERT INTO association_scopes_entities"
                " (scope_type, scope_id, entity_type, entity_id)"
                f" VALUES {values}"
                " ON CONFLICT ON CONSTRAINT uq_scope_id_entity_id DO NOTHING"
            )
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text(
            "DELETE FROM association_scopes_entities"
            " WHERE scope_type = 'project' AND entity_type = 'role'"
        )
    )
