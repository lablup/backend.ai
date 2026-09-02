from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.entity_invitation import EntityInvitationID
from ai.backend.common.data.entity.types import EntityID, EntityType, RuntimeEntityID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.data.entity_invitation.types import (
    EntityInvitationData,
    EntityInvitationStatus,
)
from ai.backend.manager.models.base import GUID, Base, IntFlagType, StrEnumType
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin

__all__ = ("EntityInvitationRow",)


class EntityInvitationRow(LifecycleTimestampsMixin, Base):
    """An offer of one existing entity to one person, settled by their answer.

    The target is a polymorphic ``(target_entity_type, target_entity_id)`` pair with no
    foreign key; the invitation is not a graph edge, so it does not name the target's
    virtual entity node. Accepting writes the entity membership the ``permission_cap``
    bounds.

    The invitee is an email rather than a user id: an invitation may name someone who
    has no account yet. Reads resolve the requester's own email instead
    (``models/entity_invitation/scopes.py``).
    """

    __tablename__ = "entity_invitations"
    __table_args__ = (
        sa.Index(
            "uq_entity_invitations_pending",
            "invitee_email",
            "target_entity_type",
            "target_entity_id",
            unique=True,
            postgresql_where=sa.text("status = 'pending'"),
        ),
        sa.Index(
            "ix_entity_invitations_target",
            "target_entity_type",
            "target_entity_id",
        ),
        sa.Index("ix_entity_invitations_invitee_email", "invitee_email"),
    )

    id: Mapped[EntityInvitationID] = mapped_column(
        "id",
        GUID(EntityInvitationID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v4()"),
    )
    inviter_user_id: Mapped[UserID] = mapped_column(
        "inviter_user_id",
        GUID(UserID),
        sa.ForeignKey("users.uuid", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    invitee_email: Mapped[str] = mapped_column(
        "invitee_email", sa.String(length=64), nullable=False
    )
    target_entity_type: Mapped[EntityType] = mapped_column(
        "target_entity_type", sa.String(length=32), nullable=False
    )
    target_entity_id: Mapped[EntityID] = mapped_column("target_entity_id", GUID(), nullable=False)
    permission_cap: Mapped[Permission | None] = mapped_column(
        "permission_cap", IntFlagType(Permission), nullable=True
    )
    status: Mapped[EntityInvitationStatus] = mapped_column(
        "status",
        StrEnumType(EntityInvitationStatus),
        nullable=False,
        default=EntityInvitationStatus.PENDING,
        server_default=EntityInvitationStatus.PENDING.value,
    )

    def to_data(self) -> EntityInvitationData:
        return EntityInvitationData(
            id=self.id,
            inviter_user_id=self.inviter_user_id,
            invitee_email=self.invitee_email,
            target=RuntimeEntityID(self.target_entity_type, self.target_entity_id),
            permission_cap=self.permission_cap,
            status=self.status,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
