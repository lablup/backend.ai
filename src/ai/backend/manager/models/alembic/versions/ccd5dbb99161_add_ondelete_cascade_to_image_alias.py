"""add ondelete cascade to image alias

Revision ID: ccd5dbb99161
Revises: ba42cb865efe
Create Date: 2026-05-19 09:52:10.921004

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "ccd5dbb99161"
down_revision = "ba42cb865efe"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("fk_image_aliases_image_images", "image_aliases", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_image_aliases_image_images"),
        "image_aliases",
        "images",
        ["image"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_image_aliases_image_images"), "image_aliases", type_="foreignkey")
    op.create_foreign_key(
        "fk_image_aliases_image_images", "image_aliases", "images", ["image"], ["id"]
    )
