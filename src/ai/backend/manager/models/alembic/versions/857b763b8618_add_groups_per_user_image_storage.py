"""add groups.container_registry

Revision ID: 857b763b8618
Revises: 75ea2b136830
Create Date: 2024-03-22 14:20:28.772534

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "857b763b8618"
down_revision = "75ea2b136830"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("groups", sa.Column("container_registry", postgresql.JSONB, nullable=True))
    op.add_column(
        "user_resource_policies",
        sa.Column(
            "max_customized_image_count",
            sa.Integer(),
            nullable=False,
            default=3,
            server_default="3",
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("user_resource_policies", "max_customized_image_count")
    op.drop_column("groups", "container_registry")
    # ### end Alembic commands ###