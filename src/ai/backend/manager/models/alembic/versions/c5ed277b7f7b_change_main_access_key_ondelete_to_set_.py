"""change_main_access_key_ondelete_to_set_null

Revision ID: c5ed277b7f7b
Revises: d3f8c74bf148
Create Date: 2024-01-11 15:37:24.097596

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "c5ed277b7f7b"
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
