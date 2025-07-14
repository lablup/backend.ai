"""Add user_id to AuditLogRow

Revision ID: 88a86ae26669
Revises: bf39b34717d4
Create Date: 2025-07-14 01:56:18.344601

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "88a86ae26669"
down_revision = "bf39b34717d4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_logs", sa.Column("user_id", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("audit_logs", "user_id")
