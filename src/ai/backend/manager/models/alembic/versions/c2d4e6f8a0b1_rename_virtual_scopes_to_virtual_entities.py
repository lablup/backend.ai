"""rename virtual_scopes to virtual_entities

Revision ID: c2d4e6f8a0b1
Revises: a1f0c7b45de2
Create Date: 2026-09-02 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "c2d4e6f8a0b1"
down_revision = "a1f0c7b45de2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("virtual_scopes", "virtual_entities")
    op.alter_column("virtual_entities", "scope_type", new_column_name="entity_type")
    op.alter_column("virtual_entities", "scope_id", new_column_name="entity_id")
    op.execute(
        "ALTER TABLE virtual_entities RENAME CONSTRAINT pk_virtual_scopes TO pk_virtual_entities"
    )
    op.execute(
        "ALTER TABLE virtual_entities "
        "RENAME CONSTRAINT uq_virtual_scopes_scope TO uq_virtual_entities_entity"
    )

    op.alter_column("scope_bindings", "virtual_scope_id", new_column_name="virtual_entity_id")
    op.execute(
        "ALTER TABLE scope_bindings "
        "RENAME CONSTRAINT fk_scope_bindings_virtual_scope_id_virtual_scopes "
        "TO fk_scope_bindings_virtual_entity_id_virtual_entities"
    )
    op.execute(
        "ALTER INDEX ix_scope_bindings_virtual_scope RENAME TO ix_scope_bindings_virtual_entity"
    )

    op.alter_column("entity_memberships", "virtual_scope_id", new_column_name="virtual_entity_id")
    op.execute(
        "ALTER TABLE entity_memberships "
        "RENAME CONSTRAINT fk_entity_memberships_virtual_scope_id_virtual_scopes "
        "TO fk_entity_memberships_virtual_entity_id_virtual_entities"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE entity_memberships "
        "RENAME CONSTRAINT fk_entity_memberships_virtual_entity_id_virtual_entities "
        "TO fk_entity_memberships_virtual_scope_id_virtual_scopes"
    )
    op.alter_column("entity_memberships", "virtual_entity_id", new_column_name="virtual_scope_id")

    op.execute(
        "ALTER INDEX ix_scope_bindings_virtual_entity RENAME TO ix_scope_bindings_virtual_scope"
    )
    op.execute(
        "ALTER TABLE scope_bindings "
        "RENAME CONSTRAINT fk_scope_bindings_virtual_entity_id_virtual_entities "
        "TO fk_scope_bindings_virtual_scope_id_virtual_scopes"
    )
    op.alter_column("scope_bindings", "virtual_entity_id", new_column_name="virtual_scope_id")

    op.execute(
        "ALTER TABLE virtual_entities "
        "RENAME CONSTRAINT uq_virtual_entities_entity TO uq_virtual_scopes_scope"
    )
    op.execute(
        "ALTER TABLE virtual_entities RENAME CONSTRAINT pk_virtual_entities TO pk_virtual_scopes"
    )
    op.alter_column("virtual_entities", "entity_id", new_column_name="scope_id")
    op.alter_column("virtual_entities", "entity_type", new_column_name="scope_type")
    op.rename_table("virtual_entities", "virtual_scopes")
