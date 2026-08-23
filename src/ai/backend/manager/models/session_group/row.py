from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.session_group.types import (
    SessionGroupData,
    SessionGroupPlacementDirection,
    SessionGroupPlacementEnforcement,
)
from ai.backend.manager.models.base import GUID, Base, StrEnumType
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin

__all__ = ("SessionGroupRow",)


class SessionGroupRow(CreatedAtMixin, Base):
    """
    A set of sessions sharing a common concern, holding their placement policy.

    Members are bound through ``sessions.session_group_id`` (nullable — NULL means
    no placement constraint). Direction and enforcement are separate columns
    because they are orthogonal (BEP-1064).
    """

    __tablename__ = "session_groups"

    id: Mapped[SessionGroupID] = mapped_column(
        "id",
        GUID(SessionGroupID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v4()"),
    )
    domain_id: Mapped[DomainID] = mapped_column(
        "domain_id",
        GUID(DomainID),
        sa.ForeignKey("domains.id"),
        nullable=False,
    )
    project_id: Mapped[ProjectID] = mapped_column(
        "project_id",
        GUID(ProjectID),
        sa.ForeignKey("groups.id"),
        nullable=False,
    )
    # Admission is decided by the owner alone: every member session belongs to
    # this user. ``domain_id`` / ``project_id`` scope visibility and cleanup.
    # RESTRICT rather than CASCADE: a user's groups are transferred (endpoint
    # delegation) or removed by the purge itself, like every other record they
    # own. Leaving the removal to the database would drop a group while its
    # delegated member sessions keep running.
    owner_user_id: Mapped[UserID] = mapped_column(
        "owner_user_id",
        GUID(UserID),
        sa.ForeignKey("users.uuid", ondelete="RESTRICT"),
        nullable=False,
    )
    placement_direction: Mapped[SessionGroupPlacementDirection] = mapped_column(
        "placement_direction",
        StrEnumType(SessionGroupPlacementDirection),
        nullable=False,
    )
    placement_enforcement: Mapped[SessionGroupPlacementEnforcement] = mapped_column(
        "placement_enforcement",
        StrEnumType(SessionGroupPlacementEnforcement),
        nullable=False,
    )
    # The retention boundary; the sweep collects groups deleted long enough ago.
    deleted_at: Mapped[datetime | None] = mapped_column(
        "deleted_at",
        sa.DateTime(timezone=True),
        nullable=True,
    )

    def to_data(self) -> SessionGroupData:
        return SessionGroupData(
            id=SessionGroupID(self.id),
            domain_id=self.domain_id,
            project_id=self.project_id,
            owner_user_id=self.owner_user_id,
            placement_direction=self.placement_direction,
            placement_enforcement=self.placement_enforcement,
            created_at=self.created_at,
            deleted_at=self.deleted_at,
        )
