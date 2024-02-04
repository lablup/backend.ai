"""Add sudo_session_enabled

Revision ID: 4871d46ba31b
Revises: d04592473df7
Create Date: 2023-09-01 07:02:30.868334

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql.expression import false

# revision identifiers, used by Alembic.
revision = "4871d46ba31b"
down_revision = "d04592473df7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "sudo_session_enabled",
            sa.BOOLEAN(),
            default=False,
            nullable=False,
            server_default=false(),
        ),
    )


def downgrade():
    op.drop_column("users", "sudo_session_enabled")
