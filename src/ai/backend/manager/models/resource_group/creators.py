"""Creator specs for the scaling_groups table."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.data.entity.resource_group import RESOURCE_GROUP_SCOPE_TYPE, ResourceGroupID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.exception import ResourceGroupConflict
from ai.backend.manager.data.permission.scope_template import ScopeTemplateValue
from ai.backend.manager.data.resource_group.types import (
    FairShareResourceGroupSpec,
    ResourceGroupData,
)
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.resource_group.row import ResourceGroupOpts, ResourceGroupRow
from ai.backend.manager.models.specs.creator import RoleManagedGlobalEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class ResourceGroupCreator(RoleManagedGlobalEntityCreator[ResourceGroupRow, ResourceGroupData]):
    """Registers a resource group, the scope its agents and sessions are created under.

    Joins nothing: the domain and project associations are written by the allow and
    associate paths.
    """

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

    @override
    def entity_id(self, row: ResourceGroupRow) -> EntityIdentifier:
        return ResourceGroupID(row.id)

    @override
    def template_value(self, row: ResourceGroupRow) -> ScopeTemplateValue:
        return ScopeTemplateValue(id=row.id, name=row.name, type=RESOURCE_GROUP_SCOPE_TYPE)

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

    @override
    def to_data(self, row: ResourceGroupRow) -> ResourceGroupData:
        return row.to_dataclass()
