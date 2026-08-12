"""add is_default to domains

The domain every user lands in has been the one literally named ``default``
since ``bae1a7326e8a``. The marker records it instead, the way
``a2f6b90c41d7`` did for keypairs.

Revision ID: b9e3a7c14f28
Revises: dfab9fd24208
Create Date: 2026-08-12 19:40:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b9e3a7c14f28"
down_revision = "dfab9fd24208"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "domains",
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.get_bind().execute(sa.text("UPDATE domains SET is_default = true WHERE name = 'default'"))
    op.create_index(
        "uq_domains_is_default",
        "domains",
        ["is_default"],
        unique=True,
        postgresql_where=sa.text("is_default"),
    )


def downgrade() -> None:
    op.drop_index("uq_domains_is_default", table_name="domains")
    op.drop_column("domains", "is_default")
