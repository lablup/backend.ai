"""cascade fragment deletion from app_config_allow_list

Add a composite FK from ``app_config_fragments (config_name, scope_type)`` to
``app_config_allow_list`` with ``ON DELETE CASCADE`` (BEP-1052): removing an
allow-list entry removes every fragment written under it, so a revoked value
disappears from the merge in the same statement. Fragments whose allow-list
entry was already removed (previously kept and still merged) are deleted before
the FK is added — the same outcome the cascade would have produced.

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
    # Fragments without an allow-list entry are unrepresentable once the FK exists;
    # remove them as the cascade would have when the entry was purged.
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


def downgrade() -> None:
    op.drop_constraint(
        "fk_app_config_fragments_config_name_scope_type",
        "app_config_fragments",
        type_="foreignkey",
    )
