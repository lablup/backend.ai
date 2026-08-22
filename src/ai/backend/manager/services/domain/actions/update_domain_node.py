from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.domain.types import DomainData, UserInfo
from ai.backend.manager.models.domain.updaters import DomainUpdater


@dataclass(frozen=True)
class UpdateDomainNodeAction(BaseSingleEntityAction):
    """Edit one domain and the resource groups it may schedule on."""

    updater: DomainUpdater
    user_info: UserInfo
    sgroup_ids_to_add: set[ResourceGroupID] | None = None
    sgroup_ids_to_remove: set[ResourceGroupID] | None = None

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.domain_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_domain_node"


@dataclass(frozen=True)
class UpdateDomainNodeActionResult:
    domain_data: DomainData
