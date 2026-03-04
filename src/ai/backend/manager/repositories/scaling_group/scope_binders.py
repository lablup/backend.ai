from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import RBACElementType
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

    When scaling_groups is None, all scaling groups in the domain are unbound.
    """

    scaling_groups: Sequence[str] | None
    domain: str

    @override
    def build_purger_spec(self) -> BatchPurgerSpec[ScalingGroupForDomainRow]:
        if self.scaling_groups is None:
            return AllScalingGroupsForDomainPurgerSpec(domain=self.domain)
        return ScalingGroupsForDomainPurgerSpec(
            scaling_groups=list(self.scaling_groups),
            domain=self.domain,
        )

    @property
    @override
    def entity_type(self) -> RBACElementType:
        return RBACElementType.RESOURCE_GROUP

    @property
    @override
    def scope_ref(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.DOMAIN, self.domain)

    @property
    @override
    def entity_ids(self) -> Sequence[str] | None:
        return list(self.scaling_groups) if self.scaling_groups is not None else None


@dataclass
class ResourceGroupProjectEntityUnbinder(RBACScopeEntityUnbinder[ScalingGroupForProjectRow]):
    """Unbind scaling groups from a project.

    When scaling_groups is None, all scaling groups in the project are unbound.
    """

    scaling_groups: Sequence[str] | None
    project: UUID

    @override
    def build_purger_spec(self) -> BatchPurgerSpec[ScalingGroupForProjectRow]:
        if self.scaling_groups is None:
            return AllScalingGroupsForProjectPurgerSpec(project=self.project)
        return ScalingGroupsForProjectPurgerSpec(
            scaling_groups=list(self.scaling_groups),
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
        return list(self.scaling_groups) if self.scaling_groups is not None else None
