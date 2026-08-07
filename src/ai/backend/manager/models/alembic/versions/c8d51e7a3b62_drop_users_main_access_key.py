"""drop users.main_access_key

Which keypair is a user's main one now lives on ``keypairs.is_default``, and
nothing reads the column any more. Its foreign key was ``ON DELETE SET NULL``,
so deleting any keypair silently cleared it — the reason for the move.

The downgrade restores the column and refills it from the marker.

Revision ID: c8d51e7a3b62
Revises: c04f8b1a6e37
Create Date: 2026-08-06 12:30:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c8d51e7a3b62"
down_revision = "c04f8b1a6e37"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("fk_users_main_access_key_keypairs", "users", type_="foreignkey")
    op.drop_column("users", "main_access_key")


def downgrade() -> None:
    op.add_column("users", sa.Column("main_access_key", sa.String(length=20), nullable=True))
    op.create_foreign_key(
        op.f("fk_users_main_access_key_keypairs"),
        "users",
        "keypairs",
        ["main_access_key"],
        ["access_key"],
        ondelete="SET NULL",
    )
    op.get_bind().execute(
        sa.text("""
            UPDATE users
            SET main_access_key = keypairs.access_key
            FROM keypairs
            WHERE keypairs."user" = users.uuid AND keypairs.is_default
        """)
    )
