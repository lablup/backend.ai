"""Scope-wide entity unbinders for scaling group associations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.data.permission.types import RBACElementRef, RBACElementType
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForDomainRow,
    ScalingGroupForProjectRow,
)
from ai.backend.manager.repositories.base.purger import BatchPurgerSpec
from ai.backend.manager.repositories.base.rbac.scope_unbinder import (
    RBACScopeWideEntityUnbinder,
)
from ai.backend.manager.repositories.scaling_group.purgers import (
    AllScalingGroupsForDomainPurgerSpec,
    AllScalingGroupsForProjectPurgerSpec,
    ScalingGroupForDomainPurgerSpec,
    ScalingGroupForProjectPurgerSpec,
    ScalingGroupsForDomainPurgerSpec,
    ScalingGroupsForProjectPurgerSpec,
)

# =============================================================================
# Domain Unbinders
# =============================================================================


@dataclass
class SGDomainEntityUnbinder(RBACScopeWideEntityUnbinder[ScalingGroupForDomainRow]):
    """Unbind specific scaling groups from a domain."""

    scaling_groups: Sequence[str]
    domain: str

    @override
    def build_purger_spec(self) -> BatchPurgerSpec[ScalingGroupForDomainRow]:
        if len(self.scaling_groups) == 1:
            return ScalingGroupForDomainPurgerSpec(
                scaling_group=self.scaling_groups[0],
                domain=self.domain,
            )
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
    def entity_ids(self) -> Sequence[str]:
        return list(self.scaling_groups)


@dataclass
class AllSGsFromDomainUnbinder(RBACScopeWideEntityUnbinder[ScalingGroupForDomainRow]):
    """Unbind ALL scaling groups from a domain."""

    domain: str

    @override
    def build_purger_spec(self) -> BatchPurgerSpec[ScalingGroupForDomainRow]:
        return AllScalingGroupsForDomainPurgerSpec(domain=self.domain)

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
    def entity_ids(self) -> None:
        return None


# =============================================================================
# Project Unbinders
# =============================================================================


@dataclass
class SGProjectEntityUnbinder(RBACScopeWideEntityUnbinder[ScalingGroupForProjectRow]):
    """Unbind specific scaling groups from a project (user group)."""

    scaling_groups: Sequence[str]
    project: UUID

    @override
    def build_purger_spec(self) -> BatchPurgerSpec[ScalingGroupForProjectRow]:
        if len(self.scaling_groups) == 1:
            return ScalingGroupForProjectPurgerSpec(
                scaling_group=self.scaling_groups[0],
                project=self.project,
            )
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
    def entity_ids(self) -> Sequence[str]:
        return list(self.scaling_groups)


@dataclass
class AllSGsFromProjectUnbinder(RBACScopeWideEntityUnbinder[ScalingGroupForProjectRow]):
    """Unbind ALL scaling groups from a project (user group)."""

    project: UUID

    @override
    def build_purger_spec(self) -> BatchPurgerSpec[ScalingGroupForProjectRow]:
        return AllScalingGroupsForProjectPurgerSpec(project=self.project)

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
    def entity_ids(self) -> None:
        return None
