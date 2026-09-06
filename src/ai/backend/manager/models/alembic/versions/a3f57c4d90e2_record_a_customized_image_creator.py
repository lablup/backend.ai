"""record the user a customized image was committed for

Adds ``images.creator_id`` — provenance, not ownership, which stays the
scope-virtual entity-entity path alone — and backfills it from the
``ai.backend.customized-image.owner`` label. The label stays as the scan's write-time
input; nothing reads it to decide ownership any more.

The graph edges of images already on file are not written here. They come with the one
ownership-data migration, which provisions every entity at once.

Revision ID: a3f57c4d90e2
Revises: e4c8b1d70a35
Create Date: 2026-09-06 10:00:00

"""

# Part of: NEXT_RELEASE_VERSION

from typing import Final

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "a3f57c4d90e2"
down_revision = "e4c8b1d70a35"
branch_labels = None
depends_on = None

_INDEX_NAME: Final = "ix_images_creator_id"

# The label reads ``<visibility>:<user id>``. Only a well-formed UUID after the colon
# names a user; anything else leaves the column empty, as an unreadable label always did.
_BACKFILL: Final = sa.text("""
    UPDATE images
    SET creator_id = split_part(labels ->> 'ai.backend.customized-image.owner', ':', 2)::uuid
    FROM users
    WHERE labels ->> 'ai.backend.customized-image.owner' IS NOT NULL
      AND split_part(labels ->> 'ai.backend.customized-image.owner', ':', 2)
          ~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
      AND users.uuid
          = split_part(labels ->> 'ai.backend.customized-image.owner', ':', 2)::uuid
""")


def upgrade() -> None:
    op.add_column("images", sa.Column("creator_id", GUID(), nullable=True))
    op.create_foreign_key(
        op.f("fk_images_creator_id_users"),
        "images",
        "users",
        ["creator_id"],
        ["uuid"],
        ondelete="SET NULL",
    )
    backfill(op.get_bind())
    # The index goes on after the backfill: it describes the state it produces.
    op.create_index(_INDEX_NAME, "images", ["creator_id"])


def backfill(conn: sa.Connection) -> None:
    """Write the creator every customized image's owner label names. Takes its
    connection so a test can run it against a real database — static analysis does not
    reach SQL."""
    conn.execute(_BACKFILL)


def downgrade() -> None:
    op.drop_index(_INDEX_NAME, table_name="images")
    op.drop_constraint(op.f("fk_images_creator_id_users"), "images", type_="foreignkey")
    op.drop_column("images", "creator_id")
