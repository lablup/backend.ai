"""add relation_type to association_scopes_entities

Revision ID: 8fd6f47bd226
Revises: 321c033a321b
Create Date: 2026-02-10 19:44:48.369502

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8fd6f47bd226"
down_revision = "321c033a321b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "association_scopes_entities",
        sa.Column("relation_type", sa.String(32), nullable=False, server_default="auto"),
    )


def downgrade() -> None:
    op.drop_column("association_scopes_entities", "relation_type")
