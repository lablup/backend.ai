"""Create error_logs table

Revision ID: d2aafa234374
Revises: 3bb80d1887d6
Create Date: 2020-02-12 13:55:12.450743

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text

from ai.backend.manager.models.base import GUID, IDColumn

# revision identifiers, used by Alembic.
revision = "d2aafa234374"
down_revision = "3bb80d1887d6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "error_logs",
        IDColumn(),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True
        ),
        sa.Column(
            "severity",
            sa.Enum("critical", "error", "warning", "info", "debug", name="errorlog_severity"),
            index=True,
        ),
        sa.Column("source", sa.String),
        sa.Column("user", GUID, sa.ForeignKey("users.uuid"), nullable=True, index=True),
        sa.Column("is_read", sa.Boolean, default=False, index=True),
        sa.Column("is_cleared", sa.Boolean, default=False, index=True),
        sa.Column("message", sa.Text),
        sa.Column("context_lang", sa.String),
        sa.Column("context_env", postgresql.JSONB()),
        sa.Column("request_url", sa.String, nullable=True),
        sa.Column("request_status", sa.Integer, nullable=True),
        sa.Column("traceback", sa.Text, nullable=True),
    )


def downgrade():
    op.drop_table("error_logs")
    op.execute(text("DROP TYPE errorlog_severity"))
