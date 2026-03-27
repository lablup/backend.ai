"""fix_destory_typo_in_audit_logs_operation_column

Revision ID: 81f2dd702d93
Revises: a1b2c3d4e5f6
Create Date: 2026-01-14 10:13:17.170033

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "81f2dd702d93"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Fix typo: "destory" -> "destroy" in audit_logs.operation column
    op.execute(sa.text("UPDATE audit_logs SET operation = 'destroy' WHERE operation = 'destory'"))


def downgrade() -> None:
    # Revert: "destroy" -> "destory" in audit_logs.operation column
    op.execute(sa.text("UPDATE audit_logs SET operation = 'destory' WHERE operation = 'destroy'"))
