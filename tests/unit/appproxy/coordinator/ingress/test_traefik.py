from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, Mock

import pytest

from ai.backend.appproxy.common.etcd import TraefikEtcd
from ai.backend.appproxy.coordinator.config import TraefikConfig
from ai.backend.appproxy.coordinator.errors.ingress import TraefikIngressRevisionConflictError
from ai.backend.appproxy.coordinator.ingress.traefik import TraefikIngressWriter
from ai.backend.appproxy.coordinator.repositories.worker import TraefikWorker, WorkerRepository
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


@dataclass(frozen=True)
class _HeldRevisionCase:
    name: str
    held_revision: str | None


@pytest.fixture
def ingress() -> Ingress:
    return Ingress(
        id=IngressID("ingress-10205"),
        authority=IngressAuthority("worker-1"),
        revision=3,
        frontend=IngressFrontend(
            kind=IngressFrontendKind.PORT,
            protocol=IngressProtocol.HTTP,
            port=PortFrontend(number=10205),
        ),
        access=IngressAccess(mode=IngressAccessMode.PUBLIC, allowed_client_ips=[]),
        backend=IngressBackend(
            id=IngressBackendID("backend-1"),
            target_groups=[
                IngressTargetGroup(id=IngressTargetGroupID("group-1"), weight=1, targets=[])
            ],
        ),
    )


@pytest.fixture
def traefik_etcd(request: pytest.FixtureRequest) -> AsyncMock:
    case: _HeldRevisionCase = request.param
    traefik_etcd = AsyncMock(spec=TraefikEtcd)
    traefik_etcd.get.return_value = case.held_revision
    traefik_etcd.compare_and_replace_prefixes.return_value = True
    return traefik_etcd


@pytest.fixture
def worker_repository() -> AsyncMock:
    worker_repository = AsyncMock(spec=WorkerRepository)
    worker_repository.get_traefik_worker.return_value = TraefikWorker(
        hostname="worker-1.example.com", wildcard_domain=None, tls_listen=False
    )
    return worker_repository


@pytest.fixture
def writer(traefik_etcd: AsyncMock, worker_repository: AsyncMock) -> TraefikIngressWriter:
    return TraefikIngressWriter(
        traefik_etcd,
        worker_repository,
        Mock(spec=TraefikConfig),
        jwt_secret="jwt-secret",
        permit_hash_secret="permit-hash-secret",
    )


class TestTraefikIngressWriter:
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
        self, writer: TraefikIngressWriter, traefik_etcd: AsyncMock, ingress: Ingress
    ) -> None:
        await writer.upsert(ingress)
        traefik_etcd.compare_and_replace_prefixes.assert_awaited_once()

    @pytest.mark.parametrize(
        "traefik_etcd",
        [_HeldRevisionCase(name="newer", held_revision="4")],
        ids=lambda case: case.name,
        indirect=True,
    )
    async def test_upsert_older_than_held_raises_conflict(
        self, writer: TraefikIngressWriter, traefik_etcd: AsyncMock, ingress: Ingress
    ) -> None:
        with pytest.raises(TraefikIngressRevisionConflictError):
            await writer.upsert(ingress)
        traefik_etcd.compare_and_replace_prefixes.assert_not_awaited()
