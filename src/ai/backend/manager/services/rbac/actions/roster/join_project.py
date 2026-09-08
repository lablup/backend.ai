from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.data.user.types import UserData

from .base import ProjectRosterAction


@dataclass(frozen=True)
class JoinProjectAction(ProjectRosterAction):
    """Put users on a project's roster, granting ``role_id`` where one is named and the
    project's auto_assign roles where none is."""

    role_id: RoleID | None = None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "join_project"


@dataclass(frozen=True)
class JoinProjectActionResult(BaseScopeActionResult):
    """The users the run put on the roster; those already on it are not among them."""

    members: list[UserData] = field(default_factory=list)

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return [UserID(member.id) for member in self.members]
