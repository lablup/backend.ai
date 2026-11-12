from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.relation.base import BaseRelationAction


@dataclass(frozen=True)
class UpdateDomainContainerRegistryRelationsAction(BaseRelationAction):
    """Set the registries the domain is related to to ``registry_ids``, in one transaction.
    The permission is asked of the domain and the registries named."""

    domain_id: DomainID
    registry_ids: Sequence[ContainerRegistryID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_domain_container_registry_relations"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [self.domain_id, *self.registry_ids]


@dataclass(frozen=True)
class UpdateDomainContainerRegistryRelationsActionResult:
    """The registries the run related and the ones it unrelated."""

    linked: Sequence[ContainerRegistryID]
    unlinked: Sequence[ContainerRegistryID]
