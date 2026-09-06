"""rename entity_invitations to entity_shares

One row now carries the whole life of handing an entity to a scope: offered, taken,
turned down, withdrawn, taken back. The name follows the state that lasts, since a
row spends its time accepted and only a moment pending.

The recipient becomes a virtual entity, the coordinates the graph edge uses, so a
project can receive as well as a person. An address that has no account yet stays an
email until it is answered, and answering fills the virtual entity in.

Revision ID: b6f2c1e94a30
Revises: c7a4f1e9b023
Create Date: 2026-09-06 12:00:00

"""

# Part of: NEXT_RELEASE_VERSION

from typing import Final

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "b6f2c1e94a30"
down_revision = "c7a4f1e9b023"
branch_labels = None
depends_on = None

_OLD_PENDING_INDEX: Final = "uq_entity_invitations_pending"
_OLD_TARGET_INDEX: Final = "ix_entity_invitations_target"
_OLD_EMAIL_INDEX: Final = "ix_entity_invitations_invitee_email"

_PENDING_EMAIL_INDEX: Final = "uq_entity_shares_pending_email"
_PENDING_RECIPIENT_INDEX: Final = "uq_entity_shares_pending_recipient"
_TARGET_INDEX: Final = "ix_entity_shares_target"
_EMAIL_INDEX: Final = "ix_entity_shares_recipient_email"

_ADDRESSED: Final = "addressed"

_BACKFILL_RECIPIENT: Final = sa.text("""
    UPDATE entity_shares s
    SET recipient_virtual_entity_id = ve.id
    FROM users u
    JOIN groups g ON g.type = 'personal' AND g.creator_id = u.uuid
    JOIN virtual_entities ve ON ve.entity_type = 'project' AND ve.entity_id = g.id
    WHERE s.recipient_email = u.email AND s.status = 'accepted'
""")


def upgrade() -> None:
    op.drop_index(_OLD_EMAIL_INDEX, table_name="entity_invitations")
    op.drop_index(_OLD_TARGET_INDEX, table_name="entity_invitations")
    op.drop_index(_OLD_PENDING_INDEX, table_name="entity_invitations")
    op.rename_table("entity_invitations", "entity_shares")
    op.alter_column("entity_shares", "inviter_user_id", new_column_name="sharer_user_id")
    op.alter_column(
        "entity_shares", "invitee_email", new_column_name="recipient_email", nullable=True
    )
    op.add_column(
        "entity_shares",
        sa.Column(
            "recipient_virtual_entity_id",
            GUID,
            sa.ForeignKey("virtual_entities.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.add_column(
        "entity_shares",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(_BACKFILL_RECIPIENT)

    op.create_check_constraint(
        _ADDRESSED,
        "entity_shares",
        "recipient_virtual_entity_id IS NOT NULL OR recipient_email IS NOT NULL",
    )
    op.create_index(
        _PENDING_EMAIL_INDEX,
        "entity_shares",
        ["recipient_email", "target_entity_type", "target_entity_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending' AND recipient_email IS NOT NULL"),
    )
    op.create_index(
        _PENDING_RECIPIENT_INDEX,
        "entity_shares",
        ["recipient_virtual_entity_id", "target_entity_type", "target_entity_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending' AND recipient_virtual_entity_id IS NOT NULL"),
    )
    op.create_index(_TARGET_INDEX, "entity_shares", ["target_entity_type", "target_entity_id"])
    op.create_index(_EMAIL_INDEX, "entity_shares", ["recipient_email"])


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM entity_shares WHERE recipient_email IS NULL"))
    op.drop_index(_EMAIL_INDEX, table_name="entity_shares")
    op.drop_index(_TARGET_INDEX, table_name="entity_shares")
    op.drop_index(_PENDING_RECIPIENT_INDEX, table_name="entity_shares")
    op.drop_index(_PENDING_EMAIL_INDEX, table_name="entity_shares")
    op.drop_constraint(op.f(f"ck_entity_shares_{_ADDRESSED}"), "entity_shares", type_="check")
    op.drop_column("entity_shares", "expires_at")
    op.drop_column("entity_shares", "recipient_virtual_entity_id")
    op.alter_column(
        "entity_shares", "recipient_email", new_column_name="invitee_email", nullable=False
    )
    op.alter_column("entity_shares", "sharer_user_id", new_column_name="inviter_user_id")
    op.rename_table("entity_shares", "entity_invitations")
    op.create_index(
        _OLD_PENDING_INDEX,
        "entity_invitations",
        ["invitee_email", "target_entity_type", "target_entity_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )
    op.create_index(
        _OLD_TARGET_INDEX, "entity_invitations", ["target_entity_type", "target_entity_id"]
    )
    op.create_index(_OLD_EMAIL_INDEX, "entity_invitations", ["invitee_email"])
