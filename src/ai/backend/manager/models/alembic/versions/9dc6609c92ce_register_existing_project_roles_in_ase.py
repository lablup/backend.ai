"""register existing project roles in association_scopes_entities

Revision ID: 9dc6609c92ce
Revises: af1b9ec86adb
Create Date: 2026-04-01

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ai.backend.manager.models.rbac_models.migration.models import (
    get_association_scopes_entities_table,
    get_permission_groups_table,
)

# revision identifiers, used by Alembic.
revision = "9dc6609c92ce"
down_revision = "af1b9ec86adb"
branch_labels = None
depends_on = None

BATCH_SIZE = 1000


def upgrade() -> None:
    conn = op.get_bind()
    pg_table = get_permission_groups_table()
    ase_table = get_association_scopes_entities_table()

    query = sa.select(pg_table.c.role_id, pg_table.c.scope_id).where(
        pg_table.c.scope_type == "project"
    )
    rows = conn.execute(query).all()

    inputs = [
        {
            "scope_type": "project",
            "scope_id": row.scope_id,
            "entity_type": "role",
            "entity_id": str(row.role_id),
        }
        for row in rows
    ]

    if inputs:
        for i in range(0, len(inputs), BATCH_SIZE):
            batch = inputs[i : i + BATCH_SIZE]
            stmt = (
                pg_insert(ase_table)
                .values(batch)
                .on_conflict_do_nothing(constraint="uq_scope_id_entity_id")
            )
            conn.execute(stmt)


def downgrade() -> None:
    conn = op.get_bind()
    ase_table = get_association_scopes_entities_table()
    conn.execute(
        sa.delete(ase_table).where(
            ase_table.c.scope_type == "project",
            ase_table.c.entity_type == "role",
        )
    )
