"""alter quota scope id format

Revision ID: eb50a33db353
Revises: a9eb2b002330
Create Date: 2023-07-01 13:18:13.037830

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "eb50a33db353"
down_revision = "a9eb2b002330"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(
        text(
            "UPDATE vfolders SET quota_scope_id = CONCAT(REPLACE(ownership_type::text, 'group',"
            " 'project'), ':', CONCAT(UUID(quota_scope_id), ''));"
        )
    )


def downgrade():
    conn = op.get_bind()
    conn.execute(text("UPDATE vfolders SET quota_scope_id = SPLIT_PART(quota_scope_id, ':', 2);"))
