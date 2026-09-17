"""Write specs for a registered service and the endpoints it announced.

The registration handler is the only writer of a catalog row, and its upserter stamps
the status healthy and the heartbeat now. A seed takes that same spec for a healthy
service. Deregistration and the stale sweep update the row in place through no spec,
so a service in either state is laid through the one spec this module defines itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Final, override

from ai.backend.common.data.entity.service_catalog import ServiceCatalogID
from ai.backend.common.types import ServiceCatalogStatus
from ai.backend.manager.data.service_catalog.types import ServiceCatalogEndpointData
from ai.backend.manager.models.service_catalog.creators import ServiceCatalogEndpointCreator
from ai.backend.manager.models.service_catalog.upserters import ServiceCatalogUpserter
from bai_scenario.seeds.seeder import Naming, SeedField, SeedRow

VERSION = "26.9.0"
"""The version every laid service reports."""

STARTED_UP = datetime(2026, 1, 1, tzinfo=UTC)
"""The startup time every laid service reports. Fixed, so the report reads the same each run."""

STATUS_NAMES: Final[dict[ServiceCatalogStatus, str]] = {
    ServiceCatalogStatus.HEALTHY: "정상",
    ServiceCatalogStatus.UNHEALTHY: "비정상",
    ServiceCatalogStatus.DEREGISTERED: "등록 해제",
}
"""레포트가 각 상태를 부르는 이름."""


@dataclass
class ServiceCatalogInStatusUpserter(ServiceCatalogUpserter):
    """The registration spec with the status it stamps replaced by the one given.

    Defined here, not in src: the manager reaches a non-healthy status only by updating
    the row in place, through no spec, so no src spec lays a service in one.
    """

    status: ServiceCatalogStatus

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {**super().build_update_values(), "status": self.status}


@dataclass(frozen=True)
class SeedService(SeedRow[ServiceCatalogID]):
    """One service instance, registered healthy in the group it is given.

    The instance id is the seeder's name, and the display name repeats it.
    """

    service_group: str
    name_hint: str = "instance"

    @override
    def kind(self) -> str:
        return "서비스"

    @override
    def detail(self) -> str:
        return f"{self.service_group} 그룹에 정상 상태로 등록됨"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> ServiceCatalogUpserter:
        return ServiceCatalogUpserter(
            service_group=self.service_group,
            instance_id=name,
            display_name=name,
            version=VERSION,
            labels={},
            startup_time=STARTED_UP,
            config_hash="",
        )


@dataclass(frozen=True)
class SeedServiceInStatus(SeedRow[ServiceCatalogID]):
    """One service instance, registered in the group and the status it is given.

    Takes the test-side spec, so it is for a status the registration spec cannot write.
    """

    service_group: str
    status: ServiceCatalogStatus
    name_hint: str = "instance"

    @override
    def kind(self) -> str:
        return "서비스"

    @override
    def detail(self) -> str:
        return f"{self.service_group} 그룹에 {STATUS_NAMES[self.status]} 상태로 등록됨"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> ServiceCatalogUpserter:
        return ServiceCatalogInStatusUpserter(
            service_group=self.service_group,
            instance_id=name,
            display_name=name,
            version=VERSION,
            labels={},
            startup_time=STARTED_UP,
            config_hash="",
            status=self.status,
        )


@dataclass(frozen=True)
class SeedEndpointOf(SeedField[ServiceCatalogID, ServiceCatalogEndpointData]):
    """One endpoint the service announced."""

    role: str = "api"
    scope: str = "public"
    address: str = "127.0.0.1"
    port: int = 8080
    protocol: str = "http"
    metadata: dict[str, Any] = field(default_factory=lambda: {"zone": "a"})

    @override
    def kind(self) -> str:
        return f"{self.protocol}://{self.address}:{self.port} 엔드포인트 하나를 갖는다"

    @override
    def owner_id(self, owner: ServiceCatalogID) -> ServiceCatalogID:
        return owner

    @override
    def seed(self) -> ServiceCatalogEndpointCreator:
        return ServiceCatalogEndpointCreator(
            role=self.role,
            scope=self.scope,
            address=self.address,
            port=self.port,
            protocol=self.protocol,
            metadata=self.metadata,
        )
