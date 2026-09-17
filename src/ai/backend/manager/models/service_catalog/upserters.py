"""Upsert specs for the service catalog."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.service_catalog import ServiceCatalogID
from ai.backend.common.types import ServiceCatalogStatus
from ai.backend.manager.models.service_catalog.row import ServiceCatalogRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import GlobalEntityUpserter


@dataclass
class ServiceCatalogUpserter(GlobalEntityUpserter[ServiceCatalogRow, ServiceCatalogID]):
    """Registers one service instance as healthy.

    Conflict key: (service_group, instance_id). On conflict the reported state is
    replaced and the heartbeat is stamped.
    """

    service_group: str
    instance_id: str
    display_name: str
    version: str
    labels: Mapping[str, Any]
    startup_time: datetime
    config_hash: str

    @override
    def entity_id(self, row: ServiceCatalogRow) -> ServiceCatalogID:
        return ServiceCatalogID(row.id)

    @override
    def row_class(self) -> type[ServiceCatalogRow]:
        return ServiceCatalogRow

    @override
    def index_elements(self) -> list[str]:
        return ["service_group", "instance_id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "service_group": self.service_group,
            "instance_id": self.instance_id,
            **self.build_update_values(),
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {
            "display_name": self.display_name,
            "version": self.version,
            "labels": dict(self.labels),
            "status": ServiceCatalogStatus.HEALTHY,
            "startup_time": self.startup_time,
            "last_heartbeat": sa.func.now(),
            "config_hash": self.config_hash,
        }

    @override
    def to_data(self, row: ServiceCatalogRow) -> ServiceCatalogID:
        return ServiceCatalogID(row.id)
