from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.relation.base import BaseRelationAction
from ai.backend.manager.services.rbac.actions.relation.base import RelationLinkResult


@dataclass(frozen=True)
class CreateDomainContainerRegistryRelationsAction(BaseRelationAction):
    """Link the domain to each container registry. A registry already linked is left as
    it stands."""

    domain_id: DomainID
    registry_ids: Sequence[ContainerRegistryID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_domain_container_registry_relations"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [self.domain_id, *self.registry_ids]


@dataclass(frozen=True)
class CreateDomainContainerRegistryRelationsActionResult:
    """What the run did to each registry named, in the order named. A registry already
    linked answers ``linked=False``."""

    results: Sequence[RelationLinkResult[DomainID, ContainerRegistryID]]
