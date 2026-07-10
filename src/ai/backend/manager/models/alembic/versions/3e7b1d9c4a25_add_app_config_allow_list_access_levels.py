"""add app_config_allow_list read/write access levels

Add ``read_access`` / ``write_access`` to ``app_config_allow_list`` (BEP-1052).
The allow-list row registers a config layer and carries its merge ``rank`` (the
read side); its mere existence used to double as the write gate, conflating
read-enablement with write-authorization. These admin-owned tiers make the two
concerns independent: who may read and who may write a layer are now explicit.
Existing rows are backfilled with the per-scope-type default policy
(public: read=public/write=admin, domain: read=authenticated/write=admin,
user: read=owner/write=owner).

Revision ID: 3e7b1d9c4a25
Revises: 7f2b9c4d1a83
Create Date: 2026-07-10

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3e7b1d9c4a25"
down_revision = "7f2b9c4d1a83"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "app_config_allow_list",
        sa.Column("read_access", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "app_config_allow_list",
        sa.Column("write_access", sa.String(length=64), nullable=True),
    )
    # Backfill by the scope-type default policy.
    op.execute(
        sa.text(
            """
            UPDATE app_config_allow_list
            SET read_access = CASE scope_type
                    WHEN 'public' THEN 'public'
                    WHEN 'domain' THEN 'authenticated'
                    WHEN 'user' THEN 'owner'
                END,
                write_access = CASE scope_type
                    WHEN 'public' THEN 'admin'
                    WHEN 'domain' THEN 'admin'
                    WHEN 'user' THEN 'owner'
                END
            WHERE read_access IS NULL OR write_access IS NULL
            """
        )
    )
    op.alter_column("app_config_allow_list", "read_access", nullable=False)
    op.alter_column("app_config_allow_list", "write_access", nullable=False)


def downgrade() -> None:
    op.drop_column("app_config_allow_list", "write_access")
    op.drop_column("app_config_allow_list", "read_access")
