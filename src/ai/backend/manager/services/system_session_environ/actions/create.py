from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.models.system_session_environ.creators import (
    SystemSessionEnvironCreator,
)

__all__ = (
    "CreateSystemSessionEnvironAction",
    "CreateSystemSessionEnvironActionResult",
)


@dataclass(frozen=True)
class CreateSystemSessionEnvironAction(BaseScopeAction):
    """Bind a value source to an environment variable name at the public scope, a domain
    or a project."""

    creator: SystemSessionEnvironCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SystemSessionEnvironEntityType()

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_system_session_environ"

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (self.creator.owner,)


@dataclass(frozen=True)
class CreateSystemSessionEnvironActionResult(BaseScopeActionResult):
    data: SystemSessionEnvironData

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return (self.data.id,)
