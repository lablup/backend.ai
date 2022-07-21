import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from .base import GUID, IDColumn, metadata

__all__ = [
    "error_logs",
]

error_logs = sa.Table(
    "error_logs",
    metadata,
    IDColumn(),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    sa.Column(
        "severity", sa.Enum("critical", "error", "warning", name="errorlog_severity"), index=True
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
