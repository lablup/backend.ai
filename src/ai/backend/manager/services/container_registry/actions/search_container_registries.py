"""Action for searching container registries."""

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.container_registry.actions.base import (
    ContainerRegistryScopeAction,
    ContainerRegistryScopeActionResult,
)


@dataclass
class SearchContainerRegistriesAction(ContainerRegistryScopeAction):
    querier: BatchQuerier
    _domain_name: str = ""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.DOMAIN

    @override
    def scope_id(self) -> str:
        return self._domain_name

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.DOMAIN, self._domain_name)


@dataclass
class SearchContainerRegistriesActionResult(ContainerRegistryScopeActionResult):
    data: list[ContainerRegistryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    _domain_name: str = ""

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.DOMAIN

    @override
    def scope_id(self) -> str:
        return self._domain_name
