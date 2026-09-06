from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.common.data.entity.types import EntityID, EntityType, RuntimeEntityID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.virtual_entity import VirtualEntityID
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

    The recipient is a virtual entity, the coordinates the graph edge uses, so a project
    receives as well as a person. An address with no account yet stays an email until it
    is answered, and answering fills the virtual entity in — which is why both are
    nullable and two checks hold them: one of the two is always there, and an accepted
    row always names the node, which answering records.

    The target is a polymorphic pair with no foreign key. A pending row is not a graph
    edge, so it does not name the target's node either.
    """

    __tablename__ = "entity_shares"
    __table_args__ = (
        sa.CheckConstraint(
            "recipient_virtual_entity_id IS NOT NULL OR recipient_email IS NOT NULL",
            name="addressed",
        ),
        sa.CheckConstraint(
            "status <> 'accepted' OR recipient_virtual_entity_id IS NOT NULL",
            name="accepted_resolved",
        ),
        sa.Index(
            "uq_entity_shares_pending_email",
            "recipient_email",
            "target_entity_type",
            "target_entity_id",
            unique=True,
            postgresql_where=sa.text("status = 'pending' AND recipient_email IS NOT NULL"),
        ),
        sa.Index(
            "uq_entity_shares_pending_recipient",
            "recipient_virtual_entity_id",
            "target_entity_type",
            "target_entity_id",
            unique=True,
            postgresql_where=sa.text(
                "status = 'pending' AND recipient_virtual_entity_id IS NOT NULL"
            ),
        ),
        sa.Index("ix_entity_shares_target", "target_entity_type", "target_entity_id"),
        sa.Index("ix_entity_shares_recipient_email", "recipient_email"),
    )

    id: Mapped[EntityShareID] = mapped_column(
        "id",
        GUID(EntityShareID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    sharer_user_id: Mapped[UserID] = mapped_column(
        "sharer_user_id",
        GUID(UserID),
        sa.ForeignKey("users.uuid", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    recipient_virtual_entity_id: Mapped[VirtualEntityID | None] = mapped_column(
        "recipient_virtual_entity_id",
        GUID(VirtualEntityID),
        sa.ForeignKey("virtual_entities.id", ondelete="CASCADE"),
        nullable=True,
    )
    recipient_email: Mapped[str | None] = mapped_column(
        "recipient_email", sa.String(length=64), nullable=True
    )
    target_entity_type: Mapped[EntityType] = mapped_column(
        "target_entity_type", sa.String(length=32), nullable=False
    )
    target_entity_id: Mapped[EntityID] = mapped_column("target_entity_id", GUID(), nullable=False)
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

    def to_data(self) -> EntityShareData:
        return EntityShareData(
            id=self.id,
            sharer_user_id=self.sharer_user_id,
            recipient_virtual_entity_id=self.recipient_virtual_entity_id,
            recipient_email=self.recipient_email,
            target=RuntimeEntityID(self.target_entity_type, self.target_entity_id),
            permission_cap=self.permission_cap,
            expires_at=self.expires_at,
            status=self.status,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
