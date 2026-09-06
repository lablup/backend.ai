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

_LIVE_EMAIL_INDEX: Final = "uq_entity_shares_live_email"
_LIVE_RECIPIENT_INDEX: Final = "uq_entity_shares_live_recipient"
_TARGET_INDEX: Final = "ix_entity_shares_target"
_EMAIL_INDEX: Final = "ix_entity_shares_recipient_email"
_RECIPIENT_INDEX: Final = "ix_entity_shares_recipient"

_ADDRESSED: Final = "addressed"

_BACKFILL_RECIPIENT: Final = sa.text("""
    UPDATE entity_shares s
    SET recipient_entity_type = 'project', recipient_entity_id = g.id
    FROM users u
    JOIN groups g ON g.type = 'personal' AND g.creator_id = u.uuid
    WHERE s.recipient_email = u.email AND s.status = 'accepted'
""")

_DROP_TARGETS_WITHOUT_A_NODE: Final = sa.text("""
    DELETE FROM entity_shares s
    WHERE NOT EXISTS (
        SELECT 1 FROM virtual_entities ve
        WHERE ve.entity_type = s.target_entity_type AND ve.entity_id = s.target_entity_id
    )
""")


def upgrade() -> None:
    op.drop_index(_OLD_EMAIL_INDEX, table_name="entity_invitations")
    op.drop_index(_OLD_TARGET_INDEX, table_name="entity_invitations")
    op.drop_index(_OLD_PENDING_INDEX, table_name="entity_invitations")
    op.rename_table("entity_invitations", "entity_shares")
    op.alter_column("entity_shares", "inviter_user_id", new_column_name="sharer_user_id")
    op.drop_constraint(
        op.f("fk_entity_invitations_inviter_user_id_users"), "entity_shares", type_="foreignkey"
    )
    op.alter_column("entity_shares", "sharer_user_id", nullable=True)
    op.create_foreign_key(
        "sharer_user_id",
        "entity_shares",
        "users",
        ["sharer_user_id"],
        ["uuid"],
        onupdate="CASCADE",
        ondelete="SET NULL",
    )
    op.alter_column(
        "entity_shares", "invitee_email", new_column_name="recipient_email", nullable=True
    )
    op.add_column(
        "entity_shares", sa.Column("recipient_entity_type", sa.String(length=32), nullable=True)
    )
    op.add_column("entity_shares", sa.Column("recipient_entity_id", GUID, nullable=True))
    op.add_column(
        "entity_shares",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(_BACKFILL_RECIPIENT)
    op.execute(_DROP_TARGETS_WITHOUT_A_NODE)
    op.create_foreign_key(
        "target",
        "entity_shares",
        "virtual_entities",
        ["target_entity_type", "target_entity_id"],
        ["entity_type", "entity_id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "recipient",
        "entity_shares",
        "virtual_entities",
        ["recipient_entity_type", "recipient_entity_id"],
        ["entity_type", "entity_id"],
        ondelete="CASCADE",
        match="FULL",
    )

    op.create_check_constraint(
        _ADDRESSED,
        "entity_shares",
        "recipient_entity_type IS NOT NULL OR recipient_email IS NOT NULL",
    )
    op.create_index(
        _LIVE_EMAIL_INDEX,
        "entity_shares",
        ["recipient_email", "target_entity_type", "target_entity_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending' AND recipient_email IS NOT NULL"),
    )
    op.create_index(
        _LIVE_RECIPIENT_INDEX,
        "entity_shares",
        ["recipient_virtual_entity_id", "target_entity_type", "target_entity_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending' AND recipient_virtual_entity_id IS NOT NULL"),
    )
    op.create_index(_TARGET_INDEX, "entity_shares", ["target_entity_type", "target_entity_id"])
    op.create_index(_EMAIL_INDEX, "entity_shares", ["recipient_email"])


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM entity_shares WHERE recipient_email IS NULL"))
    op.drop_constraint(op.f("fk_entity_shares_recipient"), "entity_shares", type_="foreignkey")
    op.drop_constraint(op.f("fk_entity_shares_target"), "entity_shares", type_="foreignkey")
    op.drop_index(_RECIPIENT_INDEX, table_name="entity_shares")
    op.drop_index(_EMAIL_INDEX, table_name="entity_shares")
    op.drop_index(_TARGET_INDEX, table_name="entity_shares")
    op.drop_index(_LIVE_RECIPIENT_INDEX, table_name="entity_shares")
    op.drop_index(_LIVE_EMAIL_INDEX, table_name="entity_shares")
    op.drop_constraint(op.f(f"ck_entity_shares_{_ADDRESSED}"), "entity_shares", type_="check")
    op.drop_column("entity_shares", "expires_at")
    op.drop_column("entity_shares", "recipient_entity_id")
    op.drop_column("entity_shares", "recipient_entity_type")
    op.alter_column(
        "entity_shares", "recipient_email", new_column_name="invitee_email", nullable=False
    )
    op.drop_constraint(op.f("fk_entity_shares_sharer_user_id"), "entity_shares", type_="foreignkey")
    op.execute(sa.text("DELETE FROM entity_shares WHERE sharer_user_id IS NULL"))
    op.alter_column("entity_shares", "sharer_user_id", nullable=False)
    op.alter_column("entity_shares", "sharer_user_id", new_column_name="inviter_user_id")
    op.create_foreign_key(
        "inviter_user_id",
        "entity_shares",
        "users",
        ["inviter_user_id"],
        ["uuid"],
        onupdate="CASCADE",
        ondelete="CASCADE",
    )
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
