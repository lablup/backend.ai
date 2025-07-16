"""Add triggered_by to AuditLogRow

Revision ID: a5ef73b01e97
Revises: 60bcbf00a96e
Create Date: 2025-07-14 02:10:48.791146

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a5ef73b01e97"
down_revision = "60bcbf00a96e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_logs", sa.Column("triggered_by", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("audit_logs", "triggered_by")
