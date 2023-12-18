"""rename_mem_stats

Revision ID: e7371ca5797a
Revises: 93e9d31d40bf
Create Date: 2017-10-10 13:01:37.169568

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "e7371ca5797a"
down_revision = "93e9d31d40bf"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("kernels", column_name="max_mem_bytes", new_column_name="mem_max_bytes")
    op.alter_column("kernels", column_name="cur_mem_bytes", new_column_name="mem_cur_bytes")


def downgrade():
    op.alter_column("kernels", column_name="mem_max_bytes", new_column_name="max_mem_bytes")
    op.alter_column("kernels", column_name="mem_cur_bytes", new_column_name="cur_mem_bytes")
