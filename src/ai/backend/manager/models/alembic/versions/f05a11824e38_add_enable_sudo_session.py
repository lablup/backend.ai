"""Add enable_sudo_session

Revision ID: f05a11824e38
Revises: ae7d4cd92aa7
Create Date: 2023-09-01 05:44:20.955402

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql.expression import false

# revision identifiers, used by Alembic.
revision = "f05a11824e38"
down_revision = "ae7d4cd92aa7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "enable_sudo_session",
            sa.BOOLEAN(),
            default=False,
            nullable=False,
            server_default=false(),
        ),
    )
    pass


def downgrade():
    op.drop_column("users", "enable_sudo_session")
    pass
