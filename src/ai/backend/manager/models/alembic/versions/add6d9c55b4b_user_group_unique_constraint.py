"""user_group_unique_constraint

Revision ID: add6d9c55b4b
Revises: d3f8c74bf148
Create Date: 2024-01-03 17:11:22.298007

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "add6d9c55b4b"
down_revision = "d3f8c74bf148"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(
        "uq_user_id_group_id", "association_groups_users", ["user_id", "group_id"]
    )


def downgrade():
    op.drop_constraint("uq_user_id_group_id", "association_groups_users", type_="unique")
