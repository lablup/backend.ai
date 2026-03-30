"""change association scopes entities uq constraint

Revision ID: 82f4d3dea750
Revises: 1f76b4c0f399
Create Date: 2025-09-23 17:47:09.762087

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "82f4d3dea750"
down_revision = "1f76b4c0f399"
branch_labels = None
depends_on = None

BATCH_SIZE = 1000


def _remove_duplicates_batch(db_conn: Connection) -> None:
    while True:
        delete_batch_query = sa.text("""
            WITH duplicates AS (
                SELECT id,
                    ROW_NUMBER() OVER (
                        PARTITION BY scope_type, scope_id, entity_id
                        ORDER BY id ASC
                    ) as rn
                FROM association_scopes_entities
            ),
            to_delete AS (
                SELECT id
                FROM duplicates
                WHERE rn > 1
                LIMIT :batch_size
            )
            DELETE FROM association_scopes_entities
            WHERE id IN (SELECT id FROM to_delete)
        """)

        result = db_conn.execute(delete_batch_query, {"batch_size": BATCH_SIZE})
        batch_deleted = result.rowcount

        if batch_deleted == 0:
            break


def upgrade() -> None:
    op.execute("""
        ALTER TABLE association_scopes_entities
        DROP CONSTRAINT IF EXISTS uq_scope_id_entity_id
    """)

    conn = op.get_bind()
    _remove_duplicates_batch(conn)
    op.create_unique_constraint(
        "uq_scope_id_entity_id",
        "association_scopes_entities",
        ["scope_type", "scope_id", "entity_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_scope_id_entity_id", "association_scopes_entities", type_="unique")
    op.create_unique_constraint(
        "uq_scope_id_entity_id", "association_scopes_entities", ["scope_id", "entity_id"]
    )
