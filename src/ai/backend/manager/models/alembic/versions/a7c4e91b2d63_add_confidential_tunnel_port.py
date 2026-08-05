"""add confidential tunnel port

Revision ID: a7c4e91b2d63
Revises: e3b5c8d1f409
Create Date: 2026-08-05

"""

import sqlalchemy as sa
from alembic import op

revision = "a7c4e91b2d63"
down_revision = "e3b5c8d1f409"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("confidential_channels", sa.Column("tunnel_port", sa.Integer, nullable=True))


def downgrade() -> None:
    op.drop_column("confidential_channels", "tunnel_port")
