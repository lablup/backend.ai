"""add model service token log

Revision ID: 02535458c0b3
Revises: ae7d4cd92aa7
Create Date: 2023-08-25 03:34:01.750965

"""

from enum import Enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from ai.backend.manager.models.base import GUID, EnumValueType, ForeignKeyIDColumn

# revision identifiers, used by Alembic.
revision = "02535458c0b3"
down_revision = "ae7d4cd92aa7"
branch_labels = None
depends_on = None


class EndpointLifecycle(Enum):
    CREATED = "created"
    DESTROYING = "destroying"
    DESTROYED = "destroyed"


endpointlifecycle_choices = [v.value for v in EndpointLifecycle]
endpointlifecycle = postgresql.ENUM(*endpointlifecycle_choices, name="endpointlifecycle")


def upgrade():
    endpointlifecycle.create(op.get_bind())
    op.create_table(
        "endpoint_tokens",
        sa.Column("token", sa.VARCHAR(1024), primary_key=True),
        sa.Column("domain", sa.String(length=64), nullable=False),
        sa.Column("project", GUID(), nullable=False),
        ForeignKeyIDColumn("endpoint", "endpoints.id"),
        ForeignKeyIDColumn("session_owner", "users.uuid"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True
        ),
    )
    op.add_column(
        "endpoints",
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True
        ),
    )
    op.add_column(
        "endpoints",
        sa.Column("destroyed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "endpoints",
        sa.Column(
            "lifecycle_stage",
            EnumValueType(EndpointLifecycle),
            nullable=False,
            default=EndpointLifecycle.CREATED,
            server_default="created",
        ),
    )
    op.add_column(
        "routings",
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True
        ),
    )


def downgrade():
    op.drop_column("endpoints", "created_at")
    op.drop_column("endpoints", "destroyed_at")
    op.drop_column("endpoints", "lifecycle_stage")
    op.drop_column("routings", "created_at")
    op.drop_table("endpoint_tokens")
