"""Update AuditLogRow.request_id column type to String, and AuditLogRow.entity_id to Nullable

Revision ID: c7fedaca4883
Revises: 305e3ddc20a7
Create Date: 2025-04-15 09:34:42.257126

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "c7fedaca4883"
down_revision = "305e3ddc20a7"
branch_labels = None
depends_on = None

NULL_UUID = "00000000-0000-0000-0000-000000000000"


def upgrade() -> None:
    op.alter_column(
        "audit_logs",
        "request_id",
        type_=sa.String(),
        nullable=True,
    )

    op.execute(f"""
        UPDATE audit_logs SET request_id = NULL
        WHERE request_id = '{NULL_UUID}'
    """)

    op.alter_column(
        "audit_logs",
        "entity_id",
        type_=sa.String(),
        nullable=True,
    )

    op.execute(f"""
        UPDATE audit_logs SET entity_id = NULL
        WHERE entity_id = '{NULL_UUID}'
    """)


def downgrade() -> None:
    # NOTE: This downgrade is not reversible.
    op.execute(f"""
        UPDATE audit_logs SET request_id = '{NULL_UUID}'
    """)

    op.alter_column(
        "audit_logs",
        "request_id",
        type_=GUID(),
        nullable=False,
        postgresql_using="request_id::uuid",
    )

    op.execute(f"""
        UPDATE audit_logs
        SET entity_id = '{NULL_UUID}'
        WHERE entity_id IS NULL
    """)

    op.alter_column(
        "audit_logs",
        "entity_id",
        existing_type=sa.String(),
        nullable=False,
    )
