"""change-kernel-identification

Revision ID: 854bd902b1bc
Revises: 0f3bc98edaa0
Create Date: 2017-08-21 17:08:20.581565

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "854bd902b1bc"
down_revision = "0f3bc98edaa0"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint(
        "fk_vfolder_attachment_vfolder_vfolders", "vfolder_attachment", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_vfolder_attachment_kernel_kernels", "vfolder_attachment", type_="foreignkey"
    )
    op.drop_constraint("pk_kernels", "kernels", type_="primary")
    op.add_column(
        "kernels",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
    )
    op.add_column(
        "kernels", sa.Column("role", sa.String(length=16), nullable=False, default="master")
    )
    op.create_primary_key("pk_kernels", "kernels", ["id"])
    op.alter_column(
        "kernels",
        "sess_id",
        existing_type=postgresql.UUID(),
        type_=sa.String(length=64),
        nullable=True,
        existing_server_default=sa.text("uuid_generate_v4()"),
    )
    op.create_index(op.f("ix_kernels_sess_id"), "kernels", ["sess_id"], unique=False)
    op.create_index(op.f("ix_kernels_sess_id_role"), "kernels", ["sess_id", "role"], unique=False)
    op.create_foreign_key(
        "fk_vfolder_attachment_vfolder_vfolders",
        "vfolder_attachment",
        "vfolders",
        ["vfolder"],
        ["id"],
        onupdate="CASCADE",
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_vfolder_attachment_kernel_kernels",
        "vfolder_attachment",
        "kernels",
        ["kernel"],
        ["id"],
        onupdate="CASCADE",
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint(
        "fk_vfolder_attachment_vfolder_vfolders", "vfolder_attachment", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_vfolder_attachment_kernel_kernels", "vfolder_attachment", type_="foreignkey"
    )
    op.drop_constraint("pk_kernels", "kernels", type_="primary")
    op.drop_index(op.f("ix_kernels_sess_id"), table_name="kernels")
    op.drop_index(op.f("ix_kernels_sess_id_role"), table_name="kernels")
    op.alter_column(
        "kernels",
        "sess_id",
        existing_type=sa.String(length=64),
        type_=postgresql.UUID(),
        nullable=False,
        existing_server_default=sa.text("uuid_generate_v4()"),
        postgresql_using="sess_id::uuid",
    )
    op.create_primary_key("pk_kernels", "kernels", ["sess_id"])
    op.drop_column("kernels", "id")
    op.drop_column("kernels", "role")
    op.create_foreign_key(
        "fk_vfolder_attachment_vfolder_vfolders",
        "vfolder_attachment",
        "vfolders",
        ["vfolder"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_vfolder_attachment_kernel_kernels",
        "vfolder_attachment",
        "kernels",
        ["kernel"],
        ["sess_id"],
    )
