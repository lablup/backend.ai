from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.system_session_environ.types import SystemSessionEnvironValueSource
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction

__all__ = (
    "PublicListSystemSessionEnvironValueSourcesAction",
    "PublicListSystemSessionEnvironValueSourcesActionResult",
)


@dataclass(frozen=True)
class PublicListSystemSessionEnvironValueSourcesAction(BaseGlobalAction):
    """List every value source a system session environ row can carry."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SystemSessionEnvironEntityType()

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "public_list_system_session_environ_value_sources"


@dataclass(frozen=True)
class PublicListSystemSessionEnvironValueSourcesActionResult:
    value_sources: list[SystemSessionEnvironValueSource]
