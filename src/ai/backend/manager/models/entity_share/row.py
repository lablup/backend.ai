from __future__ import annotations

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.common.data.entity.types import EntityType, RuntimeEntityID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.data.entity_share.types import (
    EntityShareData,
    EntityShareStatus,
)
from ai.backend.manager.models.base import GUID, Base, IntFlagType, StrEnumType
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin

__all__ = ("EntityShareRow",)


class EntityShareRow(LifecycleTimestampsMixin, Base):
    """The whole life of handing one entity to one scope: offered, taken, turned down,
    withdrawn, taken back.

    The name follows the state that lasts. A row spends its time accepted and only a
    moment pending, so it is a share carrying an offer rather than an offer that became
    something else.

    Both ends name a graph node by the pair that identifies it, which the graph holds
    unique, so each is a foreign key rather than a loose pair. Nothing that has no node
    can be lent or receive: the graph write would have nowhere to attach.

    A recipient that is an address has no node yet, so its pair stays empty until the
    offer is answered. ``MATCH FULL`` holds it to both or neither, and two checks hold
    the rest: one of the two ways of addressing is always there, and an accepted row
    always names the scope.

    One live row stands per recipient and entity, live meaning offered or taken. Ended
    rows pile up beside it, so the same entity can go out again after it came back.

    Only an offer still waiting runs out of time, which the last check holds: taking one
    clears the moment, and what was taken stands until it is given or taken back.
    """

    __tablename__ = "entity_shares"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["target_entity_type", "target_entity_id"],
            ["virtual_entities.entity_type", "virtual_entities.entity_id"],
            name="target",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["recipient_entity_type", "recipient_entity_id"],
            ["virtual_entities.entity_type", "virtual_entities.entity_id"],
            name="recipient",
            ondelete="CASCADE",
            match="FULL",
        ),
        sa.CheckConstraint(
            "recipient_entity_type IS NOT NULL OR recipient_email IS NOT NULL",
            name="addressed",
        ),
        sa.CheckConstraint(
            "status <> 'accepted' OR recipient_entity_type IS NOT NULL",
            name="accepted_resolved",
        ),
        sa.CheckConstraint(
            "status <> 'accepted' OR expires_at IS NULL",
            name="accepted_does_not_expire",
        ),
        sa.Index(
            "uq_entity_shares_live_email",
            "recipient_email",
            "target_entity_type",
            "target_entity_id",
            unique=True,
            postgresql_where=sa.text(
                "status IN ('pending', 'accepted') AND recipient_email IS NOT NULL"
            ),
        ),
        sa.Index(
            "uq_entity_shares_live_recipient",
            "recipient_entity_type",
            "recipient_entity_id",
            "target_entity_type",
            "target_entity_id",
            unique=True,
            postgresql_where=sa.text(
                "status IN ('pending', 'accepted') AND recipient_entity_type IS NOT NULL"
            ),
        ),
        sa.Index("ix_entity_shares_recipient", "recipient_entity_type", "recipient_entity_id"),
        sa.Index("ix_entity_shares_target", "target_entity_type", "target_entity_id"),
        sa.Index("ix_entity_shares_recipient_email", "recipient_email"),
    )

    id: Mapped[EntityShareID] = mapped_column(
        "id",
        GUID(EntityShareID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    #: Provenance, not authority: nothing is answered for by who sent the offer, so
    #: the account going away empties this and leaves the share standing.
    sharer_user_id: Mapped[UserID | None] = mapped_column(
        "sharer_user_id",
        GUID(UserID),
        sa.ForeignKey("users.uuid", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
    )
    recipient_entity_type: Mapped[EntityType | None] = mapped_column(
        "recipient_entity_type", sa.String(length=32), nullable=True
    )
    recipient_entity_id: Mapped[UUID | None] = mapped_column(
        "recipient_entity_id", GUID(), nullable=True
    )
    recipient_email: Mapped[str | None] = mapped_column(
        "recipient_email", sa.String(length=64), nullable=True
    )
    target_entity_type: Mapped[EntityType] = mapped_column(
        "target_entity_type", sa.String(length=32), nullable=False
    )
    target_entity_id: Mapped[UUID] = mapped_column("target_entity_id", GUID(), nullable=False)
    permission_cap: Mapped[Permission | None] = mapped_column(
        "permission_cap", IntFlagType(Permission), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        "expires_at", sa.DateTime(timezone=True), nullable=True
    )
    status: Mapped[EntityShareStatus] = mapped_column(
        "status",
        StrEnumType(EntityShareStatus),
        nullable=False,
        default=EntityShareStatus.PENDING,
        server_default=EntityShareStatus.PENDING.value,
    )

    def _recipient(self) -> RuntimeEntityID | None:
        node_type = self.recipient_entity_type
        node_id = self.recipient_entity_id
        if node_type is None or node_id is None:
            return None
        return RuntimeEntityID(node_type, node_id)

    def to_data(self) -> EntityShareData:
        return EntityShareData(
            id=self.id,
            sharer_user_id=self.sharer_user_id,
            recipient=self._recipient(),
            recipient_email=self.recipient_email,
            target=RuntimeEntityID(self.target_entity_type, self.target_entity_id),
            permission_cap=self.permission_cap,
            expires_at=self.expires_at,
            status=self.status,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
