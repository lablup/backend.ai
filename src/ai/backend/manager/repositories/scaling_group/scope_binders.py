from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForDomainRow,
    ScalingGroupForProjectRow,
)
from ai.backend.manager.repositories.base.purger import BatchPurgerSpec
from ai.backend.manager.repositories.base.rbac.scope_unbinder import (
    RBACScopeEntityUnbinder,
)
from ai.backend.manager.repositories.scaling_group.purgers import (
    AllScalingGroupsForDomainPurgerSpec,
    AllScalingGroupsForProjectPurgerSpec,
    ScalingGroupsForDomainPurgerSpec,
    ScalingGroupsForProjectPurgerSpec,
)

# =============================================================================
# Entity Unbinders (batch SGs + single scope)
# =============================================================================


@dataclass
class ResourceGroupDomainEntityUnbinder(RBACScopeEntityUnbinder[ScalingGroupForDomainRow]):
    """Unbind scaling groups from a domain.

    When resource_group_ids is None, all scaling groups in the domain are unbound.
    """

    resource_group_ids: Sequence[ResourceGroupID] | None
    domain_id: DomainID

    @override
    def build_purger_spec(self) -> BatchPurgerSpec[ScalingGroupForDomainRow]:
        if self.resource_group_ids is None:
            return AllScalingGroupsForDomainPurgerSpec(domain_id=self.domain_id)
        return ScalingGroupsForDomainPurgerSpec(
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
class ResourceGroupProjectEntityUnbinder(RBACScopeEntityUnbinder[ScalingGroupForProjectRow]):
    """Unbind scaling groups from a project.

    When resource_group_ids is None, all scaling groups in the project are unbound.
    """

    resource_group_ids: Sequence[ResourceGroupID] | None
    project: UUID

    @override
    def build_purger_spec(self) -> BatchPurgerSpec[ScalingGroupForProjectRow]:
        if self.resource_group_ids is None:
            return AllScalingGroupsForProjectPurgerSpec(project=self.project)
        return ScalingGroupsForProjectPurgerSpec(
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
