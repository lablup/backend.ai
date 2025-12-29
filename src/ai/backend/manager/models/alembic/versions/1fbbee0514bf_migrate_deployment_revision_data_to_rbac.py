"""migrate_deployment_revision_data_to_rbac

Revision ID: 1fbbee0514bf
Revises: 013a6676866c
Create Date: 2025-12-29 12:00:03.441695

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

from ai.backend.manager.data.permission.id import ScopeType
from ai.backend.manager.models.rbac_models.migration.enums import (
    EntityType,
)

# revision identifiers, used by Alembic.
revision = "1fbbee0514bf"
down_revision = "013a6676866c"
branch_labels = None
depends_on = None

# Constants
BATCH_SIZE = 1000


def _associate_deployment_revisions_to_scopes(db_conn: Connection) -> None:
    """Associate all deployment revisions to user scopes based on endpoint created_user."""
    offset = 0
    scope_type = ScopeType.USER.value
    entity_type = EntityType.DEPLOYMENT_REVISION.value

    while True:
        query = sa.text("""
            SELECT dr.id, e.created_user
            FROM deployment_revisions dr
            JOIN endpoints e ON dr.endpoint = e.id
            ORDER BY dr.id
            OFFSET :offset
            LIMIT :limit
        """)
        rows = db_conn.execute(query, {"offset": offset, "limit": BATCH_SIZE}).all()
        if not rows:
            break
        offset += BATCH_SIZE

        # Prepare values for bulk insert
        values = ", ".join(
            f"('{scope_type}', '{row.created_user}', '{entity_type}', '{row.id}')" for row in rows
        )

        insert_query = sa.text(f"""
            INSERT INTO association_scopes_entities (scope_type, scope_id, entity_type, entity_id)
            VALUES {values}
            ON CONFLICT DO NOTHING
        """)
        db_conn.execute(insert_query)


def _remove_entity_from_scopes(db_conn: Connection, entity_type: EntityType) -> None:
    """Remove all entity-scope associations for a given entity type."""
    entity_type_value = entity_type.value

    while True:
        # Query records to delete
        query = sa.text("""
            SELECT id FROM association_scopes_entities
            WHERE entity_type = :entity_type
            LIMIT :limit
        """)
        rows = db_conn.execute(query, {"entity_type": entity_type_value, "limit": BATCH_SIZE}).all()
        if not rows:
            break

        # Delete the queried records
        ids = ", ".join(f"'{row.id}'" for row in rows)
        delete_query = sa.text(f"""
            DELETE FROM association_scopes_entities
            WHERE id IN ({ids})
        """)
        db_conn.execute(delete_query)


def upgrade() -> None:
    conn = op.get_bind()
    _associate_deployment_revisions_to_scopes(conn)


def downgrade() -> None:
    conn = op.get_bind()
    _remove_entity_from_scopes(conn, EntityType.DEPLOYMENT_REVISION)
