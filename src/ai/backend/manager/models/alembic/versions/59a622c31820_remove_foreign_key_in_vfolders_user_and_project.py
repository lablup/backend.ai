"""Remove foreign key constraint from vfolders to users and projects

Revision ID: 59a622c31820
Revises: 5d92c9cc930c
Create Date: 2024-07-08 22:54:20.762521

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "59a622c31820"
down_revision = "5d92c9cc930c"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("fk_vfolders_user_users", "vfolders", type_="foreignkey")
    op.drop_constraint("fk_vfolders_group_groups", "vfolders", type_="foreignkey")
    op.drop_constraint("ck_vfolders_ownership_type_match_with_user_or_group", "vfolders")
    op.drop_constraint("ck_vfolders_either_one_of_user_or_group", "vfolders")


def downgrade():
    op.create_foreign_key("fk_vfolders_group_groups", "vfolders", "groups", ["group"], ["id"])
    op.create_foreign_key("fk_vfolders_user_users", "vfolders", "users", ["user"], ["uuid"])
    op.create_check_constraint(
        "ck_vfolders_ownership_type_match_with_user_or_group",
        "vfolders",
        "(ownership_type = 'user' AND \"user\" IS NOT NULL) OR "
        "(ownership_type = 'group' AND \"group\" IS NOT NULL)",
    )
    op.create_check_constraint(
        "ck_vfolders_either_one_of_user_or_group",
        "vfolders",
        '("user" IS NULL AND "group" IS NOT NULL) OR ("user" IS NOT NULL AND "group" IS NULL)',
    )
