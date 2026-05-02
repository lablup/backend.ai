"""add index to rbac tables

Revision ID: aa596a09c091
Revises: 8c1f7d3a9e2b
Create Date: 2026-05-01 04:40:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "aa596a09c091"
down_revision = "8c1f7d3a9e2b"
# Part of: 26.5.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    # association_scopes_entities: enables (entity_type, entity_id) lookup used by
    # the scope-walk CTE seed and the recursive parent-scope join. Existing
    # uq_scope_id_entity_id has scope_type as its leading column and cannot serve
    # this access pattern.
    op.create_index(
        "ix_association_scopes_entities_entity",
        "association_scopes_entities",
        ["entity_type", "entity_id"],
        unique=False,
    )

    # permissions: enables scope-first lookup (scope_type, scope_id, entity_type)
    # used when matching permission rows against scope_walk results. Existing
    # ix_permissions_role_scope has role_id as its leading column.
    op.create_index(
        "ix_permissions_scope_entity",
        "permissions",
        ["scope_type", "scope_id", "entity_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_permissions_scope_entity", table_name="permissions")
    op.drop_index(
        "ix_association_scopes_entities_entity",
        table_name="association_scopes_entities",
    )
