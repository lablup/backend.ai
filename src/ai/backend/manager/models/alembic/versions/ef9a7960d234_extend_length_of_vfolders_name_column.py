"""extend length of vfolders.name column

Revision ID: ef9a7960d234
Revises: 3596bc12ec09
Create Date: 2025-01-03 16:07:11.407081

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ef9a7960d234"
down_revision = "3596bc12ec09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "vfolders",
        "name",
        existing_type=sa.VARCHAR(length=64),
        type_=sa.String(length=128),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "vfolders",
        "name",
        existing_type=sa.String(length=128),
        type_=sa.VARCHAR(length=64),
        existing_nullable=False,
    )
