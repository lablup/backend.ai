"""add source col to roles

Revision ID: 42feff246198
Revises: ec7a778bcb78
Create Date: 2025-08-09 12:50:25.566785

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "42feff246198"
down_revision = "ec7a778bcb78"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "roles",
        sa.Column("source", sa.VARCHAR(length=16), server_default="system", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("roles", "source")
