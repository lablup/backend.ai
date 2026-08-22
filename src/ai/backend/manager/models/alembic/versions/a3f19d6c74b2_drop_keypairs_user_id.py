"""drop the email copy from keypairs

``keypairs`` named its owner twice: ``user`` holds the uuid and a foreign key into
``users``, while ``user_id`` held a copy of that user's email. Every read the copy
served is answerable through the foreign key, and keeping it made a create read the
user row for no other reason.

Revision ID: a3f19d6c74b2
Revises: c8e2a5f10d47
Create Date: 2026-08-21 08:10:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a3f19d6c74b2"
down_revision = "c8e2a5f10d47"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index(op.f("ix_keypairs_user_id"), table_name="keypairs")
    op.drop_column("keypairs", "user_id")


def downgrade() -> None:
    op.add_column(
        "keypairs",
        sa.Column("user_id", sa.String(length=256), nullable=True),
    )
    # "user" is a reserved word, so the column it names is quoted.
    op.execute(
        'UPDATE keypairs SET user_id = users.email FROM users WHERE users.uuid = keypairs."user"'
    )
    op.alter_column("keypairs", "user_id", nullable=False)
    op.create_index(op.f("ix_keypairs_user_id"), "keypairs", ["user_id"], unique=False)
