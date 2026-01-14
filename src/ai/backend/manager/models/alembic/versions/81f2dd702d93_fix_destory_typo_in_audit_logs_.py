"""fix_destory_typo_in_audit_logs_operation_column

Revision ID: 81f2dd702d93
Revises: 71343531dd5a
Create Date: 2026-01-14 10:13:17.170033

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '81f2dd702d93'
down_revision = '71343531dd5a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Fix typo: "destory" -> "destroy" in audit_logs.operation column
    op.execute(
        sa.text(
            "UPDATE audit_logs SET operation = 'destroy' WHERE operation = 'destory'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE audit_logs SET operation = 'destroy_multi' WHERE operation = 'destory_multi'"
        )
    )


def downgrade() -> None:
    # Revert: "destroy" -> "destory" in audit_logs.operation column
    op.execute(
        sa.text(
            "UPDATE audit_logs SET operation = 'destory' WHERE operation = 'destroy'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE audit_logs SET operation = 'destory_multi' WHERE operation = 'destroy_multi'"
        )
    )
