from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DOMAIN_SCOPE_TYPE, DomainID
from ai.backend.common.data.entity.session import SESSION_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeRef
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.data.resource_slot.types import ResourceOccupancy


@dataclass(frozen=True)
class GetDomainResourceOverviewAction(BaseScopeAction):
    """Read what the sessions inside a domain occupy.

    The sum is over what runs in the domain, not a value the domain row carries, so
    the domain is the scope rather than the entity.
    """

    domain_id: DomainID
    domain_name: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SESSION_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=DOMAIN_SCOPE_TYPE, scope_id=self.domain_id),)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_domain_resource_overview"


@dataclass(frozen=True)
class GetDomainResourceOverviewResult(BaseScopeActionResult):
    item: ResourceOccupancy

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()
