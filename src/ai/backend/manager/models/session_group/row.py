from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.session_group import SessionGroupID
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.data.session_group.types import (
    SessionGroupPlacementDirection,
    SessionGroupPlacementEnforcement,
)
from ai.backend.manager.models.base import GUID, Base, StrEnumType
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin

__all__ = ("SessionGroupRow",)


class SessionGroupRow(CreatedAtMixin, Base):  # type: ignore[misc]
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
    owner_user_id: Mapped[UserID] = mapped_column(
        "owner_user_id",
        GUID(UserID),
        sa.ForeignKey("users.uuid"),
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
