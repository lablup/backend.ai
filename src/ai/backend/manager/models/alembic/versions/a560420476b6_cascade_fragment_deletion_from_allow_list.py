"""cascade app config subtree deletion

Cascade deletion down ``definition -> allow_list -> fragment`` (BEP-1052):

1. Composite FK ``app_config_fragments (config_name, scope_type) ->
   app_config_allow_list`` ``ON DELETE CASCADE`` (orphaned fragments deleted first).
2. ``app_config_allow_list.config_name -> app_config_definitions`` -> ``CASCADE``.
3. Drop the redundant direct ``app_config_fragments.config_name ->
   app_config_definitions`` FK — the composite FK already guarantees a registered
   ``config_name`` transitively, and this FK only blocked the definition delete.

The released allow-list creation migration entered a wrong (non-convention) name
for the definitions FK, so its name differs between DBs; we drop both candidate
names with ``IF EXISTS``.

Revision ID: a560420476b6
Revises: 66d0f891ed20
Create Date: 2026-07-03

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a560420476b6"
down_revision = "66d0f891ed20"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. fragment -> allow_list composite FK (drop pre-existing orphans first).
    op.execute(
        sa.text(
            """
            DELETE FROM app_config_fragments f
            WHERE NOT EXISTS (
                SELECT 1
                FROM app_config_allow_list al
                WHERE al.config_name = f.config_name
                  AND al.scope_type = f.scope_type
            )
            """
        )
    )
    op.create_foreign_key(
        "fk_app_config_fragments_config_name_scope_type",
        "app_config_fragments",
        "app_config_allow_list",
        ["config_name", "scope_type"],
        ["config_name", "scope_type"],
        ondelete="CASCADE",
    )
    # 2. allow_list -> definitions: NO ACTION -> CASCADE.
    # The released creation migration entered a wrong (non-convention) FK name, so the
    # actual name differs by DB — drop whichever exists before recreating.
    op.execute(
        "ALTER TABLE app_config_allow_list "
        "DROP CONSTRAINT IF EXISTS fk_app_config_allow_list_config_name"
    )
    op.execute(
        "ALTER TABLE app_config_allow_list "
        "DROP CONSTRAINT IF EXISTS fk_app_config_allow_list_config_name_app_config_definitions"
    )
    op.create_foreign_key(
        "fk_app_config_allow_list_config_name_app_config_definitions",
        "app_config_allow_list",
        "app_config_definitions",
        ["config_name"],
        ["config_name"],
        ondelete="CASCADE",
    )
    # 3. fragments -> definitions: drop the redundant direct FK (it blocks the cascade).
    op.execute(
        "ALTER TABLE app_config_fragments "
        "DROP CONSTRAINT IF EXISTS fk_app_config_fragments_config_name_app_config_definitions"
    )


def downgrade() -> None:
    op.create_foreign_key(
        "fk_app_config_fragments_config_name_app_config_definitions",
        "app_config_fragments",
        "app_config_definitions",
        ["config_name"],
        ["config_name"],
        ondelete="NO ACTION",
    )
    op.execute(
        "ALTER TABLE app_config_allow_list "
        "DROP CONSTRAINT IF EXISTS fk_app_config_allow_list_config_name_app_config_definitions"
    )
    op.create_foreign_key(
        "fk_app_config_allow_list_config_name_app_config_definitions",
        "app_config_allow_list",
        "app_config_definitions",
        ["config_name"],
        ["config_name"],
        ondelete="NO ACTION",
    )
    op.drop_constraint(
        "fk_app_config_fragments_config_name_scope_type",
        "app_config_fragments",
        type_="foreignkey",
    )
