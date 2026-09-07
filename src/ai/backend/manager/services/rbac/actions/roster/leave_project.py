from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.data.project.types import UnassignUserFailure
from ai.backend.manager.data.user.types import UserData

from .base import ProjectRosterAction


@dataclass(frozen=True)
class LeaveProjectAction(ProjectRosterAction):
    """Take users off a project's roster. Role mappings are left untouched."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "leave_project"


@dataclass(frozen=True)
class LeaveProjectActionResult(BaseScopeActionResult):
    """The users the run took off the roster, and the named ones it could not."""

    members: list[UserData] = field(default_factory=list)
    failures: list[UnassignUserFailure] = field(default_factory=list)

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return [UserID(member.id) for member in self.members]
