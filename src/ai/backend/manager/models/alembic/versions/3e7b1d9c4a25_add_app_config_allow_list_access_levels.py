"""add app_config_allow_list permission

Add a ``permission`` (``ro`` / ``rw``) column to ``app_config_allow_list``
(BEP-1052). The allow-list row registers a config layer and carries its merge
``rank`` (the read side); its mere existence used to double as the write gate,
conflating read-enablement with write-authorization. This admin-owned column
makes the write policy explicit — ``rw`` lets the scope owner write the layer,
``ro`` restricts writes to superadmins — while reads keep following scope
visibility. Existing rows are backfilled with the per-scope-type default
(public / domain = ``ro``, user = ``rw``).

Revision ID: 3e7b1d9c4a25
Revises: a3c1d8e5b294
Create Date: 2026-07-10

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3e7b1d9c4a25"
down_revision = "a3c1d8e5b294"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "app_config_allow_list",
        sa.Column("permission", sa.String(length=64), nullable=True),
    )
    # Backfill by the scope-type default policy (public/domain admin-managed, user self-service).
    op.execute(
        sa.text(
            """
            UPDATE app_config_allow_list
            SET permission = CASE scope_type
                    WHEN 'public' THEN 'ro'
                    WHEN 'domain' THEN 'ro'
                    WHEN 'user' THEN 'rw'
                END
            WHERE permission IS NULL
            """
        )
    )
    op.alter_column("app_config_allow_list", "permission", nullable=False)


def downgrade() -> None:
    op.drop_column("app_config_allow_list", "permission")
