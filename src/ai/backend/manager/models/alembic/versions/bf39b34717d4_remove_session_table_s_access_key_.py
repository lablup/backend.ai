"""Drop Session, and Kernel's fk constraints to users and keypairs

Revision ID: bf39b34717d4
Revises: 01f0ed604819
Create Date: 2025-07-03 04:22:25.692164

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "bf39b34717d4"
down_revision = "01f0ed604819"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("fk_sessions_user_uuid_users", "sessions", type_="foreignkey")
    op.drop_constraint("fk_kernels_user_uuid_users", "kernels", type_="foreignkey")
    op.drop_constraint("fk_sessions_access_key_keypairs", "sessions", type_="foreignkey")
    op.drop_constraint("fk_kernels_access_key_keypairs", "kernels", type_="foreignkey")


def downgrade() -> None:
    op.create_foreign_key(
        "fk_sessions_user_uuid_users", "sessions", "users", ["user_uuid"], ["uuid"]
    )
    op.create_foreign_key("fk_kernels_user_uuid_users", "kernels", "users", ["user_uuid"], ["uuid"])
    op.create_foreign_key(
        "fk_sessions_access_key_keypairs", "sessions", "keypairs", ["access_key"], ["access_key"]
    )
    op.create_foreign_key(
        "fk_kernels_access_key_keypairs", "kernels", "keypairs", ["access_key"], ["access_key"]
    )
