"""expand sessions.name and kernels.session_name length

Revision ID: 99805291b6e0
Revises: 6e104991787d
Create Date: 2026-04-08 11:26:50.233348

The inference session name is constructed as ``f"{endpoint.name}-{route_id}"``
where ``route_id`` is a UUID string (36 chars). The previous VARCHAR(64)
limit on ``sessions.name`` and ``kernels.session_name`` caused
``StringDataRightTruncationError`` whenever a deployment name combined with
the route UUID exceeded 64 characters, which in turn broke DEPLOYING-phase
route provisioning.

Widen both columns to VARCHAR(128) so the combined ``deployment-route``
naming pattern fits without exceeding a sensible identifier length budget.
"""

# Part of: 26.3.0 (main)

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "99805291b6e0"
down_revision = "6e104991787d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "sessions",
        "name",
        existing_type=sa.String(length=64),
        type_=sa.String(length=128),
        existing_nullable=True,
    )
    op.alter_column(
        "kernels",
        "session_name",
        existing_type=sa.String(length=64),
        type_=sa.String(length=128),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "kernels",
        "session_name",
        existing_type=sa.String(length=128),
        type_=sa.String(length=64),
        existing_nullable=True,
    )
    op.alter_column(
        "sessions",
        "name",
        existing_type=sa.String(length=128),
        type_=sa.String(length=64),
        existing_nullable=True,
    )
