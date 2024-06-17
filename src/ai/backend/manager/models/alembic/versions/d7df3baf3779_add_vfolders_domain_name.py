"""add vfolders domain name

Revision ID: d7df3baf3779
Revises: 5d92c9cc930c
Create Date: 2024-06-11 16:39:26.648608

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "d7df3baf3779"
down_revision = "5d92c9cc930c"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    op.add_column("vfolders", sa.Column("domain_name", sa.String(length=64), nullable=True))

    conn.execute(
        text(
            """\
        UPDATE vfolders
        SET domain_name = COALESCE(
            (SELECT domain_name FROM users WHERE vfolders.user = users.uuid),
            (SELECT domain_name FROM groups WHERE vfolders.group = groups.id)
        )
        WHERE domain_name IS NULL;
    """
        )
    )

    op.alter_column("vfolders", column_name="domain_name", nullable=False)
    op.create_index(op.f("ix_vfolders_domain_name"), "vfolders", ["domain_name"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_vfolders_domain_name"), table_name="vfolders")
    op.drop_column("vfolders", "domain_name")
