"""mark customized images and record the user each was committed for

Adds two columns and backfills both from the ``ai.backend.customized-image.owner``
label, which stays as the scan's write-time input and is read to decide nothing.

``images.customized`` says a session commit made the image — a kind. ``images.creator_id``
says who it was made for — a person, provenance rather than ownership, which stays the
scope-virtual entity-entity path alone. They are separate because the person can go
while the kind stays: a label naming a user nobody knows, or a creator later purged,
leaves an image that is still customized and reachable by nobody.

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
_OWNER_LABEL: Final = "ai.backend.customized-image.owner"

# The label's presence is the whole question; its value is not read here.
_BACKFILL_CUSTOMIZED: Final = sa.text(f"""
    UPDATE images
    SET customized = true
    WHERE labels ->> '{_OWNER_LABEL}' IS NOT NULL
""")

# The label reads ``<visibility>:<user id>``. Only a well-formed UUID after the colon
# names a user; anything else leaves the column empty, as an unreadable label always did.
# The image stays marked customized either way, so it does not fall open.
_BACKFILL_CREATOR: Final = sa.text(f"""
    UPDATE images
    SET creator_id = split_part(labels ->> '{_OWNER_LABEL}', ':', 2)::uuid
    FROM users
    WHERE labels ->> '{_OWNER_LABEL}' IS NOT NULL
      AND split_part(labels ->> '{_OWNER_LABEL}', ':', 2)
          ~ '^[0-9a-fA-F]{{8}}-[0-9a-fA-F]{{4}}-[0-9a-fA-F]{{4}}-[0-9a-fA-F]{{4}}-[0-9a-fA-F]{{12}}$'
      AND users.uuid = split_part(labels ->> '{_OWNER_LABEL}', ':', 2)::uuid
""")


def upgrade() -> None:
    op.add_column(
        "images",
        sa.Column("customized", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
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
    """Mark every image an owner label names and write the creator each label resolves
    to. Takes its connection so a test can run it against a real database — static
    analysis does not reach SQL."""
    conn.execute(_BACKFILL_CUSTOMIZED)
    conn.execute(_BACKFILL_CREATOR)


def downgrade() -> None:
    op.drop_index(_INDEX_NAME, table_name="images")
    op.drop_constraint(op.f("fk_images_creator_id_users"), "images", type_="foreignkey")
    op.drop_column("images", "creator_id")
    op.drop_column("images", "customized")
