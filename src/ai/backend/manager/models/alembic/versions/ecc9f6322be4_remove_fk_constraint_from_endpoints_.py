"""Remove foreign key constraint from endpoints.image column

Revision ID: ecc9f6322be4
Revises: f6ca2f2d04c1
Create Date: 2025-02-07 00:58:05.211395

"""

from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "ecc9f6322be4"
down_revision = "f6ca2f2d04c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("fk_endpoints_image_images", "endpoints", type_="foreignkey")
    op.alter_column("endpoints", "image", existing_type=GUID, nullable=True)
    op.create_check_constraint(
        constraint_name="ck_image_required_unless_destroyed",
        table_name="endpoints",
        condition="lifecycle_stage = 'destroyed' OR image IS NOT NULL",
    )


def downgrade() -> None:
    op.create_foreign_key(
        "fk_endpoints_image_images", "endpoints", "images", ["image"], ["id"], ondelete="RESTRICT"
    )
    op.alter_column("endpoints", "image", existing_type=GUID, nullable=False)
    op.drop_constraint(
        constraint_name="ck_image_required_unless_destroyed", table_name="endpoints", type_="check"
    )
