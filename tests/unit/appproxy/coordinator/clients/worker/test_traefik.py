from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, Mock

import pytest

from ai.backend.appproxy.common.defs import (
    WORKER_AUTHORITY_LABEL,
    WORKER_HOSTNAME_LABEL,
    WORKER_SERVICE_GROUP,
    WORKER_TLS_LISTEN_LABEL,
)
from ai.backend.appproxy.common.etcd import TraefikEtcd
from ai.backend.appproxy.coordinator.clients.worker.traefik import (
    TraefikWorkerClient,
    TraefikWorkerClientArgs,
)
from ai.backend.appproxy.coordinator.clients.worker.traefik_routing_config import (
    TraefikRoutingConfigFactory,
)
from ai.backend.appproxy.coordinator.config import TraefikConfig
from ai.backend.appproxy.coordinator.errors.ingress import TraefikIngressRevisionConflictError
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    Ingress,
    IngressAccess,
    IngressAccessMode,
    IngressAuthority,
    IngressBackend,
    IngressBackendID,
    IngressFrontend,
    IngressFrontendKind,
    IngressID,
    IngressProtocol,
    IngressTargetGroup,
    IngressTargetGroupID,
    PortFrontend,
)
from ai.backend.common.service_discovery.service_discovery import (
    ServiceDiscovery,
    ServiceEndpoint,
    ServiceMetadata,
)


@dataclass(frozen=True)
class _HeldRevisionCase:
    name: str
    held_revision: str | None


def _port_ingress(port: int, revision: int) -> Ingress:
    return Ingress(
        id=IngressID(f"ingress-{port}"),
        authority=IngressAuthority("worker-1"),
        revision=revision,
        frontend=IngressFrontend(
            kind=IngressFrontendKind.PORT,
            protocol=IngressProtocol.HTTP,
            port=PortFrontend(number=port),
        ),
        access=IngressAccess(mode=IngressAccessMode.PUBLIC, allowed_client_ips=[]),
        backend=IngressBackend(
            id=IngressBackendID(f"backend-{port}"),
            target_groups=[
                IngressTargetGroup(id=IngressTargetGroupID("group-1"), weight=1, targets=[])
            ],
        ),
    )


@pytest.fixture
def ingress() -> Ingress:
    return _port_ingress(10205, revision=3)


@pytest.fixture
def ingress_on_another_port() -> Ingress:
    return _port_ingress(10206, revision=5)


@pytest.fixture
def traefik_etcd(request: pytest.FixtureRequest) -> AsyncMock:
    case: _HeldRevisionCase = request.param
    traefik_etcd = AsyncMock(spec=TraefikEtcd)
    traefik_etcd.get.return_value = case.held_revision
    traefik_etcd.compare_and_replace_prefixes.return_value = True
    return traefik_etcd


@pytest.fixture
def etcd_holding_a_newer_revision_of_10206() -> AsyncMock:
    traefik_etcd = AsyncMock(spec=TraefikEtcd)
    traefik_etcd.get.side_effect = lambda key: "6" if "/10206/" in key else None
    traefik_etcd.compare_and_replace_prefixes.return_value = True
    return traefik_etcd


@pytest.fixture
def worker_service_discovery() -> AsyncMock:
    worker_service_discovery = AsyncMock(spec=ServiceDiscovery)
    worker_service_discovery.get_service_group.return_value = [
        ServiceMetadata.for_endpoint(
            display_name="appproxy-worker-worker-1",
            service_group=WORKER_SERVICE_GROUP,
            version="test",
            endpoint=ServiceEndpoint(
                address="127.0.0.1",
                port=10201,
                protocol="http",
                prometheus_address="127.0.0.1:10201",
            ),
            labels={
                WORKER_AUTHORITY_LABEL: "worker-1",
                WORKER_HOSTNAME_LABEL: "worker-1.example.com",
                WORKER_TLS_LISTEN_LABEL: "false",
            },
        )
    ]
    return worker_service_discovery


@pytest.fixture
def routing_config_factory() -> TraefikRoutingConfigFactory:
    return TraefikRoutingConfigFactory(
        Mock(spec=TraefikConfig, client_ip_strategy=None),
        jwt_secret="jwt-secret",
        permit_hash_secret="permit-hash-secret",
    )


@pytest.fixture
def client(
    traefik_etcd: AsyncMock,
    worker_service_discovery: AsyncMock,
    routing_config_factory: TraefikRoutingConfigFactory,
) -> TraefikWorkerClient:
    return TraefikWorkerClient(
        TraefikWorkerClientArgs(
            etcd=traefik_etcd,
            worker_service_discovery=worker_service_discovery,
            routing_config_factory=routing_config_factory,
        )
    )


@pytest.fixture
def client_on_etcd_holding_10206(
    etcd_holding_a_newer_revision_of_10206: AsyncMock,
    worker_service_discovery: AsyncMock,
    routing_config_factory: TraefikRoutingConfigFactory,
) -> TraefikWorkerClient:
    return TraefikWorkerClient(
        TraefikWorkerClientArgs(
            etcd=etcd_holding_a_newer_revision_of_10206,
            worker_service_discovery=worker_service_discovery,
            routing_config_factory=routing_config_factory,
        )
    )


class TestTraefikWorkerClient:
    @pytest.mark.parametrize(
        "traefik_etcd",
        [
            _HeldRevisionCase(name="absent", held_revision=None),
            _HeldRevisionCase(name="older", held_revision="2"),
            _HeldRevisionCase(name="same", held_revision="3"),
        ],
        ids=lambda case: case.name,
        indirect=True,
    )
    async def test_upsert_writes_unless_etcd_holds_a_newer_revision(
        self, client: TraefikWorkerClient, traefik_etcd: AsyncMock, ingress: Ingress
    ) -> None:
        await client.upsert([ingress])
        traefik_etcd.compare_and_replace_prefixes.assert_awaited_once()

    @pytest.mark.parametrize(
        "traefik_etcd",
        [_HeldRevisionCase(name="newer", held_revision="4")],
        ids=lambda case: case.name,
        indirect=True,
    )
    async def test_upsert_older_than_held_raises_conflict(
        self, client: TraefikWorkerClient, traefik_etcd: AsyncMock, ingress: Ingress
    ) -> None:
        with pytest.raises(TraefikIngressRevisionConflictError):
            await client.upsert([ingress])
        traefik_etcd.compare_and_replace_prefixes.assert_not_awaited()

    async def test_upsert_writes_none_of_a_batch_holding_an_older_ingress(
        self,
        client_on_etcd_holding_10206: TraefikWorkerClient,
        etcd_holding_a_newer_revision_of_10206: AsyncMock,
        ingress: Ingress,
        ingress_on_another_port: Ingress,
    ) -> None:
        with pytest.raises(TraefikIngressRevisionConflictError):
            await client_on_etcd_holding_10206.upsert([ingress, ingress_on_another_port])
        etcd_holding_a_newer_revision_of_10206.compare_and_replace_prefixes.assert_not_awaited()
