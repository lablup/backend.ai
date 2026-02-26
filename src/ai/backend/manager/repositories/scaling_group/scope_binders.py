from __future__ import annotations

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
    RBACEntityUnbinder,
    RBACScopeUnbinder,
)
from ai.backend.manager.repositories.scaling_group.purgers import (
    AllScalingGroupsForDomainPurgerSpec,
    AllScalingGroupsForProjectPurgerSpec,
    ScalingGroupForDomainPurgerSpec,
    ScalingGroupForProjectPurgerSpec,
)

# =============================================================================
# Entity Unbinders (single SG + single scope)
# =============================================================================


@dataclass
class SGDomainEntityUnbinder(RBACEntityUnbinder[ScalingGroupForDomainRow]):
    """Unbind a single scaling group from a single domain."""

    scaling_group: str
    domain: str

    @override
    def build_purger_spec(self) -> BatchPurgerSpec[ScalingGroupForDomainRow]:
        return ScalingGroupForDomainPurgerSpec(
            scaling_group=self.scaling_group,
            domain=self.domain,
        )

    @property
    @override
    def entity_ref(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.RESOURCE_GROUP, self.scaling_group)

    @property
    @override
    def scope_ref(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.DOMAIN, self.domain)


@dataclass
class SGProjectEntityUnbinder(RBACEntityUnbinder[ScalingGroupForProjectRow]):
    """Unbind a single scaling group from a single project."""

    scaling_group: str
    project: UUID

    @override
    def build_purger_spec(self) -> BatchPurgerSpec[ScalingGroupForProjectRow]:
        return ScalingGroupForProjectPurgerSpec(
            scaling_group=self.scaling_group,
            project=self.project,
        )

    @property
    @override
    def entity_ref(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.RESOURCE_GROUP, self.scaling_group)

    @property
    @override
    def scope_ref(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.PROJECT, str(self.project))


# =============================================================================
# Scope Unbinders ("All" cases: entity_ref=None)
# =============================================================================


@dataclass
class AllSGsFromDomainScopeUnbinder(RBACScopeUnbinder[ScalingGroupForDomainRow]):
    """Unbind all scaling groups from a domain."""

    domain: str

    @override
    def build_purger_spec(self) -> BatchPurgerSpec[ScalingGroupForDomainRow]:
        return AllScalingGroupsForDomainPurgerSpec(domain=self.domain)

    @property
    @override
    def scope_ref(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.DOMAIN, self.domain)

    @property
    @override
    def entity_ref(self) -> RBACElementRef | None:
        return None


@dataclass
class AllSGsFromProjectScopeUnbinder(RBACScopeUnbinder[ScalingGroupForProjectRow]):
    """Unbind all scaling groups from a project."""

    project: UUID

    @override
    def build_purger_spec(self) -> BatchPurgerSpec[ScalingGroupForProjectRow]:
        return AllScalingGroupsForProjectPurgerSpec(project=self.project)

    @property
    @override
    def scope_ref(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.PROJECT, str(self.project))

    @property
    @override
    def entity_ref(self) -> RBACElementRef | None:
        return None
