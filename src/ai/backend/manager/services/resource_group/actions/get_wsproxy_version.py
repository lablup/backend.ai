from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.models.resource_group.scopes import ResourceGroupTarget


@dataclass(frozen=True)
class GetWsproxyVersionAction(BaseScopeAction):
    """Read the proxy version of one resource group the named scopes reach."""

    resource_group_name: str
    targets: Sequence[ResourceGroupTarget]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ResourceGroupEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_wsproxy_version"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [target.scope_id() for target in self.targets]


@dataclass(frozen=True)
class GetWsproxyVersionActionResult(BaseScopeActionResult):
    """Result of getting wsproxy version."""

    wsproxy_version: str

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()
