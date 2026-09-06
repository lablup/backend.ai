"""add uuid_generate_v7 and use it for session, kernel and deployment ids

Revision ID: 8f3b1c7ad204
Revises: 5c1e7a2d9b40
Create Date: 2026-09-03

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.uuid7 import DROP_UUID_GENERATE_V7_DDL, UUID_GENERATE_V7_DDL

# Part of: NEXT_RELEASE_VERSION

# revision identifiers, used by Alembic.
revision = "8f3b1c7ad204"
down_revision = "5c1e7a2d9b40"
branch_labels = None
depends_on = None

# Existing rows keep their v4 ids; the two versions share the uuid type.
_TARGET_TABLES = (
    "sessions",
    "kernels",
    "endpoints",
    "deployment_revisions",
    "routings",
    "replica_groups",
)


def upgrade() -> None:
    op.execute(sa.text(UUID_GENERATE_V7_DDL))
    for table in _TARGET_TABLES:
        op.execute(sa.text(f"ALTER TABLE {table} ALTER COLUMN id SET DEFAULT uuid_generate_v7()"))


def downgrade() -> None:
    for table in _TARGET_TABLES:
        op.execute(sa.text(f"ALTER TABLE {table} ALTER COLUMN id SET DEFAULT uuid_generate_v4()"))
    op.execute(sa.text(DROP_UUID_GENERATE_V7_DDL))
