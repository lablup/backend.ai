"""allow_unicode_in_groups_and_domains_name

Revision ID: 9a06e8c862e7
Revises: dddf9be580f5
Create Date: 2023-11-27 14:36:18.676875

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9a06e8c862e7"
down_revision = "dddf9be580f5"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "domains",
        column_name="name",
        type_=sa.types.Unicode(length=64),
    )
    op.alter_column(
        "groups",
        column_name="name",
        type_=sa.types.Unicode(length=64),
    )


def downgrade():
    op.alter_column(
        "domains",
        column_name="name",
        type_=sa.String(length=64),
    )
    op.alter_column(
        "groups",
        column_name="name",
        type_=sa.String(length=64),
    )
