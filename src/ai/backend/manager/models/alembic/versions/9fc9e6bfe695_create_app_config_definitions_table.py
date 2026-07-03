"""create app_config_definitions table

Introduce ``app_config_definitions`` — the explicitly admin-managed set of
registered ``config_name`` values and the foreign-key target for the scoped
app-config tables (BEP-1052). A config fragment may not exist for an
unregistered ``config_name``.

Revision ID: 9fc9e6bfe695
Revises: f3a8c2d51b94
Create Date: 2026-06-17

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import IDColumn

# revision identifiers, used by Alembic.
revision = "9fc9e6bfe695"
down_revision = "f3a8c2d51b94"
# Part of: 26.5.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_config_definitions",
        IDColumn(),
        sa.Column("config_name", sa.String(length=128), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("config_name", name="uq_app_config_definitions_config_name"),
    )


def downgrade() -> None:
    op.drop_table("app_config_definitions")
