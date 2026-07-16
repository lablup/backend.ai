from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.data.role_invitation.types import (
    RoleInvitationData,
    RoleInvitationState,
)
from ai.backend.manager.models.base import GUID, Base, StrEnumType


class RoleInvitationRow(Base):  # type: ignore[misc]
    __tablename__ = "role_invitations"
    __table_args__ = (
        sa.Index(
            "uq_role_invitations_active",
            "invitee_user_id",
            "role_id",
            unique=True,
            postgresql_where=sa.text("state != 'accepted'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    inviter_user_id: Mapped[uuid.UUID | None] = mapped_column(
        "inviter_user_id",
        GUID,
        sa.ForeignKey("users.uuid", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
    )
    invitee_user_id: Mapped[uuid.UUID] = mapped_column(
        "invitee_user_id",
        GUID,
        sa.ForeignKey("users.uuid", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        # The ON DELETE CASCADE above has to find every row for a user, including
        # accepted ones, so uq_role_invitations_active cannot serve it -- that
        # index is partial (state != 'accepted').
        index=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        "role_id",
        GUID,
        sa.ForeignKey("roles.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    state: Mapped[RoleInvitationState] = mapped_column(
        "state",
        StrEnumType(RoleInvitationState),
        nullable=False,
        default=RoleInvitationState.PENDING,
        server_default=RoleInvitationState.PENDING.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=True,
        onupdate=sa.func.current_timestamp(),
    )

    def to_data(self) -> RoleInvitationData:
        return RoleInvitationData(
            id=self.id,
            inviter_user_id=self.inviter_user_id,
            invitee_user_id=self.invitee_user_id,
            role_id=self.role_id,
            state=self.state,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
