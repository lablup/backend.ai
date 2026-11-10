"""Upsert specs for the scaling_groups table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_group.searchable_fields import (
    ResourceGroupSearchableFields,
)
from ai.backend.manager.models.resource_group.types import ResourceGroupOpts
from ai.backend.manager.models.specs.created_in import CreatedInGlobal
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter

__all__ = ("ResourceGroupUpserter",)


@dataclass
class ResourceGroupUpserter(
    CreatedInGlobal[ResourceGroupRow], EntityUpserter[ResourceGroupRow, ResourceGroupData]
):
    """Write a resource group under its stated id.

    Conflict key: id. ``name`` is written on insert only: agents and endpoints refer to
    the group by it. ``fair_share_spec`` and the two default options are left as they are.
    """

    id: ResourceGroupID
    name: str
    description: str | None
    is_active: bool
    is_public: bool
    is_default: bool
    wsproxy_addr: str | None
    wsproxy_api_token: str | None
    driver: str
    driver_opts: dict[str, Any]
    scheduler: str
    scheduler_opts: ResourceGroupOpts
    use_host_network: bool

    @override
    def entity_id(self, row: ResourceGroupRow) -> ResourceGroupID:
        return ResourceGroupID(row.id)

    @override
    def row_class(self) -> type[ResourceGroupRow]:
        return ResourceGroupRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, **self._values()}

    @override
    def build_update_values(self) -> dict[str, Any]:
        return self._values()

    def _values(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "is_active": self.is_active,
            "is_public": self.is_public,
            "is_default": self.is_default,
            "wsproxy_addr": self.wsproxy_addr,
            "wsproxy_api_token": self.wsproxy_api_token,
            "driver": self.driver,
            "driver_opts": self.driver_opts,
            "scheduler": self.scheduler,
            "scheduler_opts": self.scheduler_opts,
            "use_host_network": self.use_host_network,
        }

    @override
    def to_data(self, row: ResourceGroupRow) -> ResourceGroupData:
        return ResourceGroupSearchableFields.own.to_data(row)
