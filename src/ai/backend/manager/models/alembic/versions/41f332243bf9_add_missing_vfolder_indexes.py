"""add-missing-vfolder-indexes

Revision ID: 41f332243bf9
Revises: 7ff52ff68bfc
Create Date: 2024-02-28 17:27:40.387122

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "41f332243bf9"
down_revision = "7ff52ff68bfc"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(op.f("ix_vfolders_host"), "vfolders", ["host"], unique=False)
    op.create_index(
        op.f("ix_vfolders_ownership_type"), "vfolders", ["ownership_type"], unique=False
    )
    op.create_index(op.f("ix_vfolders_status"), "vfolders", ["status"], unique=False)
    op.create_index(op.f("ix_vfolders_usage_mode"), "vfolders", ["usage_mode"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_vfolders_usage_mode"), table_name="vfolders")
    op.drop_index(op.f("ix_vfolders_status"), table_name="vfolders")
    op.drop_index(op.f("ix_vfolders_ownership_type"), table_name="vfolders")
    op.drop_index(op.f("ix_vfolders_host"), table_name="vfolders")
