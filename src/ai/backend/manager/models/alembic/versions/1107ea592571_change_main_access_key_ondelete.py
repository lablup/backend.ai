"""change_main_access_key_ondelete

Revision ID: 1107ea592571
Revises: d3f8c74bf148
Create Date: 2023-12-11 20:54:36.573832

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "1107ea592571"
down_revision = "d3f8c74bf148"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("fk_users_main_access_key_keypairs", "users", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_users_main_access_key_keypairs"),
        "users",
        "keypairs",
        ["main_access_key"],
        ["access_key"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint(op.f("fk_users_main_access_key_keypairs"), "users", type_="foreignkey")
    op.create_foreign_key(
        "fk_users_main_access_key_keypairs",
        "users",
        "keypairs",
        ["main_access_key"],
        ["access_key"],
        ondelete="RESTRICT",
    )
