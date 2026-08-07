from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.resource_group import RESOURCE_GROUP_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityRef
from ai.backend.common.exception import ScalingGroupConflict
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import AccessKey
from ai.backend.manager.data.permission.role import ScopeSystemRoleData
from ai.backend.manager.data.scaling_group.types import FairShareScalingGroupSpec
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForDomainRow,
    ScalingGroupForKeypairsRow,
    ScalingGroupForProjectRow,
    ScalingGroupOpts,
    ScalingGroupRow,
)
from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.repositories.base.rbac.entity.creator import EntityCreator
from ai.backend.manager.repositories.base.rbac.entity.types import ScopeMembership
from ai.backend.manager.repositories.base.types import IntegrityErrorCheck


@dataclass
class ScalingGroupCreatorSpec(CreatorSpec[ScalingGroupRow]):
    """CreatorSpec for scaling group."""

    name: str
    driver: str
    scheduler: str
    description: str | None = None
    is_active: bool = True
    is_public: bool = True
    wsproxy_addr: str | None = None
    wsproxy_api_token: str | None = None
    driver_opts: Mapping[str, Any] = field(default_factory=dict)
    scheduler_opts: ScalingGroupOpts | None = None
    use_host_network: bool = False
    fair_share_spec: FairShareScalingGroupSpec | None = None

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=ScalingGroupConflict(f"Duplicate scaling group name: {self.name}"),
            ),
        )

    @override
    def build_row(self) -> ScalingGroupRow:
        return ScalingGroupRow(
            name=self.name,
            description=self.description,
            is_active=self.is_active,
            is_public=self.is_public,
            wsproxy_addr=self.wsproxy_addr,
            wsproxy_api_token=self.wsproxy_api_token,
            driver=self.driver,
            driver_opts=dict(self.driver_opts),
            scheduler=self.scheduler,
            scheduler_opts=self.scheduler_opts if self.scheduler_opts else ScalingGroupOpts(),
            use_host_network=self.use_host_network,
            fair_share_spec=self.fair_share_spec,
        )


@dataclass
class ResourceGroupScopeCreation(EntityCreator[ScalingGroupRow]):
    """Creates a scaling group row and the resource-group scope it becomes.

    A resource group declares no scope-local system roles: roles come only from
    matching role presets, if any. Domain/project scope memberships are written by
    the allow/associate paths, not by this creator."""

    creator_spec: ScalingGroupCreatorSpec

    @override
    def spec(self) -> CreatorSpec[ScalingGroupRow]:
        return self.creator_spec

    @override
    def entity_ref_of(self, row: ScalingGroupRow) -> EntityRef:
        return EntityRef(entity_type=RESOURCE_GROUP_ENTITY_TYPE, entity_id=row.id)

    @override
    def membership(self, row: ScalingGroupRow) -> Sequence[ScopeMembership]:
        return ()

    @override
    def system_roles_of(self, row: ScalingGroupRow) -> Collection[ScopeSystemRoleData]:
        return ()


@dataclass
class ScalingGroupForDomainCreatorSpec(CreatorSpec[ScalingGroupForDomainRow]):
    """CreatorSpec for associating a scaling group with a domain."""

    resource_group_id: ResourceGroupID
    domain_id: DomainID

    @override
    def build_row(self) -> ScalingGroupForDomainRow:
        return ScalingGroupForDomainRow(
            resource_group_id=self.resource_group_id,
            domain_id=self.domain_id,
        )


@dataclass
class ScalingGroupForKeypairsCreatorSpec(CreatorSpec[ScalingGroupForKeypairsRow]):
    """CreatorSpec for associating a scaling group with a keypair."""

    resource_group_id: ResourceGroupID
    access_key: AccessKey

    @override
    def build_row(self) -> ScalingGroupForKeypairsRow:
        return ScalingGroupForKeypairsRow(
            resource_group_id=self.resource_group_id,
            access_key=self.access_key,
        )


@dataclass
class ScalingGroupForProjectCreatorSpec(CreatorSpec[ScalingGroupForProjectRow]):
    """CreatorSpec for associating a scaling group with a project (user group)."""

    resource_group_id: ResourceGroupID
    project: UUID

    @override
    def build_row(self) -> ScalingGroupForProjectRow:
        return ScalingGroupForProjectRow(
            resource_group_id=self.resource_group_id,
            group=self.project,
        )
