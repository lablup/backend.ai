from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.resource_group import (
    ResourceGroupForDomainRow,
    ResourceGroupForProjectRow,
)
from ai.backend.manager.repositories.base.purger import BatchPurgerSpec
from ai.backend.manager.repositories.base.rbac.scope_unbinder import (
    RBACScopeEntityUnbinder,
)
from ai.backend.manager.repositories.resource_group.purgers import (
    AllResourceGroupsForDomainPurgerSpec,
    AllResourceGroupsForProjectPurgerSpec,
    ResourceGroupsForDomainPurgerSpec,
    ResourceGroupsForProjectPurgerSpec,
)

# =============================================================================
# Entity Unbinders (batch SGs + single scope)
# =============================================================================


@dataclass
class ResourceGroupDomainEntityUnbinder(RBACScopeEntityUnbinder[ResourceGroupForDomainRow]):
    """Unbind resource groups from a domain.

    When resource_group_ids is None, all resource groups in the domain are unbound.
    """

    resource_group_ids: Sequence[ResourceGroupID] | None
    domain_id: DomainID

    @override
    def build_purger_spec(self) -> BatchPurgerSpec[ResourceGroupForDomainRow]:
        if self.resource_group_ids is None:
            return AllResourceGroupsForDomainPurgerSpec(domain_id=self.domain_id)
        return ResourceGroupsForDomainPurgerSpec(
            resource_group_ids=list(self.resource_group_ids),
            domain_id=self.domain_id,
        )

    @property
    @override
    def entity_type(self) -> RBACElementType:
        return RBACElementType.RESOURCE_GROUP

    @property
    @override
    def scope_ref(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.DOMAIN, str(self.domain_id))

    @property
    @override
    def entity_ids(self) -> Sequence[str] | None:
        if self.resource_group_ids is None:
            return None
        return [str(rg_id) for rg_id in self.resource_group_ids]


@dataclass
class ResourceGroupProjectEntityUnbinder(RBACScopeEntityUnbinder[ResourceGroupForProjectRow]):
    """Unbind resource groups from a project.

    When resource_group_ids is None, all resource groups in the project are unbound.
    """

    resource_group_ids: Sequence[ResourceGroupID] | None
    project: UUID

    @override
    def build_purger_spec(self) -> BatchPurgerSpec[ResourceGroupForProjectRow]:
        if self.resource_group_ids is None:
            return AllResourceGroupsForProjectPurgerSpec(project=self.project)
        return ResourceGroupsForProjectPurgerSpec(
            resource_group_ids=list(self.resource_group_ids),
            project=self.project,
        )

    @property
    @override
    def entity_type(self) -> RBACElementType:
        return RBACElementType.RESOURCE_GROUP

    @property
    @override
    def scope_ref(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.PROJECT, str(self.project))

    @property
    @override
    def entity_ids(self) -> Sequence[str] | None:
        if self.resource_group_ids is None:
            return None
        return [str(rg_id) for rg_id in self.resource_group_ids]
