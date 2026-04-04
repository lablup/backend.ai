"""add_model_card_permissions_to_rbac

Revision ID: f1a2b3c4d5e6
Revises: bbcc151ec870
Create Date: 2026-04-02 13:30:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.rbac_models.migration.enums import (
    EntityType,
    OperationType,
)

# revision identifiers, used by Alembic.
revision = "f1a2b3c4d5e6"
down_revision = "bbcc151ec870"
branch_labels = None
depends_on = None

MEMBER_ROLE_SUFFIX = "member"
MODEL_CARD_ENTITY_TYPE = EntityType.MODEL_CARD.value


def upgrade() -> None:
    db_conn = op.get_bind()
    _add_model_card_permissions(db_conn)


def downgrade() -> None:
    db_conn = op.get_bind()
    db_conn.execute(
        sa.text("DELETE FROM permissions WHERE entity_type = :entity_type"),
        {"entity_type": MODEL_CARD_ENTITY_TYPE},
    )


def _add_model_card_permissions(db_conn: sa.engine.Connection) -> None:
    """Add MODEL_CARD permissions to all existing role+scope combinations.

    Rules (same as session migration pattern):
    - Member roles in project scope → read only
    - All other roles (admin/owner) → full operations
    - Domain-scoped member roles are skipped
    """
    member_ops = [op_type.value for op_type in OperationType.member_operations()]
    owner_ops = [op_type.value for op_type in OperationType.owner_operations()]

    insert_query = sa.text("""
        WITH role_scopes AS (
            SELECT DISTINCT
                p.role_id,
                r.name AS role_name,
                p.scope_type,
                p.scope_id
            FROM permissions p
            JOIN roles r ON p.role_id = r.id
        ),
        role_operations AS (
            -- Member operations for non-domain member roles
            SELECT
                rs.role_id,
                rs.scope_type,
                rs.scope_id,
                unnest(CAST(:member_ops AS text[])) AS operation
            FROM role_scopes rs
            WHERE rs.scope_type != 'domain'
              AND rs.role_name LIKE :member_pattern

            UNION ALL

            -- Owner operations for non-member roles
            SELECT
                rs.role_id,
                rs.scope_type,
                rs.scope_id,
                unnest(CAST(:owner_ops AS text[])) AS operation
            FROM role_scopes rs
            WHERE NOT (rs.role_name LIKE :member_pattern)
        )
        INSERT INTO permissions (role_id, scope_type, scope_id, entity_type, operation)
        SELECT
            role_id,
            scope_type,
            scope_id,
            :entity_type AS entity_type,
            operation
        FROM role_operations
        ON CONFLICT (role_id, scope_type, scope_id, entity_type, operation) DO NOTHING
    """)

    db_conn.execute(
        insert_query,
        {
            "member_ops": member_ops,
            "owner_ops": owner_ops,
            "member_pattern": f"%{MEMBER_ROLE_SUFFIX}",
            "entity_type": MODEL_CARD_ENTITY_TYPE,
        },
    )
