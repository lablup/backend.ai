"""add image_id to kernels and image_ids to sessions

Revision ID: cd067180a8b1
Revises: d8e4f2a1b3c7
Create Date: 2026-04-16

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "cd067180a8b1"
down_revision = "d8e4f2a1b3c7"
# Part of: 26.3.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # --- kernels.image_id ---
    columns = [c["name"] for c in inspector.get_columns("kernels")]
    if "image_id" not in columns:
        op.add_column(
            "kernels",
            sa.Column(
                "image_id",
                postgresql.UUID(as_uuid=True),
                nullable=True,
            ),
        )

    fk_columns = [fk["constrained_columns"] for fk in inspector.get_foreign_keys("kernels")]
    if ["image_id"] not in fk_columns:
        op.create_foreign_key(
            "fk_kernels_image_id",
            "kernels",
            "images",
            ["image_id"],
            ["id"],
            ondelete="SET NULL",
        )

    indexes = [idx["name"] for idx in inspector.get_indexes("kernels")]
    if "ix_kernels_image_id" not in indexes:
        op.create_index(
            "ix_kernels_image_id",
            "kernels",
            ["image_id"],
        )

    # Backfill kernels.image_id from images table
    op.execute(
        sa.text(
            "UPDATE kernels SET image_id = images.id"
            " FROM images"
            " WHERE kernels.image = images.name"
            "   AND kernels.architecture = images.architecture"
            "   AND kernels.image_id IS NULL"
        )
    )

    # --- sessions.image_ids ---
    session_columns = [c["name"] for c in inspector.get_columns("sessions")]
    if "image_ids" not in session_columns:
        op.add_column(
            "sessions",
            sa.Column(
                "image_ids",
                postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
                nullable=True,
            ),
        )

    # Backfill sessions.image_ids from kernels
    op.execute(
        sa.text(
            "UPDATE sessions SET image_ids = subq.ids"
            " FROM ("
            "   SELECT session_id, array_agg(DISTINCT image_id) AS ids"
            "   FROM kernels"
            "   WHERE image_id IS NOT NULL"
            "   GROUP BY session_id"
            " ) subq"
            " WHERE sessions.id = subq.session_id"
            "   AND sessions.image_ids IS NULL"
        )
    )


def downgrade() -> None:
    op.drop_column("sessions", "image_ids")
    op.drop_index("ix_kernels_image_id", table_name="kernels")
    op.drop_column("kernels", "image_id")
