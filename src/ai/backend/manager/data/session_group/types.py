from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import override

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.data.entity.types import EntityData
from ai.backend.common.data.entity.user import UserID
from ai.backend.sokovan_core.types.policy import (
    SessionGroupPlacementDirection,
    SessionGroupPlacementEnforcement,
)

__all__ = ("SessionGroupData",)


@dataclass(frozen=True)
class SessionGroupData(EntityData):
    id: SessionGroupID
    domain_id: DomainID
    project_id: ProjectID
    owner_user_id: UserID
    placement_direction: SessionGroupPlacementDirection
    placement_enforcement: SessionGroupPlacementEnforcement
    created_at: datetime
    deleted_at: datetime | None

    @override
    def entity_id(self) -> SessionGroupID:
        return self.id
