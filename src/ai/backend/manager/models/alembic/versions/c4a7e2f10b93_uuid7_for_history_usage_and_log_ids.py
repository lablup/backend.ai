"""use uuid_generate_v7 for history, usage and log ids

Revision ID: c4a7e2f10b93
Revises: c1d7a3e9f5b2
Create Date: 2026-09-03

"""

import sqlalchemy as sa
from alembic import op

# Part of: NEXT_RELEASE_VERSION

# revision identifiers, used by Alembic.
revision = "c4a7e2f10b93"
down_revision = "c1d7a3e9f5b2"
branch_labels = None
depends_on = None

# Existing rows keep their v4 ids; the two versions share the uuid type.
_TARGET_TABLES = (
    "session_scheduling_history",
    "kernel_scheduling_history",
    "deployment_history",
    "route_history",
    "replica_group_history",
    "kernel_usage_records",
    "domain_usage_buckets",
    "project_usage_buckets",
    "user_usage_buckets",
    "event_logs",
    "audit_logs",
    "audit_log_scopes",
    "error_logs",
    "login_history",
)


def upgrade() -> None:
    for table in _TARGET_TABLES:
        op.execute(sa.text(f"ALTER TABLE {table} ALTER COLUMN id SET DEFAULT uuid_generate_v7()"))


def downgrade() -> None:
    for table in _TARGET_TABLES:
        op.execute(sa.text(f"ALTER TABLE {table} ALTER COLUMN id SET DEFAULT uuid_generate_v4()"))
