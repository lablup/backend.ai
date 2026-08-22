from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_group import RESOURCE_GROUP_SCOPE_TYPE, ResourceGroupID
from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.exception import ResourceGroupConflict
from ai.backend.common.types import AccessKey
from ai.backend.manager.data.resource_group.types import FairShareResourceGroupSpec
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.resource_group import (
    ResourceGroupForDomainRow,
    ResourceGroupForKeypairsRow,
    ResourceGroupForProjectRow,
    ResourceGroupOpts,
    ResourceGroupRow,
)
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.ops.rbac.provider import ScopeCreation
from ai.backend.manager.repositories.permission_controller.role_manager import (
    ScopeSystemRoleData,
)


@dataclass
class ResourceGroupCreatorSpec(CreatorSpec[ResourceGroupRow]):
    """CreatorSpec for resource group."""

    name: str
    driver: str
    scheduler: str
    description: str | None = None
    is_active: bool = True
    is_public: bool = True
    is_default: bool = False
    wsproxy_addr: str | None = None
    wsproxy_api_token: str | None = None
    driver_opts: Mapping[str, Any] = field(default_factory=dict)
    scheduler_opts: ResourceGroupOpts | None = None
    use_host_network: bool = False
    fair_share_spec: FairShareResourceGroupSpec | None = None

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=ResourceGroupConflict(f"Duplicate resource group name: {self.name}"),
            ),
        )

    @override
    def build_row(self) -> ResourceGroupRow:
        return ResourceGroupRow(
            name=self.name,
            description=self.description,
            is_active=self.is_active,
            is_public=self.is_public,
            is_default=self.is_default,
            wsproxy_addr=self.wsproxy_addr,
            wsproxy_api_token=self.wsproxy_api_token,
            driver=self.driver,
            driver_opts=dict(self.driver_opts),
            scheduler=self.scheduler,
            scheduler_opts=self.scheduler_opts if self.scheduler_opts else ResourceGroupOpts(),
            use_host_network=self.use_host_network,
            fair_share_spec=self.fair_share_spec,
        )


@dataclass
class ResourceGroupScopeCreation(ScopeCreation[ResourceGroupRow]):
    """Creates a resource group row and the resource-group scope it becomes.

    A resource group declares no scope-local system roles: roles come only from
    matching role presets, if any. Domain/project scope associations are written by
    the allow/associate paths, not by this creator."""

    spec: ResourceGroupCreatorSpec

    @override
    def creator(self) -> RBACEntityCreator[ResourceGroupRow]:
        return RBACEntityCreator(
            spec=self.spec,
            element_type=RBACElementType.RESOURCE_GROUP,
            scope_ref=None,
        )

    @override
    def scope_of(self, row: ResourceGroupRow) -> ScopeRef:
        return ScopeRef(scope_type=RESOURCE_GROUP_SCOPE_TYPE, scope_id=row.id)

    @override
    def system_roles_of(self, row: ResourceGroupRow) -> Collection[ScopeSystemRoleData]:
        return ()


@dataclass
class ResourceGroupForDomainCreatorSpec(CreatorSpec[ResourceGroupForDomainRow]):
    """CreatorSpec for associating a resource group with a domain."""

    resource_group_id: ResourceGroupID
    domain_id: DomainID

    @override
    def build_row(self) -> ResourceGroupForDomainRow:
        return ResourceGroupForDomainRow(
            resource_group_id=self.resource_group_id,
            domain_id=self.domain_id,
        )


@dataclass
class ResourceGroupForKeypairsCreatorSpec(CreatorSpec[ResourceGroupForKeypairsRow]):
    """CreatorSpec for associating a resource group with a keypair."""

    resource_group_id: ResourceGroupID
    access_key: AccessKey

    @override
    def build_row(self) -> ResourceGroupForKeypairsRow:
        return ResourceGroupForKeypairsRow(
            resource_group_id=self.resource_group_id,
            access_key=self.access_key,
        )


@dataclass
class ResourceGroupForProjectCreatorSpec(CreatorSpec[ResourceGroupForProjectRow]):
    """CreatorSpec for associating a resource group with a project (user group)."""

    resource_group_id: ResourceGroupID
    project: UUID

    @override
    def build_row(self) -> ResourceGroupForProjectRow:
        return ResourceGroupForProjectRow(
            resource_group_id=self.resource_group_id,
            group=self.project,
        )
